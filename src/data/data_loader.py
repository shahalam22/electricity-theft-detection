import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

from src.config.settings import settings


class SGCCDataLoader:
    """
    SGCC Dataset Loader for Electricity Theft Detection
    
    The SGCC dataset contains:
    - 42,372 smart meter users
    - 1,035 days of consumption data (2014-2016)
    - ~8.5% theft cases (3,615 users)
    - ~25.64% missing data rate
    """
    
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = Path(data_path) if data_path else Path("data/raw/sgcc_dataset")
        self.processed_path = Path("data/processed")
        self.processed_path.mkdir(parents=True, exist_ok=True)
        
    def download_dataset(self) -> bool:
        """
        Download SGCC dataset from GitHub repository
        """
        try:
            import requests
            import zipfile
            import io
            
            logger.info("Downloading SGCC dataset...")
            
            # GitHub repository URL for SGCC dataset
            url = "https://github.com/henryRDlab/ElectricityTheftDetection/archive/refs/heads/master.zip"
            
            response = requests.get(url)
            response.raise_for_status()
            
            # Extract zip file
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                zip_file.extractall("data/raw/")
            
            # Move files to correct location
            extracted_path = Path("data/raw/ElectricityTheftDetection-master")
            if extracted_path.exists():
                # Find the actual data files
                for file_path in extracted_path.rglob("*.csv"):
                    if "consumption" in file_path.name.lower() or "sgcc" in file_path.name.lower():
                        file_path.rename(self.data_path / file_path.name)
                        
            logger.success("SGCC dataset downloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download SGCC dataset: {e}")
            return False
    
    def create_synthetic_sgcc_data(self) -> bool:
        """
        Create synthetic SGCC-like dataset for development/testing
        This mimics the real SGCC dataset structure and characteristics
        """
        try:
            logger.info("Creating synthetic SGCC-like dataset...")
            
            # Dataset parameters matching SGCC
            n_users = 1000  # Reduced for development (real: 42,372)
            n_days = 365    # Reduced for development (real: 1,035)
            theft_rate = 0.085  # 8.5% theft rate
            missing_rate = 0.25  # 25% missing data rate
            
            # Generate user IDs
            user_ids = [f"METER_{str(i).zfill(6)}" for i in range(1, n_users + 1)]
            
            # Determine theft users (8.5% of total)
            n_theft_users = int(n_users * theft_rate)
            theft_users = np.random.choice(user_ids, size=n_theft_users, replace=False)
            
            # Generate consumption data
            data = []
            dates = pd.date_range(start='2024-01-01', periods=n_days, freq='D')
            
            for user_id in user_ids:
                is_theft = user_id in theft_users
                
                for date in dates:
                    # Generate realistic consumption patterns
                    base_consumption = self._generate_consumption_pattern(date, is_theft)
                    
                    # Add missing values (25% missing rate)
                    if np.random.random() < missing_rate:
                        consumption = np.nan
                    else:
                        consumption = base_consumption
                    
                    data.append({
                        'meter_id': user_id,
                        'date': date.strftime('%Y-%m-%d'),
                        'consumption': consumption,
                        'label': 1 if is_theft else 0  # 1 = theft, 0 = normal
                    })
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Save dataset
            self.data_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.data_path / "sgcc_synthetic_dataset.csv", index=False)
            
            # Save metadata
            metadata = {
                'total_users': n_users,
                'total_days': n_days,
                'theft_users': n_theft_users,
                'theft_rate': theft_rate,
                'missing_rate': missing_rate,
                'total_records': len(data),
                'date_range': f"{dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}"
            }
            
            pd.DataFrame([metadata]).to_csv(self.data_path / "dataset_metadata.csv", index=False)
            
            logger.success(f"Synthetic SGCC dataset created: {len(data)} records")
            logger.info(f"Normal users: {n_users - n_theft_users}, Theft users: {n_theft_users}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create synthetic dataset: {e}")
            return False
    
    def _generate_consumption_pattern(self, date: pd.Timestamp, is_theft: bool) -> float:
        """Generate realistic consumption patterns"""
        
        # Base consumption based on day of week and season
        day_of_week = date.dayofweek
        month = date.month
        
        # Weekly pattern (lower on weekends for residential)
        if day_of_week < 5:  # Weekday
            base = 25.0
        else:  # Weekend
            base = 22.0
            
        # Seasonal variation
        if month in [12, 1, 2]:  # Winter (higher heating)
            seasonal_factor = 1.3
        elif month in [6, 7, 8]:  # Summer (higher cooling)
            seasonal_factor = 1.2
        else:
            seasonal_factor = 1.0
            
        base *= seasonal_factor
        
        # Add random variation
        noise = np.random.normal(0, 3)
        consumption = base + noise
        
        # Theft pattern: significantly lower consumption
        if is_theft:
            # Theft users consume 40-70% of normal
            theft_factor = np.random.uniform(0.4, 0.7)
            consumption *= theft_factor
            
            # Add more irregular patterns for theft
            if np.random.random() < 0.1:  # 10% chance of very low reading
                consumption *= np.random.uniform(0.1, 0.3)
        
        # Ensure positive consumption
        consumption = max(0.1, consumption)
        
        return round(consumption, 2)
    
    def load_dataset(self, use_synthetic: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        Load SGCC dataset (real or synthetic)
        
        Returns:
            Tuple of (DataFrame, metadata_dict)
        """
        try:
            if use_synthetic:
                # Check if synthetic data exists, create if not
                synthetic_file = self.data_path / "sgcc_synthetic_dataset.csv"
                if not synthetic_file.exists():
                    logger.info("Synthetic dataset not found, creating...")
                    self.create_synthetic_sgcc_data()
                
                df = pd.read_csv(synthetic_file)
                metadata_file = self.data_path / "dataset_metadata.csv"
                metadata = pd.read_csv(metadata_file).iloc[0].to_dict()
                
            else:
                # Try to load real SGCC dataset
                csv_files = list(self.data_path.glob("*.csv"))
                if not csv_files:
                    logger.warning("Real SGCC dataset not found, downloading...")
                    if not self.download_dataset():
                        raise FileNotFoundError("Could not download SGCC dataset")
                
                # Load the main dataset file
                data_file = next((f for f in csv_files if "consumption" in f.name.lower()), csv_files[0])
                df = pd.read_csv(data_file)
                metadata = {"source": "real_sgcc", "file": str(data_file)}
            
            logger.success(f"Dataset loaded: {len(df)} records, {df['meter_id'].nunique()} unique meters")
            
            return df, metadata
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    def get_dataset_info(self, df: pd.DataFrame) -> Dict:
        """Get comprehensive dataset information"""
        
        info = {
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
            'consumption_stats': {
                'mean': df['consumption'].mean(),
                'median': df['consumption'].median(),
                'std': df['consumption'].std(),
                'min': df['consumption'].min(),
                'max': df['consumption'].max()
            }
        }
        
        # Add theft statistics if labels exist
        if 'label' in df.columns:
            theft_stats = df['label'].value_counts()
            info['theft_statistics'] = {
                'normal_users': theft_stats.get(0, 0),
                'theft_users': theft_stats.get(1, 0),
                'theft_rate': (theft_stats.get(1, 0) / len(df)) * 100
            }
        
        return info
    
    def prepare_time_series_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for time series analysis
        - Convert dates to datetime
        - Sort by meter_id and date
        - Create time-based features
        """
        try:
            logger.info("Preparing time series data...")
            
            # Convert date column
            df['date'] = pd.to_datetime(df['date'])
            
            # Sort data
            df = df.sort_values(['meter_id', 'date']).reset_index(drop=True)
            
            # Add time-based features
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_of_year'] = df['date'].dt.dayofyear
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # Add season
            df['season'] = df['month'].map({
                12: 'winter', 1: 'winter', 2: 'winter',
                3: 'spring', 4: 'spring', 5: 'spring',
                6: 'summer', 7: 'summer', 8: 'summer',
                9: 'autumn', 10: 'autumn', 11: 'autumn'
            })
            
            logger.success("Time series data prepared successfully")
            return df
            
        except Exception as e:
            logger.error(f"Failed to prepare time series data: {e}")
            raise


# Utility functions
def load_sgcc_data(use_synthetic: bool = True) -> Tuple[pd.DataFrame, Dict]:
    """Convenience function to load SGCC dataset"""
    loader = SGCCDataLoader()
    return loader.load_dataset(use_synthetic=use_synthetic)