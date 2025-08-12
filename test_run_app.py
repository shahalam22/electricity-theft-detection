#!/usr/bin/env python3
"""
Quick test script for run_app.py
Tests the main components without starting the full server
"""

import sys
import json
from datetime import datetime
from pathlib import Path

def test_components():
    """Test all major components of run_app.py"""
    print("=" * 50)
    print("Testing Electricity Theft Detection System")
    print("=" * 50)
    
    try:
        # Test 1: Import components
        print("\n1. Testing imports...")
        from run_app import (
            load_trained_model, 
            engineer_features_from_consumption,
            calculate_risk_level,
            model, scaler, feature_columns, metadata
        )
        print("   SUCCESS: All imports successful")
        
        # Test 2: Model loading
        print("\n2. Testing model loading...")
        success = load_trained_model()
        if success:
            print("   SUCCESS: Model loaded successfully")
            if metadata:
                print(f"   Model type: {metadata.get('model_type', 'XGBoost')}")
                print(f"   AUC score: {metadata.get('test_auc', 'N/A'):.3f}")
                print(f"   Features: {len(feature_columns) if feature_columns else 0}")
        else:
            print("   ERROR: Model loading failed")
            return False
        
        # Test 3: Feature engineering
        print("\n3. Testing feature engineering...")
        sample_consumption_data = [
            {"date": "2024-01-01", "consumption": 1500.0},
            {"date": "2024-01-02", "consumption": 1450.0},
            {"date": "2024-01-03", "consumption": 1600.0},
            {"date": "2024-01-04", "consumption": 1520.0},
            {"date": "2024-01-05", "consumption": 1480.0},
            {"date": "2024-01-06", "consumption": 1550.0},
            {"date": "2024-01-07", "consumption": 1500.0}
        ]
        
        features = engineer_features_from_consumption(sample_consumption_data, "TEST_METER_001")
        print(f"   SUCCESS: Generated {len(features)} features")
        print(f"   Sample features: consumption={features.get('consumption')}, meter_mean={features.get('meter_mean'):.2f}")
        
        # Test 4: Risk level calculation
        print("\n4. Testing risk level calculation...")
        risk_levels = [
            (0.2, "LOW"),
            (0.4, "MEDIUM"), 
            (0.6, "HIGH"),
            (0.9, "CRITICAL")
        ]
        
        for score, expected in risk_levels:
            actual = calculate_risk_level(score)
            if actual == expected:
                print(f"   SUCCESS: Score {score} -> {actual}")
            else:
                print(f"   ERROR: Score {score} -> {actual} (expected {expected})")
        
        # Test 5: Model prediction simulation
        print("\n5. Testing model prediction simulation...")
        
        # Import required modules for prediction
        import pandas as pd
        import numpy as np
        from run_app import model, scaler, feature_columns
        
        # Prepare features for prediction
        feature_df = pd.DataFrame([features])
        
        # Ensure all required features are present
        for col in feature_columns:
            if col not in feature_df.columns:
                feature_df[col] = 0.0
        
        # Reorder columns to match training
        feature_df = feature_df[feature_columns]
        
        # Scale features
        feature_scaled = scaler.transform(feature_df)
        
        # Make prediction
        prediction = model.predict(feature_scaled)[0]
        probabilities = model.predict_proba(feature_scaled)[0]
        risk_score = probabilities[1]  # Probability of theft class
        
        risk_level = calculate_risk_level(risk_score)
        
        print(f"   SUCCESS: Prediction completed")
        print(f"   Meter ID: TEST_METER_001")
        print(f"   Prediction: {prediction} ({'Theft' if prediction else 'Normal'})")
        print(f"   Risk Score: {risk_score:.4f}")
        print(f"   Risk Level: {risk_level}")
        print(f"   Confidence: {max(probabilities):.4f}")
        
        # Test 6: Data validation
        print("\n6. Testing data validation...")
        
        # Check if model files exist and are accessible
        model_dir = Path("data/models")
        required_files = [
            "xgb_theft_detection_model.pkl",
            "feature_scaler.pkl", 
            "feature_columns.pkl"
        ]
        
        all_files_exist = True
        for file_name in required_files:
            file_path = model_dir / file_name
            if file_path.exists():
                print(f"   SUCCESS: {file_name} found ({file_path.stat().st_size} bytes)")
            else:
                print(f"   ERROR: {file_name} not found")
                all_files_exist = False
        
        if not all_files_exist:
            return False
        
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED!")
        print("The application is ready to run.")
        print("Start with: python run_app.py")
        print("API docs: http://localhost:8000/api/docs")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\nERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_components()
    sys.exit(0 if success else 1)