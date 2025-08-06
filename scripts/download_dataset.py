#!/usr/bin/env python3
"""
Download and setup SGCC dataset for Electricity Theft Detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.data_loader import SGCCDataLoader
from src.data.preprocessor import ElectricityDataPreprocessor
from src.data.feature_engineer import ElectricityFeatureEngineer
from src.utils.validators import DataValidator
from loguru import logger
import pandas as pd


def main():
    """Download and process SGCC dataset"""
    try:
        logger.info("Starting SGCC dataset download and processing...")
        
        # Initialize components
        data_loader = SGCCDataLoader()
        preprocessor = ElectricityDataPreprocessor()
        feature_engineer = ElectricityFeatureEngineer()
        validator = DataValidator()
        
        # Step 1: Load dataset (create synthetic if real not available)
        logger.info("Step 1: Loading SGCC dataset...")
        df, metadata = data_loader.load_dataset(use_synthetic=False)
        
        # Step 2: Initial validation
        logger.info("Step 2: Validating raw data...")
        validation_report = validator.comprehensive_validation(df)
        logger.info(f"Initial validation score: {validation_report['validation_score']}/100")
        
        # Step 3: Prepare time series data
        logger.info("Step 3: Preparing time series data...")
        df = data_loader.prepare_time_series_data(df)
        
        # Step 4: Data preprocessing
        logger.info("Step 4: Preprocessing data...")
        df_processed, preprocessing_report = preprocessor.preprocess_pipeline(df)
        
        # Step 5: Feature engineering
        logger.info("Step 5: Engineering features...")
        
        # Create labels dataframe if available
        if 'label' in df_processed.columns:
            labels_df = df_processed[['meter_id', 'label']].drop_duplicates()
            features_df, feature_report = feature_engineer.combine_all_features(df_processed), {}
            
            # Feature selection
            if len(labels_df) > 0:
                features_df = feature_engineer.select_best_features(features_df, labels_df)
                feature_report = feature_engineer.get_feature_importance_report()
        else:
            logger.warning("No labels found in dataset, skipping feature selection")
            features_df = feature_engineer.combine_all_features(df_processed)
            feature_report = feature_engineer.get_feature_importance_report()
        
        # Step 6: Save processed data
        logger.info("Step 6: Saving processed data...")
        
        # Create processed data directory
        processed_dir = "data/processed"
        os.makedirs(processed_dir, exist_ok=True)
        
        # Save processed datasets
        df_processed.to_csv(f"{processed_dir}/sgcc_processed.csv", index=False)
        features_df.to_csv(f"{processed_dir}/sgcc_features.csv", index=False)
        
        if 'label' in df_processed.columns:
            labels_df.to_csv(f"{processed_dir}/sgcc_labels.csv", index=False)
        
        # Save reports
        reports = {
            'metadata': metadata,
            'validation': validation_report,
            'preprocessing': preprocessing_report,
            'feature_engineering': feature_report
        }
        
        pd.DataFrame([reports]).to_json(f"{processed_dir}/processing_reports.json", indent=2)
        
        # Step 7: Dataset summary
        logger.info("Dataset processing completed successfully!")
        logger.info("=" * 60)
        logger.info("DATASET SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records: {len(df_processed):,}")
        logger.info(f"Unique meters: {df_processed['meter_id'].nunique():,}")
        logger.info(f"Date range: {df_processed['date'].min()} to {df_processed['date'].max()}")
        logger.info(f"Features created: {len(features_df.columns) - 1}")
        
        if 'label' in df_processed.columns:
            theft_rate = df_processed['label'].mean() * 100
            logger.info(f"Theft rate: {theft_rate:.2f}%")
        
        logger.info(f"Data quality score: {validation_report['validation_score']}/100")
        logger.info("=" * 60)
        
        logger.success("SGCC dataset ready for model training!")
        
    except Exception as e:
        logger.error(f"Error processing SGCC dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()