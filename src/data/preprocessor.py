import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional, List
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.impute import SimpleImputer
from scipy import stats
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

from src.config.settings import settings


class ElectricityDataPreprocessor:
    """
    Data preprocessing pipeline for electricity consumption data
    
    Handles:
    - Missing value imputation
    - Outlier detection and removal
    - Data normalization
    - Data validation
    """
    
    def __init__(self):
        self.scaler = None
        self.imputer = None
        self.outlier_bounds = {}
        self.preprocessing_stats = {}
        
    def handle_missing_values(self, df: pd.DataFrame, method: str = 'linear') -> pd.DataFrame:
        """
        Handle missing values in consumption data
        
        Args:
            df: DataFrame with consumption data
            method: 'linear', 'forward_fill', 'mean', 'median'
        
        Returns:
            DataFrame with imputed values
        """
        try:
            logger.info(f"Handling missing values using {method} method...")
            
            df_processed = df.copy()
            initial_missing = df_processed['consumption'].isnull().sum()
            
            if initial_missing == 0:
                logger.info("No missing values found")
                return df_processed
            
            logger.info(f"Found {initial_missing} missing values ({initial_missing/len(df)*100:.2f}%)")
            
            if method == 'linear':
                # Linear interpolation for time series data
                df_processed = df_processed.sort_values(['meter_id', 'date'])
                df_processed['consumption'] = df_processed.groupby('meter_id')['consumption'].transform(
                    lambda x: x.interpolate(method='linear', limit_direction='both')
                )
                
            elif method == 'forward_fill':
                df_processed = df_processed.sort_values(['meter_id', 'date'])
                df_processed['consumption'] = df_processed.groupby('meter_id')['consumption'].transform(
                    lambda x: x.fillna(method='ffill').fillna(method='bfill')
                )
                
            elif method == 'mean':
                # Fill with meter-specific mean, then global mean
                meter_means = df_processed.groupby('meter_id')['consumption'].mean()
                global_mean = df_processed['consumption'].mean()
                
                for meter_id in df_processed['meter_id'].unique():
                    mask = (df_processed['meter_id'] == meter_id) & df_processed['consumption'].isnull()
                    fill_value = meter_means.get(meter_id, global_mean)
                    df_processed.loc[mask, 'consumption'] = fill_value
                    
            elif method == 'median':
                # Fill with meter-specific median, then global median
                meter_medians = df_processed.groupby('meter_id')['consumption'].median()
                global_median = df_processed['consumption'].median()
                
                for meter_id in df_processed['meter_id'].unique():
                    mask = (df_processed['meter_id'] == meter_id) & df_processed['consumption'].isnull()
                    fill_value = meter_medians.get(meter_id, global_median)
                    df_processed.loc[mask, 'consumption'] = fill_value
            
            final_missing = df_processed['consumption'].isnull().sum()
            logger.success(f"Missing values reduced from {initial_missing} to {final_missing}")
            
            # Store statistics
            self.preprocessing_stats['missing_values'] = {
                'initial': initial_missing,
                'final': final_missing,
                'method': method
            }
            
            return df_processed
            
        except Exception as e:
            logger.error(f"Error handling missing values: {e}")
            raise
    
    def detect_and_remove_outliers(self, 
                                   df: pd.DataFrame, 
                                   method: str = 'zscore',
                                   threshold: float = 3.0) -> pd.DataFrame:
        """
        Detect and remove outliers from consumption data
        
        Args:
            df: DataFrame with consumption data
            method: 'zscore', 'iqr', 'isolation_forest'
            threshold: Threshold for outlier detection
        
        Returns:
            DataFrame with outliers removed/capped
        """
        try:
            logger.info(f"Detecting outliers using {method} method (threshold={threshold})...")
            
            df_processed = df.copy()
            initial_count = len(df_processed)
            outliers_removed = 0
            
            if method == 'zscore':
                # Z-score method (3-sigma rule)
                for meter_id in df_processed['meter_id'].unique():
                    meter_data = df_processed[df_processed['meter_id'] == meter_id]['consumption']
                    
                    if len(meter_data) > 10:  # Need sufficient data points
                        z_scores = np.abs(stats.zscore(meter_data.dropna()))
                        outlier_mask = z_scores > threshold
                        
                        # Cap outliers instead of removing (more conservative)
                        if outlier_mask.any():
                            # Calculate bounds
                            mean_val = meter_data.mean()
                            std_val = meter_data.std()
                            lower_bound = mean_val - threshold * std_val
                            upper_bound = mean_val + threshold * std_val
                            
                            # Cap outliers
                            meter_mask = df_processed['meter_id'] == meter_id
                            df_processed.loc[meter_mask, 'consumption'] = df_processed.loc[meter_mask, 'consumption'].clip(
                                lower=max(0, lower_bound), upper=upper_bound
                            )
                            
                            outliers_removed += outlier_mask.sum()
                            
            elif method == 'iqr':
                # Interquartile Range method
                for meter_id in df_processed['meter_id'].unique():
                    meter_data = df_processed[df_processed['meter_id'] == meter_id]['consumption']
                    
                    if len(meter_data) > 10:
                        Q1 = meter_data.quantile(0.25)
                        Q3 = meter_data.quantile(0.75)
                        IQR = Q3 - Q1
                        
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        # Cap outliers
                        meter_mask = df_processed['meter_id'] == meter_id
                        outlier_mask = (df_processed.loc[meter_mask, 'consumption'] < lower_bound) | \
                                     (df_processed.loc[meter_mask, 'consumption'] > upper_bound)
                        
                        df_processed.loc[meter_mask, 'consumption'] = df_processed.loc[meter_mask, 'consumption'].clip(
                            lower=max(0, lower_bound), upper=upper_bound
                        )
                        
                        outliers_removed += outlier_mask.sum()
                        
            elif method == 'isolation_forest':
                from sklearn.ensemble import IsolationForest
                
                # Apply isolation forest per meter
                for meter_id in df_processed['meter_id'].unique():
                    meter_mask = df_processed['meter_id'] == meter_id
                    meter_data = df_processed.loc[meter_mask, 'consumption'].values.reshape(-1, 1)
                    
                    if len(meter_data) > 20:  # Need sufficient data points
                        iso_forest = IsolationForest(contamination=0.1, random_state=42)
                        outlier_labels = iso_forest.fit_predict(meter_data)
                        
                        # Mark outliers (isolation forest returns -1 for outliers)
                        outlier_indices = df_processed[meter_mask].index[outlier_labels == -1]
                        
                        # Cap outliers to median value
                        median_val = df_processed.loc[meter_mask, 'consumption'].median()
                        df_processed.loc[outlier_indices, 'consumption'] = median_val
                        
                        outliers_removed += len(outlier_indices)
            
            logger.success(f"Processed {outliers_removed} outliers out of {initial_count} records")
            
            # Store statistics
            self.preprocessing_stats['outliers'] = {
                'method': method,
                'threshold': threshold,
                'outliers_processed': outliers_removed,
                'outlier_rate': outliers_removed / initial_count
            }
            
            return df_processed
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            raise
    
    def normalize_data(self, 
                      df: pd.DataFrame, 
                      method: str = 'minmax',
                      feature_columns: List[str] = None) -> pd.DataFrame:
        """
        Normalize consumption data
        
        Args:
            df: DataFrame with consumption data
            method: 'minmax', 'zscore', 'robust'
            feature_columns: Columns to normalize (default: ['consumption'])
        
        Returns:
            DataFrame with normalized features
        """
        try:
            logger.info(f"Normalizing data using {method} method...")
            
            if feature_columns is None:
                feature_columns = ['consumption']
            
            df_processed = df.copy()
            
            if method == 'minmax':
                if self.scaler is None:
                    self.scaler = MinMaxScaler()
                    df_processed[feature_columns] = self.scaler.fit_transform(df_processed[feature_columns])
                else:
                    df_processed[feature_columns] = self.scaler.transform(df_processed[feature_columns])
                    
            elif method == 'zscore':
                if self.scaler is None:
                    self.scaler = StandardScaler()
                    df_processed[feature_columns] = self.scaler.fit_transform(df_processed[feature_columns])
                else:
                    df_processed[feature_columns] = self.scaler.transform(df_processed[feature_columns])
                    
            elif method == 'robust':
                from sklearn.preprocessing import RobustScaler
                if self.scaler is None:
                    self.scaler = RobustScaler()
                    df_processed[feature_columns] = self.scaler.fit_transform(df_processed[feature_columns])
                else:
                    df_processed[feature_columns] = self.scaler.transform(df_processed[feature_columns])
            
            logger.success("Data normalization completed")
            
            # Store statistics
            self.preprocessing_stats['normalization'] = {
                'method': method,
                'features': feature_columns
            }
            
            return df_processed
            
        except Exception as e:
            logger.error(f"Error normalizing data: {e}")
            raise
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """
        Validate data quality and generate report
        
        Returns:
            Dictionary with data quality metrics
        """
        try:
            logger.info("Validating data quality...")
            
            quality_report = {
                'total_records': len(df),
                'unique_meters': df['meter_id'].nunique(),
                'date_range': {
                    'start': df['date'].min(),
                    'end': df['date'].max(),
                    'days': df['date'].nunique()
                },
                'missing_data': {
                    'consumption_missing': df['consumption'].isnull().sum(),
                    'missing_percentage': (df['consumption'].isnull().sum() / len(df)) * 100
                },
                'data_types': {
                    'consumption_dtype': str(df['consumption'].dtype),
                    'date_dtype': str(df['date'].dtype)
                },
                'consumption_quality': {
                    'negative_values': (df['consumption'] < 0).sum(),
                    'zero_values': (df['consumption'] == 0).sum(),
                    'extremely_high': (df['consumption'] > df['consumption'].quantile(0.99) * 3).sum()
                },
                'duplicates': df.duplicated(['meter_id', 'date']).sum(),
                'data_consistency': {
                    'meters_with_insufficient_data': self._check_insufficient_data(df),
                    'date_gaps': self._check_date_gaps(df)
                }
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(quality_report)
            quality_report['overall_quality_score'] = quality_score
            
            logger.success(f"Data quality validation completed. Quality score: {quality_score:.2f}/100")
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            raise
    
    def _check_insufficient_data(self, df: pd.DataFrame, min_days: int = 30) -> int:
        """Check for meters with insufficient data"""
        meter_counts = df.groupby('meter_id').size()
        return (meter_counts < min_days).sum()
    
    def _check_date_gaps(self, df: pd.DataFrame) -> Dict:
        """Check for date gaps in time series data (optimized for large datasets)"""
        gaps_info = {'meters_with_gaps': 0, 'total_gaps': 0}
        
        # For large datasets, sample a subset for performance
        unique_meters = df['meter_id'].unique()
        if len(unique_meters) > 1000:
            logger.info(f"Large dataset ({len(unique_meters)} meters), sampling 1000 meters for gap analysis")
            import numpy as np
            sample_meters = np.random.choice(unique_meters, size=1000, replace=False)
            sample_df = df[df['meter_id'].isin(sample_meters)]
        else:
            sample_df = df
            sample_meters = unique_meters
        
        for meter_id in sample_meters:
            meter_data = sample_df[sample_df['meter_id'] == meter_id].sort_values('date')
            if len(meter_data) > 1:
                date_diffs = meter_data['date'].diff().dt.days
                gaps = (date_diffs > 1).sum()
                if gaps > 0:
                    gaps_info['meters_with_gaps'] += 1
                    gaps_info['total_gaps'] += gaps
        
        # Scale up results if we sampled
        if len(unique_meters) > 1000:
            scale_factor = len(unique_meters) / len(sample_meters)
            gaps_info['meters_with_gaps'] = int(gaps_info['meters_with_gaps'] * scale_factor)
            gaps_info['total_gaps'] = int(gaps_info['total_gaps'] * scale_factor)
        
        return gaps_info
    
    def _calculate_quality_score(self, quality_report: Dict) -> float:
        """Calculate overall data quality score (0-100)"""
        score = 100.0
        
        # Deduct for missing data
        missing_rate = quality_report['missing_data']['missing_percentage']
        score -= min(missing_rate, 30)  # Max 30 points deduction
        
        # Deduct for negative values
        negative_rate = (quality_report['consumption_quality']['negative_values'] / 
                        quality_report['total_records']) * 100
        score -= min(negative_rate * 2, 20)  # Max 20 points deduction
        
        # Deduct for duplicates
        duplicate_rate = (quality_report['duplicates'] / quality_report['total_records']) * 100
        score -= min(duplicate_rate * 5, 15)  # Max 15 points deduction
        
        # Deduct for insufficient data
        insufficient_rate = (quality_report['data_consistency']['meters_with_insufficient_data'] / 
                           quality_report['unique_meters']) * 100
        score -= min(insufficient_rate, 10)  # Max 10 points deduction
        
        return max(0, score)
    
    def preprocess_pipeline(self, 
                           df: pd.DataFrame,
                           missing_method: str = 'linear',
                           outlier_method: str = 'zscore',
                           normalization_method: str = 'minmax') -> Tuple[pd.DataFrame, Dict]:
        """
        Complete preprocessing pipeline
        
        Returns:
            Tuple of (processed_dataframe, preprocessing_report)
        """
        try:
            logger.info("Starting complete preprocessing pipeline...")
            
            # Initial data quality check
            initial_quality = self.validate_data_quality(df)
            
            # Step 1: Handle missing values
            df_processed = self.handle_missing_values(df, method=missing_method)
            
            # Step 2: Remove outliers
            df_processed = self.detect_and_remove_outliers(df_processed, method=outlier_method)
            
            # Step 3: Normalize data (optional, often done after feature engineering)
            # df_processed = self.normalize_data(df_processed, method=normalization_method)
            
            # Final data quality check
            final_quality = self.validate_data_quality(df_processed)
            
            # Create preprocessing report
            preprocessing_report = {
                'initial_quality': initial_quality,
                'final_quality': final_quality,
                'processing_steps': self.preprocessing_stats,
                'improvement': {
                    'quality_score_improvement': final_quality['overall_quality_score'] - initial_quality['overall_quality_score'],
                    'missing_data_reduction': initial_quality['missing_data']['missing_percentage'] - final_quality['missing_data']['missing_percentage']
                }
            }
            
            logger.success("Preprocessing pipeline completed successfully")
            
            return df_processed, preprocessing_report
            
        except Exception as e:
            logger.error(f"Error in preprocessing pipeline: {e}")
            raise


# Utility functions
def preprocess_sgcc_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Convenience function to preprocess SGCC data"""
    preprocessor = ElectricityDataPreprocessor()
    return preprocessor.preprocess_pipeline(df)