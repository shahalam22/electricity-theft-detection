import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
from sklearn.utils import resample
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Import sampling techniques
try:
    from imblearn.over_sampling import ADASYN, SMOTE, BorderlineSMOTE, SVMSMOTE
    from imblearn.under_sampling import RandomUnderSampler, TomekLinks, EditedNearestNeighbours
    from imblearn.combine import SMOTETomek, SMOTEENN
    IMBALANCED_LEARN_AVAILABLE = True
    logger.info("imbalanced-learn is available for class balancing")
except ImportError:
    IMBALANCED_LEARN_AVAILABLE = False
    logger.warning("imbalanced-learn not available, using basic resampling methods")

from src.config.settings import settings


class ClassBalancer:
    """
    Class balancing for imbalanced electricity theft detection dataset
    
    The SGCC dataset has ~8.5% theft cases, making it highly imbalanced.
    This class provides various techniques to balance the dataset:
    - Oversampling (SMOTE, ADASYN, BorderlineSMOTE)
    - Undersampling (Random, Tomek Links, Edited Nearest Neighbours)
    - Combined methods (SMOTE + Tomek, SMOTE + ENN)
    - Simple resampling methods
    """
    
    def __init__(self):
        self.original_distribution = {}
        self.balanced_distribution = {}
        self.balancing_method = None
        self.balancing_stats = {}
    
    def analyze_class_distribution(self, y: pd.Series) -> Dict:
        """
        Analyze class distribution in the dataset
        
        Returns:
            Dictionary with class distribution statistics
        """
        try:
            distribution = y.value_counts().to_dict()
            total_samples = len(y)
            
            analysis = {
                'total_samples': total_samples,
                'class_counts': distribution,
                'class_percentages': {k: (v/total_samples)*100 for k, v in distribution.items()},
                'imbalance_ratio': max(distribution.values()) / min(distribution.values()),
                'minority_class': min(distribution, key=distribution.get),
                'majority_class': max(distribution, key=distribution.get)
            }
            
            logger.info(f"Class distribution analysis:")
            logger.info(f"  Total samples: {total_samples}")
            logger.info(f"  Class 0 (Normal): {distribution.get(0, 0)} ({analysis['class_percentages'].get(0, 0):.2f}%)")
            logger.info(f"  Class 1 (Theft): {distribution.get(1, 0)} ({analysis['class_percentages'].get(1, 0):.2f}%)")
            logger.info(f"  Imbalance ratio: {analysis['imbalance_ratio']:.2f}:1")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing class distribution: {e}")
            raise
    
    def random_oversample(self, X: pd.DataFrame, y: pd.Series, target_ratio: float = 0.5) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Simple random oversampling of minority class
        
        Args:
            X: Feature matrix
            y: Target labels
            target_ratio: Target ratio for minority class (0.5 = balanced)
        
        Returns:
            Balanced feature matrix and labels
        """
        try:
            logger.info(f"Applying random oversampling (target ratio: {target_ratio})")
            
            # Combine X and y for easier manipulation
            data = X.copy()
            data['target'] = y
            
            # Separate classes
            majority_class = data[data['target'] == 0]
            minority_class = data[data['target'] == 1]
            
            # Calculate target size for minority class
            total_majority = len(majority_class)
            target_minority_size = int(total_majority * target_ratio / (1 - target_ratio))
            
            # Oversample minority class
            minority_oversampled = resample(
                minority_class,
                replace=True,
                n_samples=target_minority_size,
                random_state=settings.random_state
            )
            
            # Combine classes
            balanced_data = pd.concat([majority_class, minority_oversampled])
            balanced_data = balanced_data.sample(frac=1, random_state=settings.random_state).reset_index(drop=True)
            
            # Separate features and target
            X_balanced = balanced_data.drop('target', axis=1)
            y_balanced = balanced_data['target']
            
            self.balancing_method = 'random_oversample'
            self.original_distribution = y.value_counts().to_dict()
            self.balanced_distribution = y_balanced.value_counts().to_dict()
            
            logger.success(f"Random oversampling completed: {len(X_balanced)} samples")
            return X_balanced, y_balanced
            
        except Exception as e:
            logger.error(f"Error in random oversampling: {e}")
            raise
    
    def random_undersample(self, X: pd.DataFrame, y: pd.Series, target_ratio: float = 0.5) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Simple random undersampling of majority class
        
        Args:
            X: Feature matrix
            y: Target labels
            target_ratio: Target ratio for minority class (0.5 = balanced)
        
        Returns:
            Balanced feature matrix and labels
        """
        try:
            logger.info(f"Applying random undersampling (target ratio: {target_ratio})")
            
            # Combine X and y for easier manipulation
            data = X.copy()
            data['target'] = y
            
            # Separate classes
            majority_class = data[data['target'] == 0]
            minority_class = data[data['target'] == 1]
            
            # Calculate target size for majority class
            total_minority = len(minority_class)
            target_majority_size = int(total_minority * (1 - target_ratio) / target_ratio)
            
            # Undersample majority class
            majority_undersampled = resample(
                majority_class,
                replace=False,
                n_samples=min(target_majority_size, len(majority_class)),
                random_state=settings.random_state
            )
            
            # Combine classes
            balanced_data = pd.concat([majority_undersampled, minority_class])
            balanced_data = balanced_data.sample(frac=1, random_state=settings.random_state).reset_index(drop=True)
            
            # Separate features and target
            X_balanced = balanced_data.drop('target', axis=1)
            y_balanced = balanced_data['target']
            
            self.balancing_method = 'random_undersample'
            self.original_distribution = y.value_counts().to_dict()
            self.balanced_distribution = y_balanced.value_counts().to_dict()
            
            logger.success(f"Random undersampling completed: {len(X_balanced)} samples")
            return X_balanced, y_balanced
            
        except Exception as e:
            logger.error(f"Error in random undersampling: {e}")
            raise
    
    def apply_smote(self, X: pd.DataFrame, y: pd.Series, variant: str = 'standard') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Apply SMOTE (Synthetic Minority Oversampling Technique)
        
        Args:
            X: Feature matrix
            y: Target labels
            variant: 'standard', 'borderline', 'svm'
        
        Returns:
            Balanced feature matrix and labels
        """
        if not IMBALANCED_LEARN_AVAILABLE:
            logger.warning("imbalanced-learn not available, falling back to random oversampling")
            return self.random_oversample(X, y)
        
        try:
            logger.info(f"Applying SMOTE ({variant} variant)")
            
            # Choose SMOTE variant
            if variant == 'borderline':
                sampler = BorderlineSMOTE(random_state=settings.random_state, k_neighbors=3)
            elif variant == 'svm':
                sampler = SVMSMOTE(random_state=settings.random_state, k_neighbors=3)
            else:  # standard
                sampler = SMOTE(random_state=settings.random_state, k_neighbors=3)
            
            # Apply SMOTE
            X_balanced, y_balanced = sampler.fit_resample(X, y)
            
            # Convert back to DataFrame/Series
            X_balanced = pd.DataFrame(X_balanced, columns=X.columns)
            y_balanced = pd.Series(y_balanced, name=y.name)
            
            self.balancing_method = f'smote_{variant}'
            self.original_distribution = y.value_counts().to_dict()
            self.balanced_distribution = y_balanced.value_counts().to_dict()
            
            logger.success(f"SMOTE ({variant}) completed: {len(X_balanced)} samples")
            return X_balanced, y_balanced
            
        except Exception as e:
            logger.error(f"Error applying SMOTE: {e}")
            # Fall back to random oversampling
            logger.info("Falling back to random oversampling")
            return self.random_oversample(X, y)
    
    def apply_adasyn(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Apply ADASYN (Adaptive Synthetic Sampling)
        
        Args:
            X: Feature matrix
            y: Target labels
        
        Returns:
            Balanced feature matrix and labels
        """
        if not IMBALANCED_LEARN_AVAILABLE:
            logger.warning("imbalanced-learn not available, falling back to random oversampling")
            return self.random_oversample(X, y)
        
        try:
            logger.info("Applying ADASYN")
            
            sampler = ADASYN(random_state=settings.random_state, n_neighbors=3)
            X_balanced, y_balanced = sampler.fit_resample(X, y)
            
            # Convert back to DataFrame/Series
            X_balanced = pd.DataFrame(X_balanced, columns=X.columns)
            y_balanced = pd.Series(y_balanced, name=y.name)
            
            self.balancing_method = 'adasyn'
            self.original_distribution = y.value_counts().to_dict()
            self.balanced_distribution = y_balanced.value_counts().to_dict()
            
            logger.success(f"ADASYN completed: {len(X_balanced)} samples")
            return X_balanced, y_balanced
            
        except Exception as e:
            logger.error(f"Error applying ADASYN: {e}")
            # Fall back to random oversampling
            logger.info("Falling back to random oversampling")
            return self.random_oversample(X, y)
    
    def apply_combined_sampling(self, X: pd.DataFrame, y: pd.Series, method: str = 'smote_tomek') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Apply combined over/under sampling methods
        
        Args:
            X: Feature matrix
            y: Target labels
            method: 'smote_tomek' or 'smote_enn'
        
        Returns:
            Balanced feature matrix and labels
        """
        if not IMBALANCED_LEARN_AVAILABLE:
            logger.warning("imbalanced-learn not available, falling back to random oversampling")
            return self.random_oversample(X, y)
        
        try:
            logger.info(f"Applying combined sampling: {method}")
            
            if method == 'smote_tomek':
                sampler = SMOTETomek(random_state=settings.random_state)
            elif method == 'smote_enn':
                sampler = SMOTEENN(random_state=settings.random_state)
            else:
                raise ValueError(f"Unknown combined method: {method}")
            
            X_balanced, y_balanced = sampler.fit_resample(X, y)
            
            # Convert back to DataFrame/Series
            X_balanced = pd.DataFrame(X_balanced, columns=X.columns)
            y_balanced = pd.Series(y_balanced, name=y.name)
            
            self.balancing_method = method
            self.original_distribution = y.value_counts().to_dict()
            self.balanced_distribution = y_balanced.value_counts().to_dict()
            
            logger.success(f"Combined sampling ({method}) completed: {len(X_balanced)} samples")
            return X_balanced, y_balanced
            
        except Exception as e:
            logger.error(f"Error applying combined sampling: {e}")
            # Fall back to random oversampling
            logger.info("Falling back to random oversampling")
            return self.random_oversample(X, y)
    
    def balance_dataset(self, 
                       X: pd.DataFrame, 
                       y: pd.Series, 
                       method: str = 'adasyn',
                       target_ratio: float = 0.3) -> Tuple[pd.DataFrame, pd.Series, Dict]:
        """
        Balance dataset using specified method
        
        Args:
            X: Feature matrix
            y: Target labels
            method: 'adasyn', 'smote', 'borderline_smote', 'svm_smote', 'smote_tomek', 
                   'smote_enn', 'random_over', 'random_under'
            target_ratio: Target ratio for minority class (used for random methods)
        
        Returns:
            Balanced feature matrix, labels, and balancing report
        """
        try:
            logger.info(f"Starting dataset balancing using {method} method")
            
            # Analyze original distribution
            original_analysis = self.analyze_class_distribution(y)
            
            # Apply balancing method
            if method == 'adasyn':
                X_balanced, y_balanced = self.apply_adasyn(X, y)
            elif method == 'smote':
                X_balanced, y_balanced = self.apply_smote(X, y, variant='standard')
            elif method == 'borderline_smote':
                X_balanced, y_balanced = self.apply_smote(X, y, variant='borderline')
            elif method == 'svm_smote':
                X_balanced, y_balanced = self.apply_smote(X, y, variant='svm')
            elif method == 'smote_tomek':
                X_balanced, y_balanced = self.apply_combined_sampling(X, y, method='smote_tomek')
            elif method == 'smote_enn':
                X_balanced, y_balanced = self.apply_combined_sampling(X, y, method='smote_enn')
            elif method == 'random_over':
                X_balanced, y_balanced = self.random_oversample(X, y, target_ratio=target_ratio)
            elif method == 'random_under':
                X_balanced, y_balanced = self.random_undersample(X, y, target_ratio=target_ratio)
            else:
                raise ValueError(f"Unknown balancing method: {method}")
            
            # Analyze balanced distribution
            balanced_analysis = self.analyze_class_distribution(y_balanced)
            
            # Create balancing report
            balancing_report = {
                'method': method,
                'original_distribution': original_analysis,
                'balanced_distribution': balanced_analysis,
                'sample_change': {
                    'original_samples': len(X),
                    'balanced_samples': len(X_balanced),
                    'samples_added': len(X_balanced) - len(X),
                    'change_percentage': ((len(X_balanced) - len(X)) / len(X)) * 100
                },
                'class_balance_improvement': {
                    'original_imbalance_ratio': original_analysis['imbalance_ratio'],
                    'balanced_imbalance_ratio': balanced_analysis['imbalance_ratio'],
                    'improvement_factor': original_analysis['imbalance_ratio'] / balanced_analysis['imbalance_ratio']
                }
            }
            
            # Store statistics
            self.balancing_stats = balancing_report
            
            logger.success(f"Dataset balancing completed successfully")
            logger.info(f"  Original samples: {len(X)} → Balanced samples: {len(X_balanced)}")
            logger.info(f"  Imbalance ratio: {original_analysis['imbalance_ratio']:.2f}:1 → {balanced_analysis['imbalance_ratio']:.2f}:1")
            
            return X_balanced, y_balanced, balancing_report
            
        except Exception as e:
            logger.error(f"Error in dataset balancing: {e}")
            raise
    
    def get_balancing_recommendations(self, y: pd.Series) -> Dict:
        """
        Get recommendations for balancing method based on dataset characteristics
        
        Returns:
            Dictionary with recommendations
        """
        try:
            analysis = self.analyze_class_distribution(y)
            
            recommendations = {
                'dataset_size': 'large' if len(y) > 10000 else 'medium' if len(y) > 1000 else 'small',
                'imbalance_severity': 'severe' if analysis['imbalance_ratio'] > 20 else 'moderate' if analysis['imbalance_ratio'] > 5 else 'mild',
                'minority_samples': analysis['class_counts'].get(1, 0)
            }
            
            # Recommend methods based on characteristics
            if recommendations['minority_samples'] < 100:
                recommendations['recommended_methods'] = ['random_over', 'smote']
                recommendations['avoid_methods'] = ['adasyn', 'borderline_smote']
                recommendations['reason'] = 'Too few minority samples for complex oversampling'
            elif recommendations['imbalance_severity'] == 'severe':
                recommendations['recommended_methods'] = ['adasyn', 'smote_tomek']
                recommendations['avoid_methods'] = ['random_under']
                recommendations['reason'] = 'Severe imbalance requires sophisticated oversampling'
            elif recommendations['dataset_size'] == 'large':
                recommendations['recommended_methods'] = ['random_under', 'smote_enn']
                recommendations['avoid_methods'] = ['random_over']
                recommendations['reason'] = 'Large dataset benefits from undersampling or combined methods'
            else:
                recommendations['recommended_methods'] = ['smote', 'adasyn']
                recommendations['avoid_methods'] = []
                recommendations['reason'] = 'Standard oversampling methods work well'
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {'error': str(e)}


# Utility functions
def balance_electricity_data(X: pd.DataFrame, y: pd.Series, method: str = 'adasyn') -> Tuple[pd.DataFrame, pd.Series, Dict]:
    """Convenience function for balancing electricity theft data"""
    balancer = ClassBalancer()
    return balancer.balance_dataset(X, y, method=method)