import axios from 'axios'
import toast from 'react-hot-toast'

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth tokens, etc.
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle common error scenarios
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          toast.error('Authentication required')
          // Redirect to login if needed
          break
        case 403:
          toast.error('Access denied')
          break
        case 404:
          toast.error('Resource not found')
          break
        case 429:
          toast.error('Too many requests. Please wait a moment.')
          break
        case 500:
          toast.error('Server error. Please try again later.')
          break
        default:
          toast.error(data?.message || 'An error occurred')
      }
    } else if (error.request) {
      toast.error('Network error. Check your connection.')
    } else {
      toast.error('Request failed')
    }
    
    return Promise.reject(error)
  }
)

// API service methods
export const apiService = {
  // Health and system endpoints
  health: () => api.get('/health'),
  systemInfo: () => api.get('/info'),
  systemStats: () => api.get('/stats'),

  // Data ingestion endpoints
  data: {
    registerMeter: (meterData) => api.post('/data/meters/register', meterData),
    uploadSingleConsumption: (consumptionData) => api.post('/data/consumption/single', consumptionData),
    uploadBulkConsumption: (bulkData) => api.post('/data/consumption/bulk', bulkData),
    uploadBatchConsumption: (batchData) => api.post('/data/consumption/batch', batchData),
    getMeterConsumption: (meterId, params = {}) => api.get(`/data/meters/${meterId}/consumption`, { params }),
    getMeters: (params = {}) => api.get('/data/meters', { params }),
  },

  // Prediction endpoints
  predictions: {
    predictSingle: (predictionRequest) => api.post('/predict/single', predictionRequest),
    predictBatch: (batchRequest) => api.post('/predict/batch', batchRequest),
    getPredictionStatus: (meterId) => api.get(`/predict/status/${meterId}`),
  },

  // Alert management endpoints
  alerts: {
    getAlerts: (params = {}) => api.get('/alerts/', { params }),
    getAlert: (alertId) => api.get(`/alerts/${alertId}`),
    updateAlert: (alertId, updateData) => api.put(`/alerts/${alertId}`, updateData),
    confirmAlert: (alertId, notes = null) => api.post(`/alerts/${alertId}/confirm`, { notes }),
    rejectAlert: (alertId, notes = null) => api.post(`/alerts/${alertId}/reject`, { notes }),
    deleteAlert: (alertId) => api.delete(`/alerts/${alertId}`),
    getDashboardSummary: (params = {}) => api.get('/alerts/dashboard/summary', { params }),
  },

  // Explanation endpoints
  explanations: {
    explainPrediction: (explanationRequest) => api.post('/explain/prediction', explanationRequest),
    getGlobalImportance: (params = {}) => api.get('/explain/global-importance', { params }),
    explainAlert: (alertId, params = {}) => api.get(`/explain/alert/${alertId}`, { params }),
    compareMeter: (meterId, params = {}) => api.get(`/explain/compare/${meterId}`, { params }),
  },
}

// Utility functions for common operations
export const apiUtils = {
  // Format error message from API response
  formatError: (error) => {
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.message) {
      return error.message
    }
    return 'An unexpected error occurred'
  },

  // Check if response is successful
  isSuccess: (response) => {
    return response?.data?.status === 'success'
  },

  // Extract data from API response
  extractData: (response) => {
    return response?.data?.data || response?.data
  },

  // Format date for API requests
  formatDate: (date) => {
    if (!date) return null
    const d = new Date(date)
    return d.toISOString().split('T')[0]
  },

  // Parse date from API response
  parseDate: (dateString) => {
    if (!dateString) return null
    return new Date(dateString)
  },

  // Format currency (BDT)
  formatCurrency: (amount) => {
    if (amount == null) return 'N/A'
    return new Intl.NumberFormat('en-BD', {
      style: 'currency',
      currency: 'BDT',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  },

  // Format percentage
  formatPercentage: (value, decimals = 1) => {
    if (value == null) return 'N/A'
    return `${(value * 100).toFixed(decimals)}%`
  },

  // Format large numbers
  formatNumber: (value) => {
    if (value == null) return 'N/A'
    return new Intl.NumberFormat('en-US').format(value)
  },

  // Get risk level color class
  getRiskLevelColor: (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case 'CRITICAL':
        return 'text-danger-600 bg-danger-100'
      case 'HIGH':
        return 'text-danger-500 bg-danger-50'
      case 'MEDIUM':
        return 'text-warning-600 bg-warning-100'
      case 'LOW':
        return 'text-success-600 bg-success-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  },

  // Get alert status color class
  getAlertStatusColor: (status) => {
    switch (status?.toLowerCase()) {
      case 'confirmed':
        return 'text-danger-600 bg-danger-100'
      case 'rejected':
        return 'text-gray-600 bg-gray-100'
      case 'pending':
        return 'text-warning-600 bg-warning-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  },

  // Debounce function for search inputs
  debounce: (func, wait) => {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  },

  // Download file from blob
  downloadFile: (blob, filename) => {
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  },
}

export default api