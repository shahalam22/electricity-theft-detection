import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.feature_selection import SelectKBest, f_classif
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Try to import tsfresh, fall back to manual feature engineering if not available
try:
    from tsfresh import extract_features, select_features
    from tsfresh.feature_extraction import ComprehensiveFCParameters
    from tsfresh.utilities.dataframe_functions import impute
    TSFRESH_AVAILABLE = True
    logger.info("tsfresh is available for feature extraction")
except ImportError:
    TSFRESH_AVAILABLE = False
    logger.warning("tsfresh not available, using manual feature engineering")

from src.config.settings import settings


class ElectricityFeatureEngineer:
    """
    Feature engineering for electricity consumption time series data
    
    Creates statistical and time-series features for theft detection:
    - Basic statistical features (mean, std, skewness, kurtosis)
    - Time-based features (seasonality, trends)
    - Consumption pattern features
    - Advanced time-series features (using tsfresh if available)
    """
    
    def __init__(self):
        self.feature_names = []
        self.feature_importance = {}
        self.selected_features = []
        
    def create_basic_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create basic statistical features for each meter
        
        Features:
        - Mean, median, std, variance
        - Min, max, range
        - Skewness, kurtosis
        - Percentiles (25th, 75th, 90th, 95th)
        """
        try:
            logger.info("Creating basic statistical features...")
            
            features_df = df.groupby('meter_id')['consumption'].agg([
                'mean', 'median', 'std', 'var',
                'min', 'max', 'count',
                ('q25', lambda x: x.quantile(0.25)),
                ('q75', lambda x: x.quantile(0.75)),
                ('q90', lambda x: x.quantile(0.90)),
                ('q95', lambda x: x.quantile(0.95)),
                'skew',
                ('kurtosis', lambda x: x.kurtosis())
            ]).reset_index()
            
            # Add derived features
            features_df['range'] = features_df['max'] - features_df['min']
            features_df['cv'] = features_df['std'] / features_df['mean']  # Coefficient of variation
            features_df['iqr'] = features_df['q75'] - features_df['q25']  # Interquartile range
            
            # Add prefix for clarity
            feature_cols = [col for col in features_df.columns if col != 'meter_id']
            for col in feature_cols:
                features_df[f'stat_{col}'] = features_df[col]
                features_df.drop(col, axis=1, inplace=True)
            
            logger.success(f"Created {len(feature_cols)} basic statistical features")
            return features_df
            
        except Exception as e:
            logger.error(f"Error creating basic statistical features: {e}")
            raise
    
    def create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create temporal/seasonal features
        
        Features:
        - Weekly consumption patterns
        - Monthly consumption patterns
        - Seasonal variations
        - Weekend vs weekday patterns
        """
        try:
            logger.info("Creating temporal features...")
            
            df_temp = df.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'])
            df_temp['day_of_week'] = df_temp['date'].dt.dayofweek
            df_temp['month'] = df_temp['date'].dt.month
            df_temp['is_weekend'] = df_temp['day_of_week'].isin([5, 6]).astype(int)
            
            # Weekly pattern features
            weekly_features = df_temp.groupby(['meter_id', 'day_of_week'])['consumption'].mean().unstack(fill_value=0)
            weekly_features.columns = [f'temporal_weekday_{i}_avg' for i in range(7)]
            
            # Monthly pattern features
            monthly_features = df_temp.groupby(['meter_id', 'month'])['consumption'].mean().unstack(fill_value=0)
            monthly_features.columns = [f'temporal_month_{i}_avg' for i in range(1, 13)]
            
            # Weekend vs weekday
            weekend_features = df_temp.groupby(['meter_id', 'is_weekend'])['consumption'].agg(['mean', 'std']).unstack(fill_value=0)
            weekend_features.columns = ['temporal_weekday_mean', 'temporal_weekday_std', 'temporal_weekend_mean', 'temporal_weekend_std']
            
            # Combine all temporal features
            temporal_df = weekly_features.join(monthly_features, how='outer').join(weekend_features, how='outer')
            temporal_df = temporal_df.fillna(0).reset_index()
            
            # Add ratio features
            temporal_df['temporal_weekend_weekday_ratio'] = temporal_df['temporal_weekend_mean'] / (temporal_df['temporal_weekday_mean'] + 1e-6)
            
            logger.success(f"Created {len(temporal_df.columns)-1} temporal features")
            return temporal_df
            
        except Exception as e:
            logger.error(f"Error creating temporal features: {e}")
            raise
    
    def create_consumption_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create consumption pattern features
        
        Features:
        - Zero consumption days
        - Low consumption days
        - Consumption stability
        - Trend features
        - Change point detection
        """
        try:
            logger.info("Creating consumption pattern features...")
            
            df_temp = df.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'])
            df_temp = df_temp.sort_values(['meter_id', 'date'])
            
            pattern_features = []
            
            for meter_id in df_temp['meter_id'].unique():
                meter_data = df_temp[df_temp['meter_id'] == meter_id]['consumption'].values
                
                if len(meter_data) < 30:  # Skip if insufficient data
                    continue
                
                features = {'meter_id': meter_id}
                
                # Zero and low consumption patterns
                features['pattern_zero_days'] = (meter_data == 0).sum()
                features['pattern_zero_ratio'] = features['pattern_zero_days'] / len(meter_data)
                features['pattern_low_consumption_days'] = (meter_data < np.percentile(meter_data, 10)).sum()
                features['pattern_low_consumption_ratio'] = features['pattern_low_consumption_days'] / len(meter_data)
                
                # Consumption stability
                features['pattern_stability'] = np.std(meter_data) / (np.mean(meter_data) + 1e-6)
                
                # Trend features (linear regression slope)
                x = np.arange(len(meter_data))
                try:
                    slope, _ = np.polyfit(x, meter_data, 1)
                    features['pattern_trend_slope'] = slope
                except:
                    features['pattern_trend_slope'] = 0
                
                # Change detection (sudden drops/increases)
                if len(meter_data) > 1:
                    daily_changes = np.diff(meter_data)
                    features['pattern_avg_daily_change'] = np.mean(daily_changes)
                    features['pattern_max_daily_drop'] = np.min(daily_changes)
                    features['pattern_max_daily_increase'] = np.max(daily_changes)
                    features['pattern_change_volatility'] = np.std(daily_changes)
                    
                    # Count significant changes (> 2 std from mean change)
                    change_threshold = np.std(daily_changes) * 2
                    features['pattern_significant_drops'] = (daily_changes < -change_threshold).sum()
                    features['pattern_significant_increases'] = (daily_changes > change_threshold).sum()
                else:
                    features['pattern_avg_daily_change'] = 0
                    features['pattern_max_daily_drop'] = 0
                    features['pattern_max_daily_increase'] = 0
                    features['pattern_change_volatility'] = 0
                    features['pattern_significant_drops'] = 0
                    features['pattern_significant_increases'] = 0
                
                # Autocorrelation features
                if len(meter_data) > 7:
                    features['pattern_autocorr_1day'] = np.corrcoef(meter_data[:-1], meter_data[1:])[0, 1]
                    if len(meter_data) > 14:
                        features['pattern_autocorr_7day'] = np.corrcoef(meter_data[:-7], meter_data[7:])[0, 1]
                    else:
                        features['pattern_autocorr_7day'] = 0
                else:
                    features['pattern_autocorr_1day'] = 0
                    features['pattern_autocorr_7day'] = 0
                
                # Handle NaN values
                for key, value in features.items():
                    if key != 'meter_id' and (np.isnan(value) or np.isinf(value)):
                        features[key] = 0
                
                pattern_features.append(features)
            
            pattern_df = pd.DataFrame(pattern_features)
            
            logger.success(f"Created {len(pattern_df.columns)-1} consumption pattern features")
            return pattern_df
            
        except Exception as e:
            logger.error(f"Error creating consumption pattern features: {e}")
            raise
    
    def create_tsfresh_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create advanced time-series features using tsfresh
        
        Only works if tsfresh is installed
        """
        if not TSFRESH_AVAILABLE:
            logger.warning("tsfresh not available, skipping advanced time-series features")
            return pd.DataFrame({'meter_id': df['meter_id'].unique()})
        
        try:
            logger.info("Creating advanced time-series features with tsfresh...")
            
            # Prepare data for tsfresh (needs specific format)
            df_tsfresh = df.copy()
            df_tsfresh['date'] = pd.to_datetime(df_tsfresh['date'])
            df_tsfresh = df_tsfresh.sort_values(['meter_id', 'date'])
            df_tsfresh['time_id'] = df_tsfresh.groupby('meter_id').cumcount()
            
            # Extract features using tsfresh
            # Use a subset of features for performance
            feature_settings = {
                'mean': None,
                'median': None,
                'standard_deviation': None,
                'variance': None,
                'skewness': None,
                'kurtosis': None,
                'minimum': None,
                'maximum': None,
                'sum_values': None,
                'abs_energy': None,
                'mean_abs_change': None,
                'mean_change': None,
                'variance_larger_than_standard_deviation': None,
                'ratio_beyond_r_sigma': [{'r': 1}, {'r': 2}],
                'autocorrelation': [{'lag': 1}, {'lag': 7}],
                'agg_autocorrelation': [{'f_agg': 'mean', 'maxlag': 10}],
                'partial_autocorrelation': [{'lag': 1}, {'lag': 7}],
                'number_peaks': [{'n': 3}],
                'approximate_entropy': [{'m': 2, 'r': 0.1}],
                'fourier_entropy': [{'bins': 10}],
                'permutation_entropy': [{'order': 3, 'normalize': True}]
            }
            
            extracted_features = extract_features(
                df_tsfresh, 
                column_id='meter_id', 
                column_sort='time_id',
                column_value='consumption',
                default_fc_parameters=feature_settings,
                n_jobs=settings.tsfresh_n_jobs,
                disable_progressbar=True
            )
            
            # Impute NaN values
            impute(extracted_features)
            
            # Reset index to make meter_id a column
            extracted_features = extracted_features.reset_index()
            
            # Add prefix to avoid naming conflicts
            feature_cols = [col for col in extracted_features.columns if col != 'meter_id']
            for col in feature_cols:
                extracted_features[f'tsfresh_{col}'] = extracted_features[col]
                extracted_features.drop(col, axis=1, inplace=True)
            
            logger.success(f"Created {len(feature_cols)} tsfresh features")
            return extracted_features
            
        except Exception as e:
            logger.error(f"Error creating tsfresh features: {e}")
            # Return empty dataframe if tsfresh fails
            return pd.DataFrame({'meter_id': df['meter_id'].unique()})
    
    def combine_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create and combine all features
        
        Returns:
            DataFrame with all engineered features
        """
        try:
            logger.info("Starting comprehensive feature engineering...")
            
            # Create different types of features
            basic_features = self.create_basic_statistical_features(df)
            temporal_features = self.create_temporal_features(df)
            pattern_features = self.create_consumption_pattern_features(df)
            
            # Start with basic features
            all_features = basic_features
            
            # Merge temporal features
            all_features = all_features.merge(temporal_features, on='meter_id', how='left')
            
            # Merge pattern features
            all_features = all_features.merge(pattern_features, on='meter_id', how='left')
            
            # Create tsfresh features if available
            if TSFRESH_AVAILABLE:
                tsfresh_features = self.create_tsfresh_features(df)
                if len(tsfresh_features.columns) > 1:  # More than just meter_id
                    all_features = all_features.merge(tsfresh_features, on='meter_id', how='left')
            
            # Fill any remaining NaN values
            numeric_columns = all_features.select_dtypes(include=[np.number]).columns
            all_features[numeric_columns] = all_features[numeric_columns].fillna(0)
            
            # Store feature names
            self.feature_names = [col for col in all_features.columns if col != 'meter_id']
            
            logger.success(f"Feature engineering completed. Total features: {len(self.feature_names)}")
            
            return all_features
            
        except Exception as e:
            logger.error(f"Error in feature engineering: {e}")
            raise
    
    def select_best_features(self, 
                           features_df: pd.DataFrame, 
                           labels_df: pd.DataFrame,
                           k: int = None) -> pd.DataFrame:
        """
        Select best features using statistical tests
        
        Args:
            features_df: DataFrame with features
            labels_df: DataFrame with labels (meter_id, label)
            k: Number of features to select (default: from settings)
        
        Returns:
            DataFrame with selected features
        """
        try:
            if k is None:
                k = min(settings.feature_selection_k_best, len(self.feature_names))
            
            logger.info(f"Selecting top {k} features...")
            
            # Merge features with labels
            data_with_labels = features_df.merge(labels_df, on='meter_id', how='inner')
            
            # Separate features and labels
            X = data_with_labels[self.feature_names]
            y = data_with_labels['label']
            
            # Feature selection
            selector = SelectKBest(f_classif, k=k)
            X_selected = selector.fit_transform(X, y)
            
            # Get selected feature names
            selected_feature_names = [self.feature_names[i] for i in selector.get_support(indices=True)]
            self.selected_features = selected_feature_names
            
            # Get feature scores
            feature_scores = selector.scores_
            self.feature_importance = dict(zip(self.feature_names, feature_scores))
            
            # Create selected features dataframe
            selected_features_df = pd.DataFrame(X_selected, columns=selected_feature_names)
            selected_features_df['meter_id'] = data_with_labels['meter_id'].values
            
            # Reorder columns
            selected_features_df = selected_features_df[['meter_id'] + selected_feature_names]
            
            logger.success(f"Selected {len(selected_feature_names)} best features")
            
            return selected_features_df
            
        except Exception as e:
            logger.error(f"Error in feature selection: {e}")
            raise
    
    def get_feature_importance_report(self) -> Dict:
        """Get feature importance report"""
        if not self.feature_importance:
            return {"error": "Feature importance not calculated. Run select_best_features first."}
        
        # Sort features by importance
        sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_features': len(self.feature_names),
            'selected_features': len(self.selected_features),
            'top_10_features': sorted_features[:10],
            'feature_categories': {
                'statistical': len([f for f in self.selected_features if f.startswith('stat_')]),
                'temporal': len([f for f in self.selected_features if f.startswith('temporal_')]),
                'pattern': len([f for f in self.selected_features if f.startswith('pattern_')]),
                'tsfresh': len([f for f in self.selected_features if f.startswith('tsfresh_')])
            }
        }


# Utility functions
def engineer_features(df: pd.DataFrame, labels_df: pd.DataFrame = None) -> Tuple[pd.DataFrame, Dict]:
    """Convenience function for feature engineering"""
    engineer = ElectricityFeatureEngineer()
    features_df = engineer.combine_all_features(df)
    
    # Perform feature selection if labels are provided
    if labels_df is not None:
        features_df = engineer.select_best_features(features_df, labels_df)
    
    report = engineer.get_feature_importance_report()
    return features_df, report