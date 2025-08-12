# ⚡ Electricity Theft Detection System

**Production-ready AI system** for detecting electricity theft using trained XGBoost model on smart meter consumption data.

> **🎯 Status**: **PRODUCTION READY** - Trained model integrated with full API backend

## 🌟 Features

- **🤖 Trained XGBoost Model**: 86.7% AUC accuracy on SGCC dataset
- **📊 27 Engineered Features**: Advanced time-series and statistical features
- **🚀 FastAPI Backend**: Complete REST API with real-time predictions
- **📈 Web Dashboard**: React frontend for monitoring and alerts
- **🔍 Real-time Detection**: Live theft prediction with risk scoring
- **📋 Alert Management**: Automatic alert generation and investigation workflow

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Ensure you have Python 3.8+ and virtual environment
cd electricity-theft-detection
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Model Setup ✅ **READY**

Your trained model is already integrated! The system includes:
```
data/models/
├── xgb_theft_detection_model.pkl  # Trained XGBoost model (86.7% AUC)
├── feature_scaler.pkl              # Feature normalization scaler  
├── feature_columns.pkl             # 27 engineered features
└── model_metadata.json             # Performance metrics
```

> 💡 **Want to retrain the model?** See the [Model Training with Google Colab](#-model-training-with-google-colab) section below.

### 3. Start Application

#### **Option 1: Production Mode (Recommended)**

```bash
# Activate virtual environment
venv\Scripts\activate

# Start production server with trained model
python run_app.py
```

#### **Option 2: Demo Mode**

```bash
# Start demo server with mock predictions
python run_simple.py
```

#### **Option 3: Frontend Dashboard (Optional)**

```bash
# In a separate terminal
cd frontend
npm install  # First time only
npm run dev
```

### 4. Access Points 🌐

- **🔧 API Server**: http://localhost:8000
- **📖 API Documentation**: http://localhost:8000/api/docs
- **❤️ Health Check**: http://localhost:8000/health
- **📊 React Dashboard**: http://localhost:3000 *(if frontend running)*

## 🤖 Model Performance

**✅ Current Production Model (Trained on SGCC Dataset):**

| Metric | Value | Description |
|--------|-------|-------------|
| **AUC Score** | **0.8672** | Area Under ROC Curve (86.7% accuracy) |
| **Training Samples** | **740,689** | Records used for training |
| **Test Samples** | **134,463** | Records used for validation |
| **Features** | **27** | Engineered time-series & statistical features |
| **Model Type** | **XGBoost** | Extreme Gradient Boosting Classifier |
| **Dataset** | **SGCC** | State Grid Corporation of China |
| **Theft Rate** | **8.19%** | Balanced dataset with realistic fraud distribution |

**🔍 Feature Categories:**
- **Temporal Features**: Weekend patterns, seasonal variations, day-of-week trends
- **Statistical Features**: Mean, std, min, max, percentiles, skewness, kurtosis  
- **Rolling Windows**: 7-day and 30-day consumption statistics
- **Lag Features**: Previous consumption values for trend analysis

## 🎓 Model Training with Google Colab

### 📋 **Training Overview**

The current production model was trained using Google Colab with GPU acceleration. Here's how to retrain or create your own model:

### **1. Dataset Preparation**

#### **SGCC Dataset Format**
Your dataset should be in CSV format with the following structure:
```csv
01/01/2014,01/02/2014,01/03/2014,...,CONS_NO,FLAG
2401,2500,2674,...,A0E791400CF1C48C43DC26A68227854A,1
3318,282,540,...,B415F931D3BFB17ACEF48BC648B04FC2,1
4150,3876,3692,...,C28F8E5F9F1A4B2E8D7C6A5B3E2D1F4G,0
```

**Column Structure:**
- **Date Columns**: Daily consumption values (e.g., `01/01/2014`, `01/02/2014`, etc.)
- **CONS_NO**: Unique meter identifier (customer hash)
- **FLAG**: Target variable (0 = Normal, 1 = Theft)

#### **Data Requirements**
- **Minimum Records**: 10,000+ for meaningful training
- **Theft Rate**: 5-15% (realistic fraud distribution)
- **Time Coverage**: At least 30 days of consumption data per meter
- **Data Quality**: Minimal missing values, realistic consumption patterns

### **2. Google Colab Training Process**

#### **Step 1: Setup Colab Environment**

```python
# 1. Upload colab_training_notebook.ipynb to Google Colab
# 2. Enable GPU Runtime: Runtime > Change runtime type > Hardware accelerator: GPU
# 3. Install required packages
!pip install xgboost scikit-learn pandas numpy joblib loguru imbalanced-learn
```

#### **Step 2: Upload Your Dataset**

```python
# Upload your CSV dataset when prompted
from google.colab import files
uploaded = files.upload()

# Your dataset should be named 'datasetsmall.csv'
import pandas as pd
df = pd.read_csv('datasetsmall.csv')
print(f"Dataset shape: {df.shape}")
print(f"Theft rate: {df['FLAG'].mean()*100:.2f}%")
```

#### **Step 3: Data Preprocessing Pipeline**

The notebook includes comprehensive preprocessing:

```python
# Automatic preprocessing steps:
# 1. Wide-to-long format conversion
# 2. Date parsing and validation  
# 3. Missing value imputation
# 4. Outlier detection and handling
# 5. Data quality validation
```

**Preprocessing Features:**
- **Format Conversion**: Wide CSV → Long time-series format
- **Date Handling**: Automatic date column detection and parsing
- **Missing Values**: Linear interpolation for time-series data
- **Outlier Detection**: Z-score and IQR-based outlier capping
- **Data Validation**: Quality checks and statistics reporting

#### **Step 4: Feature Engineering**

**27 Engineered Features Created:**

1. **Temporal Features (6)**:
   - `year`, `month`, `day_of_week`, `day_of_year`
   - `is_weekend`, `season_winter`

2. **Rolling Statistics (8)**:
   - `consumption_7d_mean`, `consumption_7d_std`
   - `consumption_7d_max`, `consumption_7d_min`
   - `consumption_30d_mean`, `consumption_30d_std`

3. **Lag Features (2)**:
   - `consumption_lag1`, `consumption_lag7`

4. **Meter Aggregates (11)**:
   - `meter_mean`, `meter_std`, `meter_min`, `meter_max`
   - `meter_median`, `meter_q1`, `meter_q3`
   - `meter_skew`, `meter_kurt`, `meter_range`, `meter_iqr`, `meter_cv`

#### **Step 5: Model Training**

**XGBoost Configuration:**
```python
# Optimized hyperparameters for theft detection
model_params = {
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 200,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'scale_pos_weight': 10,  # Handle class imbalance
    'random_state': 42
}
```

**Training Process:**
- **Class Balancing**: SMOTE oversampling for minority class
- **Cross Validation**: 5-fold stratified cross-validation
- **Feature Selection**: SelectKBest with f_classif scoring
- **Model Validation**: Separate test set evaluation
- **Performance Metrics**: AUC, Precision, Recall, F1-Score

#### **Step 6: Model Export**

The notebook automatically packages the trained model:

```python
# Creates model package with:
# - xgb_theft_detection_model.pkl (trained model)
# - feature_scaler.pkl (StandardScaler)
# - feature_columns.pkl (feature list)
# - model_metadata.json (training stats)

# Downloads as: electricity_theft_detection_model.zip
```

### **3. Training Performance Expectations**

**Typical Training Results:**
- **Training Time**: 10-15 minutes (Colab GPU)
- **Expected AUC**: 0.85-0.95 (depending on data quality)
- **Memory Usage**: 2-4GB RAM for 100k+ samples
- **Model Size**: ~1MB for XGBoost model file

**Performance Factors:**
- **Data Quality**: Clean, realistic consumption patterns
- **Theft Rate**: 5-15% optimal for training stability
- **Feature Engineering**: Time-series features crucial for performance
- **Class Balancing**: SMOTE improves minority class detection

### **4. Custom Dataset Training**

#### **Prepare Your Data**

1. **Format Your CSV**:
   ```bash
   # Required columns: daily consumption + CONS_NO + FLAG
   # Example: 01/01/2024,01/02/2024,...,01/30/2024,METER_ID,LABEL
   ```

2. **Data Quality Checklist**:
   - ✅ Consistent date format across columns
   - ✅ Unique meter identifiers in CONS_NO
   - ✅ Binary labels (0/1) in FLAG column  
   - ✅ Realistic consumption values (no negative values)
   - ✅ Sufficient data (30+ days per meter)

3. **Upload to Colab**:
   - Rename your file to `datasetsmall.csv`
   - Upload via Colab's file upload interface
   - Run the training notebook cells sequentially

#### **Training Best Practices**

1. **Data Split**: 80% training, 20% testing
2. **Validation**: Use stratified splits to preserve class distribution
3. **Feature Engineering**: Let the notebook handle automatic feature creation
4. **Hyperparameter Tuning**: Use provided optimal parameters
5. **Model Evaluation**: Check AUC > 0.8 for production readiness

### **5. Model Deployment**

After training in Colab:

```bash
# 1. Download electricity_theft_detection_model.zip from Colab
# 2. Extract to your local project
unzip electricity_theft_detection_model.zip -d data/models/

# 3. Verify model files
ls data/models/
# Should show: xgb_theft_detection_model.pkl, feature_scaler.pkl, 
#              feature_columns.pkl, model_metadata.json

# 4. Test the model
python test_run_app.py

# 5. Start production server
python run_app.py
```

### **6. Retraining Schedule**

**Recommended Retraining Frequency:**
- **Monthly**: For high-volume utilities with changing patterns
- **Quarterly**: For stable consumption environments
- **Data-Driven**: When model performance drops below 80% AUC
- **Event-Based**: After significant infrastructure changes

**Retraining Indicators:**
- Declining prediction accuracy
- Increased false positive rates
- Seasonal pattern changes
- New theft methodologies detected

## 🔄 Future Model Retraining Guide

### **When to Retrain Your Model**

**🚨 Performance Degradation Signals:**
- Model AUC drops below 0.8 on recent data
- False positive rate increases above 20%
- User feedback indicates poor detection quality
- Seasonal consumption patterns change significantly
- New theft methodologies emerge in your area

**📅 Scheduled Retraining Scenarios:**
- **Quarterly Updates**: For stable utility environments
- **Monthly Updates**: For high-volume, changing consumption patterns
- **Event-Driven**: After major infrastructure changes or policy updates
- **Data-Driven**: When you accumulate 20%+ new consumption data

### **Step-by-Step Retraining Process**

#### **Phase 1: Data Collection & Preparation**

**1. Gather New Data**
```bash
# Collect new consumption data in the same SGCC format
# Required columns: date columns + CONS_NO + FLAG
# Recommended: 6+ months of new data for meaningful retraining
```

**2. Data Quality Assessment**
```python
# Use this Python script to validate your new data
import pandas as pd

def validate_retraining_data(csv_file):
    df = pd.read_csv(csv_file)
    
    # Basic validation
    print(f"Dataset shape: {df.shape}")
    print(f"Unique meters: {df['CONS_NO'].nunique()}")
    print(f"Date range: {df.columns[0]} to {df.columns[-3]}")
    print(f"Theft rate: {df['FLAG'].mean()*100:.2f}%")
    
    # Quality checks
    missing_data = df.isnull().sum().sum()
    print(f"Missing values: {missing_data}")
    
    # Recommended thresholds
    if df.shape[0] < 10000:
        print("⚠️  Warning: Less than 10,000 records. Consider collecting more data.")
    if df['FLAG'].mean() < 0.05 or df['FLAG'].mean() > 0.15:
        print("⚠️  Warning: Theft rate outside optimal 5-15% range.")
    if missing_data > df.shape[0] * 0.1:
        print("⚠️  Warning: High missing data. Consider data cleaning.")
    
    return df

# Usage
new_data = validate_retraining_data('new_consumption_data.csv')
```

**3. Combine with Historical Data (Optional)**
```python
# Option A: Train on new data only (for concept drift)
# Option B: Combine with historical data (for stability)

# If combining datasets:
# - Weight recent data more heavily
# - Ensure balanced theft representation
# - Remove outdated patterns (data older than 2 years)
```

#### **Phase 2: Google Colab Retraining**

**1. Prepare Colab Environment**
```python
# 1. Open Google Colab
# 2. Upload fresh copy of colab_training_notebook.ipynb
# 3. Enable GPU runtime for faster training
# 4. Install/update packages
!pip install --upgrade xgboost scikit-learn pandas numpy joblib loguru imbalanced-learn
```

**2. Upload New Dataset**
```python
from google.colab import files
import pandas as pd

# Upload your new dataset
uploaded = files.upload()

# Rename to expected filename
!mv your_new_data.csv datasetsmall.csv

# Validate data format
df = pd.read_csv('datasetsmall.csv')
print(f"New dataset loaded: {df.shape}")
print(f"Theft rate: {df['FLAG'].mean()*100:.2f}%")
```

**3. Compare with Previous Model**
```python
# Before retraining, document current model performance
current_model_stats = {
    'auc': 0.8672,  # Your current model's AUC
    'training_date': '2025-08-06',
    'training_samples': 740689,
    'theft_rate': 8.19
}

print("Previous model performance:")
print(f"AUC: {current_model_stats['auc']:.3f}")
print(f"Training samples: {current_model_stats['training_samples']:,}")
```

**4. Run Complete Training Pipeline**
```python
# Execute all notebook cells in sequence:
# 1. Data loading and validation
# 2. Preprocessing (wide-to-long conversion)
# 3. Feature engineering (27 features)
# 4. Model training with cross-validation
# 5. Model evaluation and comparison
# 6. Model export and packaging

# The notebook will automatically:
# - Handle preprocessing
# - Engineer all 27 features
# - Train XGBoost with optimal hyperparameters
# - Validate performance with cross-validation
# - Export new model package
```

#### **Phase 3: Model Comparison & Validation**

**1. Performance Comparison**
```python
# Notebook automatically compares new vs old model
# Key metrics to evaluate:

new_model_performance = {
    'auc_improvement': '+0.015',  # Should be positive
    'precision_change': '+2.3%',  # Higher precision preferred
    'recall_change': '+1.8%',     # Higher recall preferred
    'training_time': '12 minutes', # Training efficiency
    'model_size': '1.2MB'         # Model complexity
}

# Decision criteria:
# ✅ Deploy if AUC improves by >1%
# ⚠️  Review if AUC drops by <2%
# ❌ Don't deploy if AUC drops by >2%
```

**2. Validation on Historical Data**
```python
# Test new model on previous period's data
# Ensure no significant performance regression
# Validate that old theft cases are still detected
```

#### **Phase 4: Model Deployment**

**1. Download New Model Package**
```python
# Colab automatically creates: electricity_theft_detection_model_v2.zip
# Download contains:
# - xgb_theft_detection_model.pkl (new model)
# - feature_scaler.pkl (updated scaler)
# - feature_columns.pkl (same 27 features)
# - model_metadata.json (new training stats)
```

**2. Backup Current Model**
```bash
# Create backup of current production model
cd "your-project-directory"
mkdir -p backups/model_backup_$(date +%Y%m%d)
cp -r data/models/* backups/model_backup_$(date +%Y%m%d)/

echo "Current model backed up successfully"
```

**3. Deploy New Model**
```bash
# Replace current model with new trained model
cd "your-project-directory"

# Extract new model package
unzip electricity_theft_detection_model_v2.zip -d data/models/

# Verify new model files
ls -la data/models/
# Should show updated timestamps on all files

# Test new model
python test_run_app.py

# Expected output:
# ✅ Model loading
# ✅ Feature engineering (27 features)  
# ✅ Risk level calculation
# ✅ End-to-end prediction
```

**4. Gradual Rollout (Production Best Practice)**
```bash
# Option 1: Shadow mode (parallel testing)
# Run new model alongside old model for 1-2 weeks
# Compare predictions and performance

# Option 2: Canary deployment
# Deploy to subset of meters (10-20%)
# Monitor performance before full deployment

# Option 3: A/B testing
# Split traffic between old and new models
# Measure business impact (detection rate, false positives)
```

#### **Phase 5: Post-Deployment Monitoring**

**1. Performance Monitoring**
```python
# Monitor these metrics for first 30 days:
monitoring_metrics = {
    'daily_predictions': 'Track prediction volume',
    'risk_score_distribution': 'Ensure similar to training',
    'alert_generation_rate': 'Monitor for sudden changes',
    'false_positive_feedback': 'User feedback on alerts',
    'detection_accuracy': 'Validated theft cases'
}

# Set up alerts for:
# - Prediction failures or errors
# - Unusual risk score distributions  
# - Significant changes in alert volume
# - User complaints about accuracy
```

**2. Model Performance Tracking**
```bash
# Weekly performance review
curl http://localhost:8000/model/info
# Check model metadata and performance stats

# Monthly detailed analysis
# - Compare AUC on recent data vs training AUC
# - Analyze false positive/negative cases
# - Review user feedback and confirmed cases
```

### **Retraining Checklist ✅**

**Before Retraining:**
- [ ] Performance degradation confirmed (AUC < 0.8)
- [ ] New data collected (minimum 10,000 records)
- [ ] Data quality validated (theft rate 5-15%)
- [ ] Business stakeholders notified
- [ ] Current model backed up

**During Retraining:**
- [ ] Colab environment prepared with GPU
- [ ] Data preprocessing completed successfully
- [ ] All 27 features engineered correctly
- [ ] Model training converged (no errors)
- [ ] New model AUC ≥ current model AUC
- [ ] Cross-validation results acceptable

**After Deployment:**
- [ ] Model deployment verified with test suite
- [ ] Production API functioning correctly
- [ ] Monitoring alerts configured
- [ ] Performance baseline established
- [ ] Documentation updated with new model stats
- [ ] Team trained on new model characteristics

### **Retraining Troubleshooting**

| Issue | Solution |
|-------|----------|
| **New model performs worse** | Review data quality, consider combining with historical data |
| **Colab training fails** | Check GPU availability, reduce dataset size, update packages |
| **Feature engineering errors** | Validate date formats, check for missing columns |
| **Model won't load locally** | Verify all 4 files downloaded, check file permissions |
| **High false positive rate** | Adjust prediction threshold, review labeling quality |
| **Poor convergence** | Tune hyperparameters, increase n_estimators |

### **Long-term Model Management**

**📊 Model Versioning:**
```bash
# Keep track of model versions
data/models/
├── v1.0_20250806/  # Current production
├── v1.1_20251101/  # Quarterly update
├── v2.0_20260201/  # Major retraining
└── current/        # Symlink to active model
```

**📈 Performance Benchmarks:**
- Maintain model performance history
- Track business metrics (cost savings, theft prevention)
- Document seasonal patterns and adjustments
- Plan for major model architecture upgrades

**🔄 Automation Opportunities:**
- Automated data quality checks
- Scheduled retraining pipelines
- Performance monitoring dashboards
- Alert-driven retraining triggers

## 📊 API Usage & Examples

### Single Meter Prediction

```bash
curl -X POST "http://localhost:8000/api/v1/predict/single" \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "METER_001",
    "consumption_data": [
      {"date": "2024-01-01", "consumption": 1500.0},
      {"date": "2024-01-02", "consumption": 1450.0},
      {"date": "2024-01-03", "consumption": 1600.0}
    ],
    "include_explanation": true
  }'
```

**Response:**
```json
{
  "meter_id": "METER_001",
  "prediction": 0,
  "risk_score": 0.1270,
  "risk_level": "LOW",
  "confidence": 0.8730,
  "is_theft": false,
  "processing_time_ms": 45.2
}
```

### Training Data Format (SGCC Dataset)

```csv
01/01/2014,01/02/2014,01/03/2014,...,CONS_NO,FLAG
2401,2500,2674,...,A0E791400CF1C48C43DC26A68227854A,1
3318,282,540,...,B415F931D3BFB17ACEF48BC648B04FC2,1
```

- **Date columns**: Daily consumption values (kWh)
- **CONS_NO**: Unique meter identifier  
- **FLAG**: 0 = normal, 1 = theft

## 📡 Complete API Reference

### 🔍 **Core System Endpoints**
```bash
GET  /                    # System information & status
GET  /health              # Health check with model status
GET  /model/info          # Detailed model information
GET  /api/docs            # Interactive API documentation (Swagger)
```

### 📊 **Data Management**
```bash
POST /api/v1/data/meters/register    # Register new meter
GET  /api/v1/data/meters             # List all meters  
GET  /api/v1/data/meters/{meter_id}  # Get specific meter
```

### 🤖 **ML Predictions (Production)**
```bash
POST /api/v1/predict/single    # Single meter theft prediction
POST /api/v1/predict/batch     # Batch predictions (multiple meters)
```

### 🚨 **Alert Management**
```bash
GET  /api/v1/alerts/                    # List alerts with filtering
GET  /api/v1/alerts/{alert_id}          # Get alert details
POST /api/v1/alerts/{alert_id}/confirm  # Confirm theft alert
POST /api/v1/alerts/{alert_id}/reject   # Reject false positive
GET  /api/v1/alerts/dashboard/summary   # Dashboard statistics
```

### 🔍 **Model Explanations & Analytics**
```bash
GET  /api/v1/explain/alert/{alert_id}   # Explain specific alert
GET  /api/v1/system/stats               # System performance stats
```

## 🏗️ System Architecture

### **Production Mode Features (run_app.py)**
- ✅ **Trained XGBoost Model** - Real AI predictions with 86.7% AUC
- ✅ **27 Engineered Features** - Advanced time-series analysis
- ✅ **Real-time Theft Detection** - Live risk scoring & classification
- ✅ **Automatic Alert Generation** - Theft predictions → Alerts
- ✅ **Complete API Backend** - 15+ REST endpoints
- ✅ **Alert Management** - Confirm/reject workflow
- ✅ **Performance Monitoring** - System stats & model metrics

### **Demo Mode Features (run_simple.py)**
- ✅ Mock predictions for testing
- ✅ Sample alerts and meter data
- ✅ Full API compatibility
- ✅ Development & demo purposes

### **Project Structure**

```
electricity-theft-detection/
├── run_app.py                     # 🚀 Main application server (PRODUCTION)
├── run_simple.py                  # 💻 Demo version (for testing)
├── test_run_app.py               # 🧪 Application test suite
├── 
├── src/                          # Core source code
│   ├── api/                      # FastAPI routes & models
│   ├── data/                     # Data processing pipeline
│   ├── models/                   # ML model utilities
│   ├── config/                   # Configuration management
│   └── utils/                    # Utility functions
├── 
├── data/                         # Data storage
│   ├── models/                   # ✅ Trained model files
│   │   ├── xgb_theft_detection_model.pkl
│   │   ├── feature_scaler.pkl
│   │   ├── feature_columns.pkl
│   │   └── model_metadata.json
│   ├── raw/sgcc_dataset/         # Original dataset
│   └── processed/                # Processed data
├── 
├── frontend/                     # React web dashboard
├── requirements.txt              # Python dependencies
├── colab_training_notebook.ipynb # 🎓 Google Colab model training
└── *.md                         # Documentation
```

## 📊 Dashboard Features

### 1. 📈 **Main Dashboard**
- Key performance metrics (Active Alerts, Total Meters, Potential Savings)
- Real-time detection trend charts
- Risk level distribution
- Recent alerts overview
- Quick action buttons

### 2. 🚨 **Alert Management** 
- Comprehensive alert list with filtering
- Risk level indicators and status badges
- Alert detail view with consumption analysis
- Confirm/Reject workflow
- AI explanation integration

### 3. 🔮 **Predictions Interface**
- Single meter prediction form
- Batch prediction file upload
- Model performance visualization
- Risk analysis charts
- Real-time prediction results

### 4. 📊 **Data Management**
- Meter registration form
- Bulk data upload (drag & drop)
- Meter management interface
- Upload statistics monitoring

### 5. ⚙️ **System Settings**
- General configuration
- Alert threshold settings  
- ML model parameters
- Security settings
- System maintenance tools

## 🛠️ Technology Stack

### **Backend (Production)**
- **FastAPI 0.104.1** - Modern async Python web framework  
- **XGBoost 2.0.2** - Trained ML model for theft detection
- **scikit-learn 1.3.2** - Feature scaling and preprocessing
- **pandas 2.1.4** - Data manipulation and feature engineering
- **joblib** - Model serialization and loading
- **Uvicorn** - High-performance ASGI server
- **Pydantic** - Data validation and serialization

### **Frontend**
- **React 18** - Modern UI framework
- **Vite** - Fast build tool and dev server  
- **Tailwind CSS** - Utility-first styling framework
- **React Router** - Client-side navigation
- **React Query** - Server state management & caching
- **Recharts** - Interactive data visualization
- **Lucide React** - Beautiful icon library
- **React Hot Toast** - Toast notifications

## 🧪 Testing & Validation

### **Test Complete System**
```bash
# Comprehensive test suite
python test_run_app.py

# Expected output:
# ✅ Model loading
# ✅ Feature engineering (27 features)
# ✅ Risk level calculation  
# ✅ End-to-end prediction
# ✅ File validation
```

### **Manual Testing**
```bash
# Start production server
python run_app.py

# Test health endpoint
curl http://localhost:8000/health

# Test single prediction
curl -X POST "http://localhost:8000/api/v1/predict/single" \
  -H "Content-Type: application/json" \
  -d '{"meter_id": "TEST_001", "consumption_data": [{"date": "2024-01-01", "consumption": 1500}]}'
```

## 🎯 Key Commands

```bash
# Test all components
python test_run_app.py

# Start production server
python run_app.py

# Start demo version (mock predictions)
python run_simple.py

# Check system health
curl http://localhost:8000/health
```

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Model not found"** | Check `data/models/` directory has all 4 files |
| **"Import errors"** | Activate virtual environment: `venv\Scripts\activate` |
| **"Port already in use"** | Kill process: `taskkill /F /IM python.exe` or use different port |
| **"Prediction fails"** | Check consumption data format and minimum 1 day of data |
| **Slow predictions** | Normal for first prediction (~50ms), subsequent ones are faster |

## 🚀 Development & Customization

### **Prerequisites**
- **Python 3.8+** with virtual environment
- **Node.js 16+** for frontend development
- **Git** for version control

### **Backend Development**
```bash
# Setup environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Development mode with auto-reload
uvicorn run_app:app --reload --port 8000
```

### **Frontend Development**  
```bash
cd frontend
npm install
npm run dev     # Development server
npm run build   # Production build
npm run preview # Preview production build
```

## 🎉 Production Ready!

**✅ System Status:**
1. **Model**: Trained XGBoost (86.7% AUC) ✅
2. **Training**: Google Colab notebook for custom models ✅
3. **API**: Full FastAPI backend with 15+ endpoints ✅  
4. **Features**: 27 engineered features from consumption data ✅
5. **Alerts**: Automatic detection and management ✅
6. **Documentation**: Complete API docs at `/api/docs` ✅

**🚀 Ready for:**
- Real-time electricity theft detection
- Custom model training with your data
- Production deployment  
- Integration with utility systems
- Scalable fraud monitoring

## 📚 Documentation

- **📖 API Documentation**: http://localhost:8000/api/docs *(Interactive Swagger UI)*
- **❤️ Health Check**: http://localhost:8000/health *(System status)*
- **📊 Model Info**: http://localhost:8000/model/info *(ML model details)*

---

Built for **real-world electricity theft detection**! ⚡

> **💡 Tip**: Visit http://localhost:8000/api/docs when running for complete interactive API documentation