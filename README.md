# Electricity Theft Detection System

An AI-powered electricity theft detection system using the SGCC dataset with FA-XGBoost and statistical features for smart grid security.

## 🚀 Features

- **Real-time Theft Detection**: Analyze consumption patterns and detect anomalies
- **Statistical Feature Engineering**: Extract 50+ features using tsfresh
- **Explainable AI**: SHAP/LIME explanations for predictions
- **Web Dashboard**: User-friendly interface for utility staff
- **Periodic Retraining**: Continuous learning with confirmed labels
- **REST API**: Easy integration with existing utility systems

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Smart Meters  │───▶│   FastAPI    │───▶│   PostgreSQL    │
│   (Data Source) │    │   Backend    │    │   Database      │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │                      │
                              ▼                      ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   React         │◀───│  FA-XGBoost  │◀───│   Feature       │
│   Dashboard     │    │   Model      │    │   Engineering   │
└─────────────────┘    └──────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Docker & Docker Compose (optional)
- Node.js 16+ (for frontend)

## 🛠️ Quick Start

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd electricity-theft-detection
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - API: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

### Option 2: Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   # Install PostgreSQL and create database
   createdb electricity_theft_db
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database**
   ```bash
   python scripts/setup_database.py
   ```

6. **Start the API server**
   ```bash
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📊 Dataset Setup

1. **Download SGCC Dataset**
   ```bash
   python scripts/download_dataset.py
   ```

2. **Process the dataset**
   ```bash
   python scripts/process_sgcc_data.py
   ```

## 🧪 Model Training

1. **Train the FA-XGBoost model**
   ```bash
   python scripts/train_model.py
   ```

2. **Evaluate model performance**
   ```bash
   python scripts/evaluate_model.py
   ```

## 📱 API Usage

### Data Ingestion
```bash
curl -X POST "http://localhost:8000/api/v1/data/consumption" \
     -H "Content-Type: application/json" \
     -d '{
       "meter_id": "METER_001",
       "date": "2024-01-15",
       "consumption": 25.7
     }'
```

### Theft Prediction
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "meter_id": "METER_001",
       "consumption_data": [...]
     }'
```

### Get Alerts
```bash
curl "http://localhost:8000/api/v1/alerts?status=pending&limit=10"
```

## 🖥️ Dashboard Features

- **Alert Overview**: Summary of pending and confirmed theft cases
- **Meter Analysis**: Individual meter consumption patterns
- **Feature Explanations**: SHAP values for each prediction
- **Manual Review**: Confirm/reject theft alerts
- **Performance Metrics**: Model accuracy and system statistics

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test module
pytest tests/test_api/
```

## 📈 Performance

- **Throughput**: 50,000+ meter readings per day
- **Latency**: <100ms for real-time predictions
- **Accuracy**: >95% ROC-AUC on SGCC dataset
- **Scalability**: Horizontal scaling with Docker

## 🔐 Security

- Input validation and sanitization
- SQL injection prevention
- Rate limiting on API endpoints
- Authentication and authorization
- Encrypted data storage

## 📚 Project Structure

```
electricity-theft-detection/
├── src/
│   ├── config/          # Configuration and settings
│   ├── data/           # Data processing modules
│   ├── models/         # ML model implementations
│   ├── api/            # FastAPI routes and models
│   ├── database/       # Database models and schemas
│   └── utils/          # Utility functions
├── frontend/           # React dashboard
├── notebooks/          # Jupyter notebooks for analysis
├── scripts/           # Setup and utility scripts
├── tests/             # Test suite
├── docs/              # Documentation
└── data/              # Dataset and model files
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For support and questions:
- Open an issue on GitHub
- Email: support@electricity-theft-detection.com
- Documentation: [docs/](docs/)

## 🏆 Acknowledgments

- SGCC dataset providers
- Open source ML community
- FastAPI and React communities
- Bangladesh utility partners