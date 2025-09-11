import React, { useState } from 'react'
import { useQuery, useMutation } from 'react-query'
import {
  TrendingUpIcon,
  ZapIcon,
  PlayIcon,
  PauseIcon,
  RefreshCwIcon,
  DownloadIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  BarChart3Icon,
  EyeIcon,
  UploadIcon,
  ClockIcon
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { apiService, apiUtils } from '../utils/api'
import toast from 'react-hot-toast'

const PredictionCard = ({ title, value, change, icon: Icon, color = 'primary', description }) => {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    warning: 'bg-warning-50 text-warning-600',
    danger: 'bg-danger-50 text-danger-600',
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${colorClasses[color]} mr-3`}>
              <Icon className="h-6 w-6" />
            </div>
        
            <div>
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              {description && (
                <p className="text-sm text-gray-500 mt-1">{description}</p>
              )}
            </div>
          </div>
        </div>
        {change !== undefined && (
          <div className={`text-right ${change >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            <div className="text-sm font-medium">
              {change >= 0 ? '+' : ''}{change}%
            </div>
            <div className="text-xs text-gray-500">vs last run</div>
          </div>
        )}
      </div>
    </div>
  )
}

const SinglePredictionForm = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    meter_id: '',
    days: 30,
    include_features: true
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Meter ID
        </label>
        
        <input
          type="text"
          name="meter_id"
          value={formData.meter_id}
          onChange={handleChange}
          placeholder="Enter meter ID (e.g., M001234)"
          className="input"
          required
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Analysis Period (Days)
        </label>
        <select
          name="days"
          value={formData.days}
          onChange={handleChange}
          className="input"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>
      
      <div className="flex items-center">
        <input
          type="checkbox"
          name="include_features"
          id="include_features"
          checked={formData.include_features}
          onChange={handleChange}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <label htmlFor="include_features" className="ml-2 text-sm text-gray-700">
          Include feature analysis and explanation
        </label>
      </div>
      
      <button
        type="submit"
        disabled={isLoading}
        className="w-full btn-primary disabled:opacity-50"
      >
        {isLoading ? (
          <>
            <RefreshCwIcon className="h-4 w-4 mr-2 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <PlayIcon className="h-4 w-4 mr-2" />
            Run Prediction
          </>
        )}
      </button>
    </form>
  )
}

const BatchPredictionForm = ({ onSubmit, isLoading }) => {
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (file) {
      onSubmit(file)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload Meter List (CSV)
        </label>
       
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center ${
            dragActive 
              ? 'border-primary-400 bg-primary-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {file ? (
            <div className="flex items-center justify-center">
              <div className="text-center">
                <CheckCircleIcon className="h-8 w-8 text-success-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-900">{file.name}</p>
                <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  className="text-sm text-danger-600 hover:text-danger-800 mt-2"
                >
                  Remove file
                </button>
              </div>
            </div>
          ) : (
            <div>
              <UploadIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600">
                Drag and drop your CSV file here, or{' '}
                <label className="text-primary-600 hover:text-primary-700 cursor-pointer">
                  browse
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
              </p>
              <p className="text-xs text-gray-500 mt-1">
                CSV should contain meter_id column
              </p>
            </div>
          )}
        </div>
      </div>
      
      <button
        type="submit"
        disabled={!file || isLoading}
        className="w-full btn-primary disabled:opacity-50"
      >
        {isLoading ? (
          <>
            <RefreshCwIcon className="h-4 w-4 mr-2 animate-spin" />
            Processing Batch...
          </>
        ) : (
          <>
            <PlayIcon className="h-4 w-4 mr-2" />
            Run Batch Prediction
          </>
        )}
      </button>
    </form>
  )
}

