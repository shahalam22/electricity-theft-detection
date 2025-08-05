import React, { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { Link } from 'react-router-dom'
import {
  AlertTriangleIcon,
  EyeIcon,
  CheckIcon,
  XIcon,
  FilterIcon,
  SearchIcon,
  DownloadIcon,
  MapPinIcon,
  CalendarIcon,
  ClockIcon,
  TrendingUpIcon,
  AlertCircleIcon
} from 'lucide-react'
import { apiService, apiUtils } from '../utils/api'
import toast from 'react-hot-toast'

const AlertStatusBadge = ({ status }) => {
  const colorClass = apiUtils.getAlertStatusColor(status)
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {status === 'pending' && <ClockIcon className="w-3 h-3 mr-1" />}
      {status === 'confirmed' && <CheckIcon className="w-3 h-3 mr-1" />}
      {status === 'rejected' && <XIcon className="w-3 h-3 mr-1" />}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

const RiskLevelBadge = ({ riskLevel }) => {
  const colorClass = apiUtils.getRiskLevelColor(riskLevel)
  
  const icons = {
    'LOW': ClockIcon,
    'MEDIUM': AlertCircleIcon,
    'HIGH': AlertTriangleIcon,
    'CRITICAL': TrendingUpIcon
  }
  
  const Icon = icons[riskLevel?.toUpperCase()] || AlertCircleIcon
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      <Icon className="w-3 h-3 mr-1" />
      {riskLevel}
    </span>
  )
}

const AlertRow = ({ alert, onConfirm, onReject, isProcessing }) => {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <AlertTriangleIcon className="h-8 w-8 text-warning-500" />
          </div>
          <div className="ml-4">
            <div className="text-sm font-medium text-gray-900">
              Meter {alert.meter_id}
            </div>
            <div className="text-sm text-gray-500">
              ID: {alert.id}
            </div>
          </div>
        </div>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap">
        <RiskLevelBadge riskLevel={alert.risk_level} />
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        <div className="font-medium">{(alert.risk_score * 100).toFixed(1)}%</div>
        <div className="text-gray-500">Confidence: {(alert.confidence * 100).toFixed(1)}%</div>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap">
        <AlertStatusBadge status={alert.status} />
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        <div className="flex items-center">
          <MapPinIcon className="h-4 w-4 text-gray-400 mr-1" />
          {alert.location || 'Unknown'}
        </div>
        <div className="text-gray-500 mt-1">
          Area: {alert.area || 'N/A'}
        </div>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        <div className="flex items-center">
          <CalendarIcon className="h-4 w-4 mr-1" />
          {apiUtils.parseDate(alert.created_at)?.toLocaleDateString()}
        </div>
        <div className="mt-1">
          {apiUtils.parseDate(alert.created_at)?.toLocaleTimeString()}
        </div>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {apiUtils.formatCurrency(alert.estimated_loss)}
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex items-center space-x-2">
          <Link
            to={`/alerts/${alert.id}`}
            className="text-primary-600 hover:text-primary-900"
          >
            <EyeIcon className="h-4 w-4" />
          </Link>
          
          {alert.status === 'pending' && (
            <>
              <button
                onClick={() => onConfirm(alert.id)}
                disabled={isProcessing}
                className="text-success-600 hover:text-success-900 disabled:opacity-50"
                title="Confirm Alert"
              >
                <CheckIcon className="h-4 w-4" />
              </button>
              
              <button
                onClick={() => onReject(alert.id)}
                disabled={isProcessing}
                className="text-danger-600 hover:text-danger-900 disabled:opacity-50"
                title="Reject Alert"
              >
                <XIcon className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  )
}

const FilterPanel = ({ filters, onFiltersChange, onClose }) => {
  const handleFilterChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <XIcon className="h-5 w-5" />
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={filters.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="input"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Risk Level
          </label>
          <select
            value={filters.risk_level || ''}
            onChange={(e) => handleFilterChange('risk_level', e.target.value)}
            className="input"
          >
            <option value="">All Risk Levels</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date Range (Days)
          </label>
          <select
            value={filters.days || ''}
            onChange={(e) => handleFilterChange('days', e.target.value)}
            className="input"
          >
            <option value="">All Time</option>
            <option value="1">Last 24 Hours</option>
            <option value="7">Last Week</option>
            <option value="30">Last Month</option>
            <option value="90">Last 3 Months</option>
          </select>
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Location/Area
        </label>
        <input
          type="text"
          value={filters.location || ''}
          onChange={(e) => handleFilterChange('location', e.target.value)}
          placeholder="Enter location or area..."
          className="input"
        />
      </div>
      
      <div className="flex justify-end space-x-2">
        <button
          onClick={() => onFiltersChange({})}
          className="btn-secondary"
        >
          Clear All
        </button>
        <button
          onClick={onClose}
          className="btn-primary"
        >
          Apply Filters
        </button>
      </div>
    </div>
  )
}

const Alerts = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({})
  const [showFilters, setShowFilters] = useState(false)
  const [selectedAlerts, setSelectedAlerts] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 20

  const queryClient = useQueryClient()

  // Fetch alerts with filters
  const { data: alertsData, isLoading, error } = useQuery(
    ['alerts', filters, searchTerm, currentPage],
    () => apiService.alerts.getAlerts({
      ...filters,
      search: searchTerm,
      page: currentPage,
      limit: pageSize
    }),
    {
      refetchInterval: 30000,
      keepPreviousData: true
    }
  )

  // Mutations for alert actions
  const confirmMutation = useMutation(
    (alertId) => apiService.alerts.confirmAlert(alertId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('alerts')
        toast.success('Alert confirmed successfully')
      },
      onError: (error) => {
        toast.error(`Failed to confirm alert: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const rejectMutation = useMutation(
    (alertId) => apiService.alerts.rejectAlert(alertId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('alerts')
        toast.success('Alert rejected successfully')
      },
      onError: (error) => {
        toast.error(`Failed to reject alert: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const alerts = alertsData?.data?.alerts || []
  const totalAlerts = alertsData?.data?.total || 0
  const totalPages = Math.ceil(totalAlerts / pageSize)

  // Filtered alerts based on search term
  const filteredAlerts = useMemo(() => {
    if (!searchTerm) return alerts
    
    return alerts.filter(alert =>
      alert.meter_id.toString().includes(searchTerm) ||
      alert.location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alert.area?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alert.id.toString().includes(searchTerm)
    )
  }, [alerts, searchTerm])

  const handleConfirm = (alertId) => {
    confirmMutation.mutate(alertId)
  }

  const handleReject = (alertId) => {
    rejectMutation.mutate(alertId)
  }

  const handleExport = () => {
    // In a real implementation, this would trigger a download
    toast.success('Export functionality would be implemented here')
  }

  const isProcessing = confirmMutation.isLoading || rejectMutation.isLoading

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangleIcon className="h-12 w-12 text-danger-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Alerts</h3>
        <p className="text-gray-600">{apiUtils.formatError(error)}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alert Management</h1>
          <p className="text-gray-600 mt-1">
            Monitor and manage electricity theft alerts
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={handleExport}
            className="btn-secondary"
          >
            <DownloadIcon className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-warning-100 rounded-lg">
              <ClockIcon className="h-6 w-6 text-warning-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.status === 'pending').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-success-100 rounded-lg">
              <CheckIcon className="h-6 w-6 text-success-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Confirmed</p>
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.status === 'confirmed').length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-danger-100 rounded-lg">
              <AlertTriangleIcon className="h-6 w-6 text-danger-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Risk</p>
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => ['HIGH', 'CRITICAL'].includes(a.risk_level)).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-primary-100 rounded-lg">
              <TrendingUpIcon className="h-6 w-6 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total</p>
              <p className="text-2xl font-bold text-gray-900">{totalAlerts}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by meter ID, location, or alert ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary"
          >
            <FilterIcon className="h-4 w-4 mr-2" />
            Filters
          </button>
        </div>
        
        {showFilters && (
          <div className="mt-4">
            <FilterPanel
              filters={filters}
              onFiltersChange={setFilters}
              onClose={() => setShowFilters(false)}
            />
          </div>
        )}
      </div>

      {/* Alerts Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="loading-spinner" />
          </div>
        ) : filteredAlerts.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Alert
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Risk Level
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Risk Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Est. Loss
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAlerts.map((alert) => (
                    <AlertRow
                      key={alert.id}
                      alert={alert}
                      onConfirm={handleConfirm}
                      onReject={handleReject}
                      isProcessing={isProcessing}
                    />
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="btn-secondary disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="btn-secondary disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing <span className="font-medium">{((currentPage - 1) * pageSize) + 1}</span> to{' '}
                      <span className="font-medium">
                        {Math.min(currentPage * pageSize, totalAlerts)}
                      </span>{' '}
                      of <span className="font-medium">{totalAlerts}</span> results
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage === totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <AlertTriangleIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Alerts Found</h3>
            <p className="text-gray-600">
              {searchTerm || Object.keys(filters).length > 0
                ? 'Try adjusting your search or filters'
                : 'No alerts have been generated yet'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Alerts