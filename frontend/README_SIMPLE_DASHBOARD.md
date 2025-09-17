# Simple Electricity Theft Detection Dashboard

A lightweight, single-page HTML dashboard for the Electricity Theft Detection System.

## 🚀 Quick Start

### 1. Start the API Server
First, make sure the main API server is running:
```bash
cd ..
python run_app.py
```
The API should be running on `http://localhost:8000`

### 2. Start the Dashboard
```bash
# Option 1: Using Python server script
python serve_dashboard.py

# Option 2: Open directly in browser
# Open simple-dashboard.html in your web browser
```

The dashboard will be available at `http://localhost:3000`

## 📋 Features

### Dashboard Overview
- **System Statistics**: Total alerts, pending alerts, high-risk alerts, total meters
- **Recent Alerts**: Latest 5 alerts with quick action buttons
- **Real-time Data**: Auto-refreshed dashboard stats

### Single Prediction
- **Meter Input**: Enter meter ID and consumption data
- **Multiple Data Points**: Add multiple date/consumption pairs
- **Risk Assessment**: Get immediate theft risk evaluation
- **Alert Generation**: Automatic alert creation for high-risk predictions

### Batch Prediction
- **JSON Input**: Process multiple meters at once
- **Bulk Analysis**: Efficient processing of large datasets
- **Results Summary**: Overview of all processed predictions

### Alert Management
- **View All Alerts**: Complete alert listing with filtering
- **Status Filtering**: Filter by pending, confirmed, or rejected alerts
- **Quick Actions**: Confirm or reject alerts with one click
- **Alert Explanation**: Detailed AI explanation for each alert

### System Information
- **Model Details**: XGBoost model information and performance metrics
- **System Stats**: Real-time system statistics
- **Health Check**: API connectivity and model status verification

## 🎨 Design Features

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Clean, professional interface with gradient backgrounds
- **Risk Color Coding**: Visual risk level indicators (LOW=Green, MEDIUM=Yellow, HIGH=Orange, CRITICAL=Red)
- **Real-time Updates**: Live data refresh and status updates
- **Error Handling**: Comprehensive error messages and user feedback

## 🔧 Technical Details

### API Integration
The dashboard integrates with all available API endpoints:

- `GET /` - Health check
- `GET /health` - System health status
- `POST /api/v1/predict/single` - Single meter prediction
- `POST /api/v1/predict/batch` - Batch predictions
- `GET /api/v1/alerts/` - List alerts (with filtering)
- `POST /api/v1/alerts/{id}/confirm` - Confirm alert
- `POST /api/v1/alerts/{id}/reject` - Reject alert
- `GET /api/v1/explain/alert/{id}` - Alert explanation
- `GET /api/v1/alerts/dashboard/summary` - Dashboard summary
- `GET /api/v1/system/stats` - System statistics
- `GET /model/info` - Model information

### CORS Support
The Python server script includes CORS headers to enable API communication.

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- JavaScript ES6+ features
- Fetch API for HTTP requests

## 📱 Usage Examples

### Single Prediction Example
1. Go to "Single Prediction" tab
2. Enter meter ID: `METER_001`
3. Add consumption data:
   - Date: `2024-01-01`, Consumption: `1500.0`
   - Date: `2024-01-02`, Consumption: `1450.0`
4. Click "Predict Theft Risk"
5. View risk assessment and any generated alerts

### Batch Prediction Example
1. Go to "Batch Prediction" tab
2. Enter JSON data:
```json
[
  {
    "meter_id": "METER_001",
    "consumption_data": [
      {"date": "2024-01-01", "consumption": 1500.0},
      {"date": "2024-01-02", "consumption": 1450.0}
    ]
  },
  {
    "meter_id": "METER_002", 
    "consumption_data": [
      {"date": "2024-01-01", "consumption": 800.0},
      {"date": "2024-01-02", "consumption": 750.0}
    ]
  }
]
```
3. Click "Run Batch Prediction"
4. Review results for all processed meters

## 🔒 Security Notes

- **Local Development**: This dashboard is designed for local development and testing
- **CORS**: CORS is enabled for localhost API access
- **No Authentication**: No built-in authentication (add as needed for production)

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure the API server is running on `http://localhost:8000`
   - Check browser console for detailed error messages

2. **Dashboard Not Loading**
   - Verify `simple-dashboard.html` exists in the frontend directory
   - Try opening the file directly in browser

3. **Port Already in Use**
   - Change the PORT variable in `serve_dashboard.py`
   - Kill existing processes using port 3000

### Browser Console
Check browser developer tools (F12) for JavaScript errors and network issues.

## 🎯 Next Steps

- Add authentication for production deployment
- Implement WebSocket for real-time updates
- Add data visualization charts
- Export functionality for reports
- Mobile app integration