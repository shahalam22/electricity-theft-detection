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
    - Smart meter consumption data in wide format
    - Daily consumption columns (dates as headers)
    - CONS_NO: Meter identifier
    - FLAG: 0=normal, 1=theft
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
    
    def load_real_sgcc_data(self, filename: str = "datasetsmall.csv") -> pd.DataFrame:
        """
        Load real SGCC dataset from CSV file
        
        Args:
            filename: Name of the SGCC dataset file
            
        Returns:
            DataFrame in wide format as loaded from CSV
        """
        try:
            logger.info(f"Loading real SGCC dataset from {filename}...")
            
            # Load the dataset
            data_file = self.data_path / filename
            if not data_file.exists():
                raise FileNotFoundError(f"Dataset file not found: {data_file}")
            
            # Read CSV with proper handling
            df_raw = pd.read_csv(data_file, low_memory=False)
            
            logger.info(f"Raw dataset loaded: {len(df_raw)} meters, {len(df_raw.columns)} columns")
            
            # Basic validation
            if 'CONS_NO' not in df_raw.columns:
                raise ValueError("Dataset must contain 'CONS_NO' column")
            if 'FLAG' not in df_raw.columns:
                raise ValueError("Dataset must contain 'FLAG' column")
            
            # Get dataset statistics
            total_meters = len(df_raw)
            theft_meters = df_raw['FLAG'].sum()
            normal_meters = total_meters - theft_meters
            theft_rate = (theft_meters / total_meters) * 100
            
            logger.success(f"SGCC dataset loaded successfully:")
            logger.info(f"  - Total meters: {total_meters:,}")
            logger.info(f"  - Normal meters: {normal_meters:,} ({100-theft_rate:.1f}%)")
            logger.info(f"  - Theft meters: {theft_meters:,} ({theft_rate:.1f}%)")
            logger.info(f"  - Date columns: {len(df_raw.columns) - 2}")
            
            return df_raw
            
        except Exception as e:
            logger.error(f"Failed to load real SGCC dataset: {e}")
            raise
    
    
    def load_dataset(self, filename: str = "datasetsmall.csv") -> Tuple[pd.DataFrame, Dict]:
        """
        Load SGCC dataset and convert to long format
        
        Args:
            filename: Name of the SGCC dataset file
            
        Returns:
            Tuple of (DataFrame in long format, metadata_dict)
        """
        try:
            # Load raw data in wide format
            df_raw = self.load_real_sgcc_data(filename)
            
            # Convert from wide format to long format
            df_long = self.convert_sgcc_wide_to_long(df_raw)
            
            # Create metadata
            metadata = {
                "source": "real_sgcc",
                "filename": filename,
                "original_format": "wide", 
                "total_meters": len(df_raw),
                "total_days": len(df_raw.columns) - 2,
                "total_records": len(df_long),
                "theft_rate": (df_raw['FLAG'].sum() / len(df_raw)) * 100,
                "date_range": self._extract_date_range(df_raw)
            }
            
            logger.success(f"Dataset converted to long format: {len(df_long):,} records, {df_long['meter_id'].nunique():,} unique meters")
            
            return df_long, metadata
            
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
    
    def convert_sgcc_wide_to_long(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Convert SGCC dataset from wide format (days as columns) to long format
        
        Args:
            df_raw: Raw SGCC dataframe with consumption days as columns
            
        Returns:
            Long format dataframe with date, meter_id, consumption, label columns
        """
        logger.info("Converting wide format SGCC data to long format...")
        
        # Get date columns (all except last 2 which are CONS_NO and FLAG)
        date_columns = df_raw.columns[:-2].tolist()
        
        # Create a copy and rename identifier columns
        df_work = df_raw.copy()
        df_work = df_work.rename(columns={'CONS_NO': 'meter_id', 'FLAG': 'label'})
        
        # Melt the dataframe to convert from wide to long format
        df_long = pd.melt(
            df_work,
            id_vars=['meter_id', 'label'],
            value_vars=date_columns,
            var_name='date',
            value_name='consumption'
        )
        
        # Convert date strings to datetime with improved parsing
        logger.info("Parsing date columns...")
        
        def parse_date_column(date_str):
            """Parse various date formats in the dataset"""
            try:
                # Try MM/DD/YYYY first
                if '/' in date_str:
                    return pd.to_datetime(date_str, format='%m/%d/%Y', errors='coerce')
                else:
                    return pd.to_datetime(date_str, errors='coerce')
            except:
                return pd.NaT
        
        df_long['date'] = df_long['date'].apply(parse_date_column)
        
        # Handle any dates that couldn't be parsed
        failed_dates = df_long['date'].isna().sum()
        if failed_dates > 0:
            logger.warning(f"Could not parse {failed_dates} date entries, creating sequential dates")
            
            # For failed dates, create sequential dates starting from 2014-01-01
            unique_dates = sorted(df_long['date'].dropna().unique())
            if len(unique_dates) > 0:
                start_date = min(unique_dates)
            else:
                start_date = pd.to_datetime('2014-01-01')
            
            # Fill missing dates sequentially
            date_mapping = {}
            for i, col in enumerate(date_columns):
                if df_long[df_long['date'].notna() & (df_long['date'] == parse_date_column(col))].empty:
                    date_mapping[col] = start_date + pd.Timedelta(days=i)
            
            for idx, row in df_long[df_long['date'].isna()].iterrows():
                original_date = row['date']
                if pd.isna(original_date):
                    # Find the original column name from the melted data
                    original_col = date_columns[idx % len(date_columns)]
                    if original_col in date_mapping:
                        df_long.loc[idx, 'date'] = date_mapping[original_col]
        
        # Convert consumption to numeric, handling various formats
        logger.info("Converting consumption values to numeric...")
        df_long['consumption'] = pd.to_numeric(df_long['consumption'], errors='coerce')
        
        # Handle zero consumption (keep as is, might be legitimate)
        zero_consumption = (df_long['consumption'] == 0).sum()
        logger.info(f"Found {zero_consumption:,} zero consumption readings")
        
        # Remove rows with missing consumption values
        initial_len = len(df_long)
        df_long = df_long.dropna(subset=['consumption'])
        removed = initial_len - len(df_long)
        if removed > 0:
            logger.info(f"Removed {removed:,} rows with missing consumption values")
        
        # Sort by meter_id and date
        df_long = df_long.sort_values(['meter_id', 'date']).reset_index(drop=True)
        
        # Final statistics
        logger.success(f"Converted to long format: {len(df_long):,} records")
        logger.info(f"Date range: {df_long['date'].min()} to {df_long['date'].max()}")
        logger.info(f"Unique meters: {df_long['meter_id'].nunique():,}")
        logger.info(f"Consumption range: {df_long['consumption'].min():.2f} to {df_long['consumption'].max():.2f}")
        
        return df_long
    
    def _extract_date_range(self, df_raw: pd.DataFrame) -> Dict:
        """Extract date range information from wide format dataset"""
        try:
            date_columns = df_raw.columns[:-2].tolist()
            
            # Parse first and last date columns
            start_date_str = date_columns[0]
            end_date_str = date_columns[-1]
            
            start_date = pd.to_datetime(start_date_str, format='%m/%d/%Y', errors='coerce')
            end_date = pd.to_datetime(end_date_str, format='%m/%d/%Y', errors='coerce')
            
            if pd.isna(start_date) or pd.isna(end_date):
                return {
                    'start': start_date_str,
                    'end': end_date_str,
                    'days': len(date_columns)
                }
            
            return {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'days': len(date_columns),
                'duration_days': (end_date - start_date).days + 1
            }
        except Exception as e:
            logger.warning(f"Could not extract date range: {e}")
            return {
                'start': 'unknown',
                'end': 'unknown', 
                'days': len(df_raw.columns) - 2
            }

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
def load_sgcc_data(filename: str = "datasetsmall.csv") -> Tuple[pd.DataFrame, Dict]:
    """Convenience function to load SGCC dataset"""
    loader = SGCCDataLoader()
    return loader.load_dataset(filename=filename)