const PredictionResult = ({ result, onClose }) => {
  if (!result) return null

  const riskColor = result.risk_level === 'HIGH' || result.risk_level === 'CRITICAL' 
    ? 'danger' : result.risk_level === 'MEDIUM' ? 'warning' : 'success'

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Prediction Result</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <XCircleIcon className="h-5 w-5" />
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <TrendingUpIcon className={`h-8 w-8 mx-auto mb-2 ${
            riskColor === 'danger' ? 'text-danger-600' : 
            riskColor === 'warning' ? 'text-warning-600' : 'text-success-600'
          }`} />
          <div className="text-2xl font-bold text-gray-900">
            {(result.risk_score * 100).toFixed(1)}%
          </div>
        
          <div className="text-sm text-gray-600">Risk Score</div>
        </div>
        
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
            apiUtils.getRiskLevelColor(result.risk_level)
          }`}>
            {result.risk_level}
          </span>
          <div className="text-sm text-gray-600 mt-2">Risk Level</div>
        </div>
        
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">
            {(result.confidence * 100).toFixed(1)}%
          </div>
         
          <div className="text-sm text-gray-600">Confidence</div>
        </div>
      </div>
      
      {result.features && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-3">Key Features</h4>
          <div className="space-y-2">
            {Object.entries(result.features).slice(0, 5).map(([feature, value]) => (
              <div key={feature} className="flex justify-between text-sm">
                <span className="text-gray-600">{feature.replace(/_/g, ' ')}</span>
                <span className="font-medium text-gray-900">
                  {typeof value === 'number' ? value.toFixed(3) : value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {result.risk_score > 0.7 && (
        <div className="mt-4 p-4 bg-warning-50 border border-warning-200 rounded-lg">
          <div className="flex">
            <AlertTriangleIcon className="h-5 w-5 text-warning-600 mt-0.5 mr-2" />
            <div>
              <h4 className="text-sm font-medium text-warning-800">High Risk Detected</h4>
              <p className="text-sm text-warning-700 mt-1">
                This meter shows strong indicators of potential electricity theft. 
                Consider creating an alert for investigation.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const Predictions = () => {
  const [activeTab, setActiveTab] = useState('single')
  const [predictionResult, setPredictionResult] = useState(null)

  // Mock data for charts
  const riskTrendData = [
    { date: '2024-01-01', high_risk: 12, medium_risk: 25, low_risk: 48 },
    { date: '2024-01-02', high_risk: 15, medium_risk: 28, low_risk: 45 },
    { date: '2024-01-03', high_risk: 18, medium_risk: 22, low_risk: 52 },
    { date: '2024-01-04', high_risk: 14, medium_risk: 30, low_risk: 41 },
    { date: '2024-01-05', high_risk: 16, medium_risk: 26, low_risk: 49 },
    { date: '2024-01-06', high_risk: 13, medium_risk: 31, low_risk: 46 },
    { date: '2024-01-07', high_risk: 19, medium_risk: 24, low_risk: 47 }
  ]

  const accuracyData = [
    { name: 'Precision', value: 91.8, fill: '#3b82f6' },
    { name: 'Recall', value: 88.3, fill: '#10b981' },
    { name: 'F1-Score', value: 90.0, fill: '#f59e0b' }
  ]

  const riskDistribution = [
    { name: 'Low Risk', value: 65, color: '#10b981' },
    { name: 'Medium Risk', value: 25, color: '#f59e0b' },
    { name: 'High Risk', value: 8, color: '#ef4444' },
    { name: 'Critical Risk', value: 2, color: '#dc2626' }
  ]

  // Mutations for predictions
  const singlePredictionMutation = useMutation(
    (data) => apiService.predictions.predictSingle(data),
    {
      onSuccess: (response) => {
        setPredictionResult(response.data)
        toast.success('Prediction completed successfully')
      },
      onError: (error) => {
        toast.error(`Prediction failed: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const batchPredictionMutation = useMutation(
    (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return apiService.predictions.predictBatch(formData)
    },
    {
      onSuccess: (response) => {
        toast.success(`Batch prediction started. Job ID: ${response.data.job_id}`)
        // In a real app, you'd poll for job status or show a progress screen
      },
      onError: (error) => {
        toast.error(`Batch prediction failed: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const handleSinglePrediction = (data) => {
    singlePredictionMutation.mutate(data)
  }

  const handleBatchPrediction = (file) => {
    batchPredictionMutation.mutate(file)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Theft Predictions</h1>
          <p className="text-gray-600 mt-1">
            Run ML predictions to detect potential electricity theft
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Model Status</p>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-success-500 rounded-full mr-2" />
              <p className="text-sm font-medium text-gray-900">FA-XGBoost v2.1 Ready</p>
            </div>
          </div>
        </div>
      </div>

      {/* Model Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <PredictionCard
          title="Model Accuracy"
          value="94.2%"
          change={1.3}
          icon={BarChart3Icon}
          color="success"
          description="Overall prediction accuracy"
        />
        <PredictionCard
          title="Precision"
          value="91.8%"
          change={0.8}
          icon={TrendingUpIcon}
          color="primary"
          description="True positive rate"
        />
        <PredictionCard
          title="Recall"
          value="88.3%"
          change={-0.5}
          icon={ZapIcon}
          color="warning"
          description="Detection sensitivity"
        />
        <PredictionCard
          title="F1-Score"
          value="90.0%"
          change={0.6}
          icon={CheckCircleIcon}
          color="success"
          description="Balanced performance"
        />
      </div>

      {/* Prediction Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Prediction Forms */}
        <div className="card p-6">
          <div className="flex space-x-4 mb-6">
            <button
              onClick={() => setActiveTab('single')}
              className={`px-4 py-2 text-sm font-medium rounded-md ${
                activeTab === 'single'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Single Prediction
            </button>
            <button
              onClick={() => setActiveTab('batch')}
              className={`px-4 py-2 text-sm font-medium rounded-md ${
                activeTab === 'batch'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Batch Prediction
            </button>
          </div>

          {activeTab === 'single' ? (
            <SinglePredictionForm
              onSubmit={handleSinglePrediction}
              isLoading={singlePredictionMutation.isLoading}
            />
          ) : (
            <BatchPredictionForm
              onSubmit={handleBatchPrediction}
              isLoading={batchPredictionMutation.isLoading}
            />
          )}
        </div>

        {/* Model Performance Chart */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Model Performance</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={accuracyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" stroke="#6b7280" />
              <YAxis stroke="#6b7280" domain={[0, 100]} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
                formatter={(value) => [`${value}%`, 'Score']}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Prediction Result */}
      {predictionResult && (
        <PredictionResult 
          result={predictionResult} 
          onClose={() => setPredictionResult(null)}
        />
      )}

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Trend Analysis */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Risk Trend Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={riskTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="high_risk" 
                stroke="#ef4444" 
                strokeWidth={2}
                name="High Risk"
              />
              <Line 
                type="monotone" 
                dataKey="medium_risk" 
                stroke="#f59e0b" 
                strokeWidth={2}
                name="Medium Risk"
              />
              <Line 
                type="monotone" 
                dataKey="low_risk" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Low Risk"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Distribution */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskDistribution}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
              >
                {riskDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
                formatter={(value) => [`${value}%`, 'Percentage']}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <RefreshCwIcon className="h-6 w-6 text-primary-600 mr-3" />
            <div className="text-left">
              <div className="font-medium text-gray-900">Retrain Model</div>
              <div className="text-sm text-gray-500">Update with latest data</div>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <DownloadIcon className="h-6 w-6 text-success-600 mr-3" />
            <div className="text-left">
              <div className="font-medium text-gray-900">Export Results</div>
              <div className="text-sm text-gray-500">Download prediction data</div>
            </div>
          </button>
          
          <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <EyeIcon className="h-6 w-6 text-warning-600 mr-3" />
            <div className="text-left">
              <div className="font-medium text-gray-900">View History</div>
              <div className="text-sm text-gray-500">Past prediction runs</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Predictions