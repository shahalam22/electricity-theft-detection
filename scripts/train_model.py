#!/usr/bin/env python3
"""
Train FA-XGBoost model for Electricity Theft Detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

from src.models.model_trainer import ModelTrainer
from src.models.model_evaluator import ModelEvaluator
from src.models.explainer import ModelExplainer
from src.models.fa_xgboost import FAXGBoostModel
from src.config.settings import settings


def main():
    """Train and evaluate FA-XGBoost model"""
    try:
        logger.info("Starting FA-XGBoost model training pipeline...")
        
        # Check if processed data exists
        processed_dir = Path("data/processed")
        if not processed_dir.exists():
            logger.error("Processed data not found. Run 'python scripts/download_dataset.py' first.")
            sys.exit(1)
        
        # Load processed data
        logger.info("Loading processed data...")
        features_file = processed_dir / "sgcc_features.csv"
        labels_file = processed_dir / "sgcc_labels.csv"
        
        if not features_file.exists() or not labels_file.exists():
            logger.error("Features or labels file not found. Run data processing first.")
            sys.exit(1)
        
        features_df = pd.read_csv(features_file)
        labels_df = pd.read_csv(labels_file)
        
        logger.info(f"Loaded {len(features_df)} feature records and {len(labels_df)} label records")
        
        # Initialize trainer
        trainer = ModelTrainer(random_state=settings.random_state)
        
        # Prepare data splits
        logger.info("Preparing data splits...")
        data_splits = trainer.prepare_data(
            features_df, 
            labels_df,
            test_size=settings.test_size,
            val_size=0.1,
            balance_method='adasyn'
        )
        
        logger.info("Data split summary:")
        logger.info(f"  Training samples: {data_splits['split_info']['train_size']}")
        logger.info(f"  Validation samples: {data_splits['split_info']['val_size']}")
        logger.info(f"  Test samples: {data_splits['split_info']['test_size']}")
        
        # Train FA-XGBoost model with optimization
        logger.info("Training FA-XGBoost model with Firefly Algorithm optimization...")
        training_results = trainer.train_model(
            data_splits,
            model_name='fa_xgboost_optimized',
            optimize_hyperparams=True,
            n_fireflies=15,  # Reduced for faster training
            max_iterations=20  # Reduced for faster training
        )
        
        # Get trained model
        trained_model = trainer.models['fa_xgboost_optimized']
        
        # Evaluate model
        logger.info("Evaluating model performance...")
        evaluator = ModelEvaluator()
        evaluation_results = evaluator.evaluate_model(
            trained_model,
            data_splits['X_test'],
            data_splits['y_test'],
            model_name='fa_xgboost_optimized'
        )
        
        # Generate evaluation report
        logger.info("Generating evaluation report...")
        report = evaluator.generate_evaluation_report(
            'fa_xgboost_optimized',
            save_path="data/models/evaluation_report.json"
        )
        
        # Cross-validation
        logger.info("Performing cross-validation...")
        cv_results = trainer.cross_validate_model(
            data_splits,
            model_name='fa_xgboost_optimized',
            cv_folds=5
        )
        
        # Initialize explainer for sample predictions
        logger.info("Setting up model explainer...")
        explainer = ModelExplainer()
        
        # Initialize SHAP explainer with sample data
        sample_size = min(1000, len(data_splits['X_train']))
        X_sample = data_splits['X_train'].sample(n=sample_size, random_state=settings.random_state)
        
        explainer.initialize_shap_explainer(trained_model, X_sample, explainer_type='tree')
        
        # Generate global feature importance
        global_importance = explainer.explain_global_feature_importance(
            trained_model, X_sample, method='both'
        )
        
        # Generate sample explanations
        logger.info("Generating sample explanations...")
        sample_explanations = []
        
        # Select a few test samples for explanation
        test_samples = data_splits['X_test'].head(3)
        for idx, (_, row) in enumerate(test_samples.iterrows()):
            sample_df = pd.DataFrame([row])
            explanation = explainer.explain_prediction_shap(sample_df, trained_model, top_n=10)
            business_explanation = explainer.generate_business_explanation(explanation)
            
            sample_explanations.append({
                'sample_index': idx,
                'technical_explanation': explanation,
                'business_explanation': business_explanation
            })
        
        # Save training artifacts
        logger.info("Saving training artifacts...")
        saved_files = trainer.save_training_artifacts('fa_xgboost_optimized')
        
        # Save additional results
        results_dir = Path("data/models")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save cross-validation results
        pd.DataFrame([cv_results]).to_json(
            results_dir / "cross_validation_results.json", indent=2
        )
        
        # Save global feature importance
        pd.DataFrame([global_importance]).to_json(
            results_dir / "global_feature_importance.json", indent=2
        )
        
        # Save sample explanations
        pd.DataFrame(sample_explanations).to_json(
            results_dir / "sample_explanations.json", indent=2, default=str
        )
        
        # Print training summary
        logger.info("=" * 60)
        logger.info("MODEL TRAINING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        
        # Training metrics
        metrics = training_results['training_metrics']
        logger.info("TRAINING PERFORMANCE:")
        logger.info(f"  Training ROC-AUC: {metrics['train_roc_auc']:.4f}")
        logger.info(f"  Validation ROC-AUC: {metrics['val_roc_auc']:.4f}")
        logger.info(f"  Training F1-Score: {metrics['train_f1']:.4f}")
        logger.info(f"  Validation F1-Score: {metrics['val_f1']:.4f}")
        
        # Test metrics
        test_metrics = evaluation_results['basic_metrics']
        logger.info("TEST PERFORMANCE:")
        logger.info(f"  Test ROC-AUC: {test_metrics['roc_auc']:.4f}")
        logger.info(f"  Test F1-Score: {test_metrics['f1_score']:.4f}")
        logger.info(f"  Test Precision: {test_metrics['precision']:.4f}")
        logger.info(f"  Test Recall: {test_metrics['recall']:.4f}")
        
        # Cross-validation metrics
        cv_roc_auc = cv_results['cv_results']['roc_auc']
        logger.info("CROSS-VALIDATION PERFORMANCE:")
        logger.info(f"  Mean ROC-AUC: {cv_roc_auc['test_mean']:.4f} ± {cv_roc_auc['test_std']:.4f}")
        
        # Business metrics
        business_metrics = evaluation_results['business_metrics']
        logger.info("BUSINESS IMPACT:")
        logger.info(f"  Detection Rate: {business_metrics['detection_rate']:.2%}")
        logger.info(f"  Inspection Efficiency: {business_metrics['inspection_efficiency']:.2%}")
        logger.info(f"  ROI: {business_metrics['financial_impact']['roi_percentage']:.1f}%")
        logger.info(f"  Net Savings: {business_metrics['financial_impact']['net_savings_bdt']:,.0f} BDT")
        
        # Feature importance
        if 'top_features' in training_results['feature_importance']:
            logger.info("TOP 5 IMPORTANT FEATURES:")
            for i, (feature, importance) in enumerate(training_results['feature_importance']['top_features'][:5]):
                logger.info(f"  {i+1}. {feature}: {importance:.4f}")
        
        # Model parameters
        logger.info("OPTIMIZED PARAMETERS:")
        for param, value in training_results['model_parameters'].items():
            logger.info(f"  {param}: {value}")
        
        # Recommendations
        recommendations = report['recommendations']
        logger.info("RECOMMENDATIONS:")
        for rec in recommendations:
            logger.info(f"  {rec}")
        
        logger.info("=" * 60)
        logger.info("Files saved:")
        for key, filepath in saved_files.items():
            logger.info(f"  {key}: {filepath}")
        
        logger.info(f"  Evaluation report: data/models/evaluation_report.json")
        logger.info(f"  Cross-validation results: data/models/cross_validation_results.json")
        logger.info(f"  Feature importance: data/models/global_feature_importance.json")
        logger.info(f"  Sample explanations: data/models/sample_explanations.json")
        
        logger.success("FA-XGBoost model training pipeline completed successfully!")
        
        # Return success code
        return 0
        
    except Exception as e:
        logger.error(f"Error in model training pipeline: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)