import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import {
  UploadIcon,
  DatabaseIcon,
  ZapIcon,
  CheckCircleIcon,
  XCircleIcon,
  AlertTriangleIcon,
  DownloadIcon,
  RefreshCwIcon,
  PlusIcon,
  EyeIcon,
  TrashIcon,
  SearchIcon,
  CalendarIcon,
  BarChart3Icon
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import { apiService, apiUtils } from '../utils/api'
import toast from 'react-hot-toast'

const UploadCard = ({ title, description, icon: Icon, color, onUpload, isLoading, accept, multiple = false }) => {
  const [dragActive, setDragActive] = useState(false)

  const colorClasses = {
    primary: 'border-primary-300 bg-primary-50 text-primary-600',
    success: 'border-success-300 bg-success-50 text-success-600',
    warning: 'border-warning-300 bg-warning-50 text-warning-600',
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
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(multiple ? Array.from(e.dataTransfer.files) : e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(multiple ? Array.from(e.target.files) : e.target.files[0])
    }
  }

  return (
    <div className="card p-6">
      <div className="flex items-center mb-4">
        <Icon className={`h-6 w-6 mr-3 ${colorClasses[color].split(' ')[2]}`} />
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
      </div>
      
      <p className="text-sm text-gray-600 mb-4">{description}</p>
      
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive 
            ? colorClasses[color]
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <UploadIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-sm text-gray-600 mb-2">
          Drag and drop your files here, or{' '}
          <label className="text-primary-600 hover:text-primary-700 cursor-pointer">
            browse
            <input
              type="file"
              accept={accept}
              multiple={multiple}
              onChange={handleFileChange}
              className="hidden"
              disabled={isLoading}
            />
          </label>
        </p>
        <p className="text-xs text-gray-500">
          {accept === '.csv' ? 'CSV files only' : 'Excel or CSV files'}
        </p>
        
        {isLoading && (
          <div className="mt-4">
            <RefreshCwIcon className="h-6 w-6 text-primary-600 mx-auto animate-spin" />
            <p className="text-sm text-gray-600 mt-2">Uploading...</p>
          </div>
        )}
      </div>
    </div>
  )
}

const MeterRegistrationForm = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    meter_id: '',
    customer_name: '',
    location: '',
    area: '',
    zone: '',
    customer_type: 'residential',
    connection_type: 'single_phase',
    installation_date: '',
    tariff_type: 'domestic'
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleReset = () => {
    setFormData({
      meter_id: '',
      customer_name: '',
      location: '',
      area: '',
      zone: '',
      customer_type: 'residential',
      connection_type: 'single_phase',
      installation_date: '',
      tariff_type: 'domestic'
    })
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Register New Meter</h3>
        <button
          type="button"
          onClick={handleReset}
          className="btn-secondary text-sm"
        >
          Reset Form
        </button>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Meter ID *
            </label>
            <input
              type="text"
              name="meter_id"
              value={formData.meter_id}
              onChange={handleChange}
              placeholder="e.g., M001234"
              className="input"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Customer Name *
            </label>
            <input
              type="text"
              name="customer_name"
              value={formData.customer_name}
              onChange={handleChange}
              placeholder="Enter customer name"
              className="input"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location *
            </label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="Full address"
              className="input"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Area
            </label>
            <input
              type="text"
              name="area"
              value={formData.area}
              onChange={handleChange}
              placeholder="Area/District"
              className="input"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Zone
            </label>
            <input
              type="text"
              name="zone"
              value={formData.zone}
              onChange={handleChange}
              placeholder="Distribution zone"
              className="input"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Customer Type
            </label>
            <select
              name="customer_type"
              value={formData.customer_type}
              onChange={handleChange}
              className="input"
            >
              <option value="residential">Residential</option>
              <option value="commercial">Commercial</option>
              <option value="industrial">Industrial</option>
              <option value="agricultural">Agricultural</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Connection Type
            </label>
            <select
              name="connection_type"
              value={formData.connection_type}
              onChange={handleChange}
              className="input"
            >
              <option value="single_phase">Single Phase</option>
              <option value="three_phase">Three Phase</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Installation Date
            </label>
            <input
              type="date"
              name="installation_date"
              value={formData.installation_date}
              onChange={handleChange}
              className="input"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tariff Type
            </label>
            <select
              name="tariff_type"
              value={formData.tariff_type}
              onChange={handleChange}
              className="input"
            >
              <option value="domestic">Domestic</option>
              <option value="commercial">Commercial</option>
              <option value="industrial">Industrial</option>
              <option value="agricultural">Agricultural</option>
            </select>
          </div>
       
        </div>
        
        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={handleReset}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <RefreshCwIcon className="h-4 w-4 mr-2 animate-spin" />
                Registering...
              </>
            ) : (
              <>
                <PlusIcon className="h-4 w-4 mr-2" />
                Register Meter
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

const MeterList = ({ meters, isLoading, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  const itemsPerPage = 10

  const filteredMeters = meters.filter(meter =>
    meter.meter_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    meter.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    meter.location?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const paginatedMeters = filteredMeters.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const totalPages = Math.ceil(filteredMeters.length / itemsPerPage)

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Registered Meters</h3>
        <button onClick={onRefresh} className="btn-secondary">
          <RefreshCwIcon className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>
      
      <div className="mb-4">
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search meters..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>
      
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="loading-spinner" />
        </div>
      ) : paginatedMeters.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Meter ID</th>
                <th>Customer</th>
                <th>Location</th>
                <th>Type</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedMeters.map((meter) => (
                <tr key={meter.meter_id}>
                  <td className="font-mono">{meter.meter_id}</td>
                  <td>{meter.customer_name || 'N/A'}</td>
                  <td>{meter.location || 'N/A'}</td>
                  <td>
                    <span className="badge-primary">
                      {meter.customer_type || 'residential'}
                    </span>
                  </td>
                  <td>
                    <span className="badge-success">Active</span>
                  </td>
                  <td>
                    <div className="flex items-center space-x-2">
                      <button className="text-primary-600 hover:text-primary-900">
                        <EyeIcon className="h-4 w-4" />
                      </button>
                      <button className="text-danger-600 hover:text-danger-900">
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-gray-700">
                Showing {((currentPage - 1) * itemsPerPage) + 1} to{' '}
                {Math.min(currentPage * itemsPerPage, filteredMeters.length)} of{' '}
                {filteredMeters.length} results
              </div>
             
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="btn-secondary disabled:opacity-50 text-sm"
                >
                  Previous
                </button>
              
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="btn-secondary disabled:opacity-50 text-sm"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <DatabaseIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No meters found</p>
        </div>
      )}
    </div>
  )
}

const DataIngestion = () => {
  const [activeTab, setActiveTab] = useState('upload')
  const queryClient = useQueryClient()

  // Fetch meters data
  const { data: metersData, isLoading: metersLoading } = useQuery(
    'meters',
    () => apiService.data.getMeters({ limit: 1000 }),
    {
      refetchInterval: 60000
    }
  )

  const meters = metersData?.data?.meters || []

  // Sample data for charts
  const uploadStatsData = [
    { date: '2024-01-01', uploads: 45, errors: 2 },
    { date: '2024-01-02', uploads: 52, errors: 1 },
    { date: '2024-01-03', uploads: 38, errors: 3 },
    { date: '2024-01-04', uploads: 61, errors: 0 },
    { date: '2024-01-05', uploads: 55, errors: 1 },
    { date: '2024-01-06', uploads: 47, errors: 2 },
    { date: '2024-01-07', uploads: 58, errors: 1 }
  ]

  // Mutations
  const meterRegistrationMutation = useMutation(
    (data) => apiService.data.registerMeter(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('meters')
        toast.success('Meter registered successfully')
      },
      onError: (error) => {
        toast.error(`Registration failed: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const bulkUploadMutation = useMutation(
    (data) => apiService.data.uploadBulkConsumption(data),
    {
      onSuccess: () => {
        toast.success('Bulk upload completed successfully')
      },
      onError: (error) => {
        toast.error(`Upload failed: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const batchUploadMutation = useMutation(
    (data) => apiService.data.uploadBatchConsumption(data),
    {
      onSuccess: () => {
        toast.success('Batch upload started successfully')
      },
      onError: (error) => {
        toast.error(`Upload failed: ${apiUtils.formatError(error)}`)
      }
    }
  )

  const handleMeterRegistration = (data) => {
    meterRegistrationMutation.mutate(data)
  }

  const handleBulkUpload = (file) => {
    const formData = new FormData()
    formData.append('file', file)
    bulkUploadMutation.mutate(formData)
  }

  const handleBatchUpload = (files) => {
    const formData = new FormData()
    files.forEach((file, index) => {
      formData.append('files', file)
    })
    batchUploadMutation.mutate(formData)
  }

  const handleMetersRefresh = () => {
    queryClient.invalidateQueries('meters')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Data Management</h1>
          <p className="text-gray-600 mt-1">
            Manage meter registrations and consumption data uploads
          </p>
        </div>
      
        <div className="flex items-center space-x-4">
          <button className="btn-secondary">
            <DownloadIcon className="h-4 w-4 mr-2" />
            Export Data
          </button>
         
          <button className="btn-secondary">
            <BarChart3Icon className="h-4 w-4 mr-2" />
            View Reports
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-2 bg-primary-100 rounded-lg">
              <ZapIcon className="h-6 w-6 text-primary-600" />
            </div>
         
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Meters</p>
              <p className="text-2xl font-bold text-gray-900">{apiUtils.formatNumber(meters.length)}</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-2 bg-success-100 rounded-lg">
              <UploadIcon className="h-6 w-6 text-success-600" />
            </div>
           
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Data Uploads</p>
              <p className="text-2xl font-bold text-gray-900">1,247</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-2 bg-warning-100 rounded-lg">
              <AlertTriangleIcon className="h-6 w-6 text-warning-600" />
            </div>
           
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Upload Errors</p>
              <p className="text-2xl font-bold text-gray-900">8</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="p-2 bg-danger-100 rounded-lg">
              <DatabaseIcon className="h-6 w-6 text-danger-600" />
            </div>
           
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Data Quality</p>
              <p className="text-2xl font-bold text-gray-900">98.5%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('upload')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'upload'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Data Upload
          </button>
        
          <button
            onClick={() => setActiveTab('register')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'register'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Meter Registration
          </button>
         
          <button
            onClick={() => setActiveTab('manage')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'manage'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Manage Meters
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'upload' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <UploadCard
              title="Consumption Data Upload"
              description="Upload daily/monthly consumption data in CSV format"
              icon={UploadIcon}
              color="primary"
              accept=".csv"
              onUpload={handleBulkUpload}
              isLoading={bulkUploadMutation.isLoading}
            />

            <UploadCard
              title="Batch File Upload"
              description="Upload multiple consumption files at once"
              icon={DatabaseIcon}
              color="success"
              accept=".csv,.xlsx"
              multiple={true}
              onUpload={handleBatchUpload}
              isLoading={batchUploadMutation.isLoading}
            />
          </div>

          {/* Upload Statistics */}
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Statistics</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={uploadStatsData}>
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
                <Bar dataKey="uploads" fill="#3b82f6" name="Successful Uploads" />
                <Bar dataKey="errors" fill="#ef4444" name="Upload Errors" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === 'register' && (
        <MeterRegistrationForm
          onSubmit={handleMeterRegistration}
          isLoading={meterRegistrationMutation.isLoading}
        />
      )}

      {activeTab === 'manage' && (
        <MeterList
          meters={meters}
          isLoading={metersLoading}
          onRefresh={handleMetersRefresh}
        />
      )}
    </div>
  )
}

export default DataIngestion