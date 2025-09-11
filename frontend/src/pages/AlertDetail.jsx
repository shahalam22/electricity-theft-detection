import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import {
  ArrowLeftIcon,
  AlertTriangleIcon,
  MapPinIcon,
  CalendarIcon,
  TrendingUpIcon,
  ZapIcon,
  DollarSignIcon,
  CheckIcon,
  XIcon,
  EyeIcon,
  ClockIcon,
  UserIcon,
  FileTextIcon,
  BarChart3Icon
} from 'lucide-react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import { apiService, apiUtils } from '../utils/api'
import toast from 'react-hot-toast'

const AlertDetail = () => {
  const { alertId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [notes, setNotes] = useState('')
  const [showExplanation, setShowExplanation] = useState(false)

  // Fetch alert details
  const { data: alertData, isLoading: alertLoading, error } = useQuery(
    ['alert', alertId],
    () => apiService.alerts.getAlert(alertId),
    {
      enabled: !!alertId,
      refetchInterval: 30000
    }
  )

  // Fetch explanation data
  const { data: explanationData, isLoading: explanationLoading } = useQuery(
    ['explanation', alertId],
    () => apiService.explanations.explainAlert(alertId),
    {
      enabled: !!alertId && showExplanation,
    }
  )

  // Mutations for alert actions
  const confirmMutation = useMutation(
    ({ alertId, notes }) => apiService.alerts.confirmAlert(alertId, notes),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['alert', alertId])
        queryClient.invalidateQueries('alerts')
        toast.success('Alert confirmed successfully')
      },
      onError: (error) => {
        toast.error(`Failed to confirm alert: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const rejectMutation = useMutation(
    ({ alertId, notes }) => apiService.alerts.rejectAlert(alertId, notes),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['alert', alertId])
        queryClient.invalidateQueries('alerts')
        toast.success('Alert rejected successfully')
      },
      onError: (error) => {
        toast.error(`Failed to reject alert: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const alert = alertData?.data
  const explanation = explanationData?.data

  // Sample consumption data (would come from API)
  const consumptionData = [
    { date: '2024-01-01', consumption: 250, baseline: 280, anomaly: false },
    { date: '2024-01-02', consumption: 245, baseline: 275, anomaly: false },
    { date: '2024-01-03', consumption: 180, baseline: 270, anomaly: true },
    { date: '2024-01-04', consumption: 160, baseline: 268, anomaly: true },
    { date: '2024-01-05', consumption: 150, baseline: 265, anomaly: true },
    { date: '2024-01-06', consumption: 145, baseline: 263, anomaly: true },
    { date: '2024-01-07', consumption: 155, baseline: 260, anomaly: true },
  ]

  const featureImportance = [
    { feature: 'Consumption Variance', importance: 0.35, value: 'High' },
    { feature: 'Peak Hour Usage', importance: 0.28, value: 'Abnormal' },
    { feature: 'Monthly Trend', importance: 0.22, value: 'Declining' },
    { feature: 'Weekend Pattern', importance: 0.15, value: 'Irregular' }
  ]

  const handleConfirm = () => {
    confirmMutation.mutate({ alertId, notes })
  }

  const handleReject = () => {
    rejectMutation.mutate({ alertId, notes })
  }

  const isProcessing = confirmMutation.isLoading || rejectMutation.isLoading

  if (alertLoading) 
  {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner" />
      </div>
    )
  }

  if (error || !alert) {
    return (
      <div className="text-center py-12">
        <AlertTriangleIcon className="h-12 w-12 text-danger-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Alert Not Found</h3>
        <p className="text-gray-600 mb-4">
          {error ? apiUtils.formatError(error) : 'The requested alert could not be found.'}
        </p>
        <button onClick={() => navigate('/alerts')} className="btn-primary">
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Alerts
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/alerts')}
            className="btn-secondary"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back to Alerts
          </button>
          
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Alert #{alert.id}
            </h1>
            <p className="text-gray-600 mt-1">
              Meter {alert.meter_id} • Created {apiUtils.parseDate(alert.created_at)?.toLocaleString()}
            </p>
          </div>
        </div>
        
        {alert.status === 'pending' && (
          <div className="flex items-center space-x-3">
            <button
              onClick={handleReject}
              disabled={isProcessing}
              className="btn-secondary disabled:opacity-50"
            >
              <XIcon className="h-4 w-4 mr-2" />
              Reject
            </button>
          
            <button
              onClick={handleConfirm}
              disabled={isProcessing}
              className="btn-danger disabled:opacity-50"
            >
              <CheckIcon className="h-4 w-4 mr-2" />
              Confirm Theft
            </button>
          </div>
        )}
      </div>

      {/* Alert Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Alert Info */}
        <div className="lg:col-span-2 card p-6">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-danger-100 rounded-lg">
                <AlertTriangleIcon className="h-8 w-8 text-danger-600" />
              </div>
          
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Electricity Theft Detection
                </h2>
                <div className="flex items-center space-x-4 mt-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    apiUtils.getRiskLevelColor(alert.risk_level)
                  }`}>
                    {alert.risk_level} Risk
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    apiUtils.getAlertStatusColor(alert.status)
                  }`}>
                    {alert.status.charAt(0).toUpperCase() + alert.status.slice(1)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <TrendingUpIcon className="h-6 w-6 text-danger-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-900">
                {(alert.risk_score * 100).toFixed(1)}%
              </div>
          
              <div className="text-sm text-gray-600">Risk Score</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <BarChart3Icon className="h-6 w-6 text-primary-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-gray-900">
                {(alert.confidence * 100).toFixed(1)}%
              </div>
          
              <div className="text-sm text-gray-600">Confidence</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <DollarSignIcon className="h-6 w-6 text-warning-600 mx-auto mb-2" />
            
              <div className="text-2xl font-bold text-gray-900">
                {apiUtils.formatCurrency(alert.estimated_loss)}
              </div>
            
              <div className="text-sm text-gray-600">Est. Loss</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <ZapIcon className="h-6 w-6 text-success-600 mx-auto mb-2" />
            
              <div className="text-2xl font-bold text-gray-900">
                {alert.consumption_reduction}%
              </div>
              <div className="text-sm text-gray-600">Reduction</div>
            </div>
          </div>

          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Detection Details</h3>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-600">Detection Method</dt>
                <dd className="text-sm text-gray-900 mt-1">FA-XGBoost Algorithm</dd>
              </div>
            
              <div>
                <dt className="text-sm font-medium text-gray-600">Model Version</dt>
                <dd className="text-sm text-gray-900 mt-1">v2.1.0</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-600">Detection Date</dt>
                <dd className="text-sm text-gray-900 mt-1">
                  {apiUtils.parseDate(alert.created_at)?.toLocaleDateString()}
                </dd>
              </div>
            
              <div>
                <dt className="text-sm font-medium text-gray-600">Analysis Period</dt>
                <dd className="text-sm text-gray-900 mt-1">Last 30 days</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Location & Meter Info */}
        <div className="space-y-6">
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              <MapPinIcon className="h-5 w-5 inline mr-2" />
              Location Details
            </h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-600">Address</dt>
                <dd className="text-sm text-gray-900 mt-1">{alert.location || 'Not specified'}</dd>
              </div>
            
              <div>
                <dt className="text-sm font-medium text-gray-600">Area</dt>
                <dd className="text-sm text-gray-900 mt-1">{alert.area || 'Not specified'}</dd>
              </div>
            
              <div>
                <dt className="text-sm font-medium text-gray-600">Zone</dt>
                <dd className="text-sm text-gray-900 mt-1">{alert.zone || 'Not specified'}</dd>
              </div>
            
              <div>
                <dt className="text-sm font-medium text-gray-600">Customer Type</dt>
                <dd className="text-sm text-gray-900 mt-1">{alert.customer_type || 'Residential'}</dd>
              </div>
            </dl>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              <ZapIcon className="h-5 w-5 inline mr-2" />
              Meter Information
            </h3>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-600">Meter ID</dt>
                <dd className="text-sm text-gray-900 mt-1 font-mono">{alert.meter_id}</dd>
              </div>
             
              <div>
                <dt className="text-sm font-medium text-gray-600">Installation Date</dt>
                <dd className="text-sm text-gray-900 mt-1">2023-03-15</dd>
              </div>
             
              <div>
                <dt className="text-sm font-medium text-gray-600">Last Reading</dt>
                <dd className="text-sm text-gray-900 mt-1">2024-06-01 09:30</dd>
              </div>
             
              <div>
                <dt className="text-sm font-medium text-gray-600">Connection Type</dt>
                <dd className="text-sm text-gray-900 mt-1">Single Phase</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {/* Consumption Analysis */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">Consumption Analysis</h3>
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="btn-secondary"
          >
            <EyeIcon className="h-4 w-4 mr-2" />
            {showExplanation ? 'Hide' : 'Show'} AI Explanation
          </button>
        </div>
        
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={consumptionData}>
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
            <Line 
              type="monotone" 
              dataKey="baseline" 
              stroke="#6b7280" 
              strokeDasharray="5 5"
              name="Baseline"
            />
            <Line 
              type="monotone" 
              dataKey="consumption" 
              stroke="#ef4444" 
              strokeWidth={2}
              name="Actual Consumption"
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* AI Explanation */}
      {showExplanation && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">AI Model Explanation</h3>
          
          {explanationLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="loading-spinner" />
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Feature Importance</h4>
                <div className="space-y-3">
                  {featureImportance.map((feature, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-32 text-sm text-gray-600">{feature.feature}</div>
                      <div className="flex-1 mx-4">
                        <div className="bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full"
                            style={{ width: `${feature.importance * 100}%` }}
                          />
                        </div>
                      </div>
             
                      <div className="w-20 text-sm text-gray-900 text-right">
                        {(feature.importance * 100).toFixed(1)}%
                      </div>
                      <div className="w-24 text-sm text-gray-600 text-right">
                        {feature.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="border-t pt-6">
                <h4 className="text-md font-medium text-gray-900 mb-3">Key Findings</h4>
                <ul className="list-disc list-inside space-y-2 text-sm text-gray-700">
                  <li>Consumption shows significant reduction (45%) compared to historical patterns</li>
                  <li>Peak hour usage patterns are inconsistent with typical residential behavior</li>
                  <li>Monthly consumption trend shows gradual decline over the past 3 months</li>
                  <li>Weekend consumption patterns are irregular compared to weekdays</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Section */}
      {alert.status === 'pending' && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Take Action</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Investigation Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                placeholder="Add notes about your investigation, field inspection results, or other relevant information..."
              />
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={handleConfirm}
                disabled={isProcessing}
                className="btn-danger disabled:opacity-50"
              >
                <CheckIcon className="h-4 w-4 mr-2" />
                {isProcessing ? 'Processing...' : 'Confirm Theft'}
              </button>
              
              <button
                onClick={handleReject}
                disabled={isProcessing}
                className="btn-secondary disabled:opacity-50"
              >
                <XIcon className="h-4 w-4 mr-2" />
                {isProcessing ? 'Processing...' : 'Mark as False Positive'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Status History */}
      {(alert.status !== 'pending' || alert.investigation_notes) && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            <ClockIcon className="h-5 w-5 inline mr-2" />
            Investigation History
          </h3>
          
          <div className="flow-root">
            <ul className="-mb-8">
              <li>
                <div className="relative pb-8">
                  <div className="relative flex space-x-3">
                    <div>
                      <span className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center ring-8 ring-white">
                        <AlertTriangleIcon className="h-4 w-4 text-white" />
                      </span>
                    </div>
             
                    <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                      <div>
                        <p className="text-sm text-gray-500">
                          Alert created by FA-XGBoost model
                        </p>
                      </div>
              
                      <div className="text-right text-sm whitespace-nowrap text-gray-500">
                        {apiUtils.parseDate(alert.created_at)?.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              </li>
              
              {alert.status !== 'pending' && (
                <li>
                  <div className="relative pb-8">
                    <div className="relative flex space-x-3">
                      <div>
                        <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${
                          alert.status === 'confirmed' ? 'bg-danger-500' : 'bg-gray-500'
                        }`}>
                          <UserIcon className="h-4 w-4 text-white" />
                        </span>
                      </div>
              
                      <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                        <div>
                          <p className="text-sm text-gray-500">
                            Alert {alert.status} by utility staff
                          </p>
                          {alert.investigation_notes && (
                            <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                              <p className="text-sm text-gray-700">{alert.investigation_notes}</p>
                            </div>
                          )}
                        </div>
              
                        <div className="text-right text-sm whitespace-nowrap text-gray-500">
                          {apiUtils.parseDate(alert.updated_at)?.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              )}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

export default AlertDetail