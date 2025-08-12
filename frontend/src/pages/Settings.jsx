import React, { useState } from 'react'
import { useQuery, useMutation } from 'react-query'
import {
  SettingsIcon,
  UserIcon,
  BellIcon,
  ShieldIcon,
  DatabaseIcon,
  ZapIcon,
  SaveIcon,
  RefreshCwIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  EyeIcon,
  EyeOffIcon,
  DownloadIcon,
  UploadIcon
} from 'lucide-react'
import { apiService, apiUtils } from '../utils/api'
import toast from 'react-hot-toast'

const SettingCard = ({ title, description, children }) => (
  <div className="card p-6">
    <div className="mb-4">
      <h3 className="text-lg font-medium text-gray-900">{title}</h3>
      {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
    </div>
    {children}
  </div>
)

const Settings = () => {
  const [activeTab, setActiveTab] = useState('general')
  const [showApiKey, setShowApiKey] = useState(false)

  // Settings state
  const [generalSettings, setGeneralSettings] = useState({
    system_name: 'TheftGuard System',
    company_name: 'Bangladesh Utility Company',
    timezone: 'Asia/Dhaka',
    language: 'en',
    date_format: 'DD/MM/YYYY',
    currency: 'BDT'
  })

  const [alertSettings, setAlertSettings] = useState({
    email_notifications: true,
    sms_notifications: false,
    high_risk_threshold: 0.8,
    medium_risk_threshold: 0.5,
    auto_alert_creation: true,
    alert_retention_days: 90
  })

  const [modelSettings, setModelSettings] = useState({
    model_version: '2.1.0',
    confidence_threshold: 0.7,
    auto_retrain: true,
    retrain_frequency: 'weekly',
    feature_selection: 'automatic',
    max_features: 50
  })

  const [securitySettings, setSecuritySettings] = useState({
    session_timeout: 30,
    password_policy: 'strong',
    two_factor_auth: false,
    api_rate_limit: 1000,
    login_attempts: 5,
    account_lockout_duration: 15
  })

  // Mock system info
  const systemInfo = {
    version: '1.0.0',
    database_size: '2.4 GB',
    total_records: '1,247,563',
    last_backup: '2024-01-07 02:00:00',
    uptime: '15 days, 6 hours',
    api_key: 'sk-1234567890abcdef...'
  }

  const tabs = [
    { id: 'general', name: 'General', icon: SettingsIcon },
    { id: 'alerts', name: 'Alerts', icon: BellIcon },
    { id: 'model', name: 'ML Model', icon: ZapIcon },
    { id: 'security', name: 'Security', icon: ShieldIcon },
    { id: 'system', name: 'System', icon: DatabaseIcon }
  ]

  const handleGeneralSave = () => {
    toast.success('General settings saved successfully')
  }

  const handleAlertSave = () => {
    toast.success('Alert settings saved successfully')
  }

  const handleModelSave = () => {
    toast.success('Model settings saved successfully')
  }

  const handleSecuritySave = () => {
    toast.success('Security settings saved successfully')
  }

  const handleBackup = () => {
    toast.success('Database backup initiated')
  }

  const handleRestore = () => {
    toast.loading('Restoring database... This may take a few minutes.')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Settings</h1>
          <p className="text-gray-600 mt-1">
            Configure system preferences and security settings
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">System Version</p>
            <p className="text-sm font-medium text-gray-900">v{systemInfo.version}</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {tab.name}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'general' && (
        <div className="space-y-6">
          <SettingCard
            title="General Configuration"
            description="Basic system settings and preferences"
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    System Name
                  </label>
                  <input
                    type="text"
                    value={generalSettings.system_name}
                    onChange={(e) => setGeneralSettings(prev => ({
                      ...prev, system_name: e.target.value
                    }))}
                    className="input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={generalSettings.company_name}
                    onChange={(e) => setGeneralSettings(prev => ({
                      ...prev, company_name: e.target.value
                    }))}
                    className="input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Timezone
                  </label>
                  <select
                    value={generalSettings.timezone}
                    onChange={(e) => setGeneralSettings(prev => ({
                      ...prev, timezone: e.target.value
                    }))}
                    className="input"
                  >
                    <option value="Asia/Dhaka">Asia/Dhaka (GMT+6)</option>
                    <option value="UTC">UTC (GMT+0)</option>
                    <option value="Asia/Kolkata">Asia/Kolkata (GMT+5:30)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date Format
                  </label>
                  <select
                    value={generalSettings.date_format}
                    onChange={(e) => setGeneralSettings(prev => ({
                      ...prev, date_format: e.target.value
                    }))}
                    className="input"
                  >
                    <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Currency
                  </label>
                  <select
                    value={generalSettings.currency}
                    onChange={(e) => setGeneralSettings(prev => ({
                      ...prev, currency: e.target.value
                    }))}
                    className="input"
                  >
                    <option value="BDT">BDT (৳)</option>
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Language
                  </label>
                  <select
                    value={generalSettings.language}
                    onChange={(e) => setGeneralSettings(prev => ({
                      ...prev, language: e.target.value
                    }))}
                    className="input"
                  >
                    <option value="en">English</option>
                    <option value="bn">বাংলা</option>
                  </select>
                </div>
              </div>
              
              <div className="flex justify-end">
                <button onClick={handleGeneralSave} className="btn-primary">
                  <SaveIcon className="h-4 w-4 mr-2" />
                  Save Changes
                </button>
              </div>
            </div>
          </SettingCard>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="space-y-6">
          <SettingCard
            title="Alert Configuration"
            description="Configure alert thresholds and notification settings"
          >
            <div className="space-y-6">
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Notification Preferences</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Email Notifications</label>
                      <p className="text-sm text-gray-500">Receive alert notifications via email</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={alertSettings.email_notifications}
                        onChange={(e) => setAlertSettings(prev => ({
                          ...prev, email_notifications: e.target.checked
                        }))}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-700">SMS Notifications</label>
                      <p className="text-sm text-gray-500">Receive critical alerts via SMS</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={alertSettings.sms_notifications}
                        onChange={(e) => setAlertSettings(prev => ({
                          ...prev, sms_notifications: e.target.checked
                        }))}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Risk Thresholds</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      High Risk Threshold
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.01"
                      value={alertSettings.high_risk_threshold}
                      onChange={(e) => setAlertSettings(prev => ({
                        ...prev, high_risk_threshold: parseFloat(e.target.value)
                      }))}
                      className="input"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Medium Risk Threshold
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.01"
                      value={alertSettings.medium_risk_threshold}
                      onChange={(e) => setAlertSettings(prev => ({
                        ...prev, medium_risk_threshold: parseFloat(e.target.value)
                      }))}
                      className="input"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Alert Retention (Days)
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={alertSettings.alert_retention_days}
                      onChange={(e) => setAlertSettings(prev => ({
                        ...prev, alert_retention_days: parseInt(e.target.value)
                      }))}
                      className="input"
                    />
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end">
                <button onClick={handleAlertSave} className="btn-primary">
                  <SaveIcon className="h-4 w-4 mr-2" />
                  Save Changes
                </button>
              </div>
            </div>
          </SettingCard>
        </div>
      )}

      {activeTab === 'model' && (
        <div className="space-y-6">
          <SettingCard
            title="ML Model Configuration"
            description="Configure machine learning model parameters and training settings"
          >
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Current Model Version
                  </label>
                  <input
                    type="text"
                    value={modelSettings.model_version}
                    disabled
                    className="input bg-gray-50"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Confidence Threshold
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={modelSettings.confidence_threshold}
                    onChange={(e) => setModelSettings(prev => ({
                      ...prev, confidence_threshold: parseFloat(e.target.value)
                    }))}
                    className="input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Retrain Frequency
                  </label>
                  <select
                    value={modelSettings.retrain_frequency}
                    onChange={(e) => setModelSettings(prev => ({
                      ...prev, retrain_frequency: e.target.value
                    }))}
                    className="input"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="manual">Manual Only</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Maximum Features
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="100"
                    value={modelSettings.max_features}
                    onChange={(e) => setModelSettings(prev => ({
                      ...prev, max_features: parseInt(e.target.value)
                    }))}
                    className="input"
                  />
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Automatic Retraining</label>
                  <p className="text-sm text-gray-500">Automatically retrain model with new data</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={modelSettings.auto_retrain}
                    onChange={(e) => setModelSettings(prev => ({
                      ...prev, auto_retrain: e.target.checked
                    }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button className="btn-secondary">
                  <RefreshCwIcon className="h-4 w-4 mr-2" />
                  Retrain Now
                </button>
                <button onClick={handleModelSave} className="btn-primary">
                  <SaveIcon className="h-4 w-4 mr-2" />
                  Save Changes
                </button>
              </div>
            </div>
          </SettingCard>
        </div>
      )}

      {activeTab === 'security' && (
        <div className="space-y-6">
          <SettingCard
            title="Security Configuration"
            description="Configure authentication and security settings"
          >
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Session Timeout (minutes)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="120"
                    value={securitySettings.session_timeout}
                    onChange={(e) => setSecuritySettings(prev => ({
                      ...prev, session_timeout: parseInt(e.target.value)
                    }))}
                    className="input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password Policy
                  </label>
                  <select
                    value={securitySettings.password_policy}
                    onChange={(e) => setSecuritySettings(prev => ({
                      ...prev, password_policy: e.target.value
                    }))}
                    className="input"
                  >
                    <option value="weak">Weak (8+ characters)</option>
                    <option value="medium">Medium (8+ chars, mixed case)</option>
                    <option value="strong">Strong (12+ chars, mixed case, symbols)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API Rate Limit (requests/hour)
                  </label>
                  <input
                    type="number"
                    min="100"
                    max="10000"
                    value={securitySettings.api_rate_limit}
                    onChange={(e) => setSecuritySettings(prev => ({
                      ...prev, api_rate_limit: parseInt(e.target.value)
                    }))}
                    className="input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Login Attempts
                  </label>
                  <input
                    type="number"
                    min="3"
                    max="10"
                    value={securitySettings.login_attempts}
                    onChange={(e) => setSecuritySettings(prev => ({
                      ...prev, login_attempts: parseInt(e.target.value)
                    }))}
                    className="input"
                  />
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Two-Factor Authentication</label>
                  <p className="text-sm text-gray-500">Require 2FA for all user accounts</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={securitySettings.two_factor_auth}
                    onChange={(e) => setSecuritySettings(prev => ({
                      ...prev, two_factor_auth: e.target.checked
                    }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>
              
              <div className="flex justify-end">
                <button onClick={handleSecuritySave} className="btn-primary">
                  <SaveIcon className="h-4 w-4 mr-2" />
                  Save Changes
                </button>
              </div>
            </div>
          </SettingCard>
        </div>
      )}

      {activeTab === 'system' && (
        <div className="space-y-6">
          <SettingCard
            title="System Information"
            description="View system status and perform maintenance tasks"
          >
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">System Status</h4>
                  <dl className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-600">Version:</dt>
                      <dd className="font-medium text-gray-900">{systemInfo.version}</dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-600">Database Size:</dt>
                      <dd className="font-medium text-gray-900">{systemInfo.database_size}</dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-600">Total Records:</dt>
                      <dd className="font-medium text-gray-900">{systemInfo.total_records}</dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-600">Last Backup:</dt>
                      <dd className="font-medium text-gray-900">{systemInfo.last_backup}</dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-600">System Uptime:</dt>
                      <dd className="font-medium text-gray-900">{systemInfo.uptime}</dd>
                    </div>
                  </dl>
                </div>
                
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">API Configuration</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        API Key
                      </label>
                      <div className="flex">
                        <input
                          type={showApiKey ? 'text' : 'password'}
                          value={systemInfo.api_key}
                          disabled
                          className="input rounded-r-none"
                        />
                        <button
                          onClick={() => setShowApiKey(!showApiKey)}
                          className="px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 hover:bg-gray-100"
                        >
                          {showApiKey ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Maintenance Actions</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button onClick={handleBackup} className="flex items-center justify-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <div className="text-center">
                      <DownloadIcon className="h-6 w-6 text-primary-600 mx-auto mb-2" />
                      <div className="text-sm font-medium text-gray-900">Backup Database</div>
                      <div className="text-xs text-gray-500">Create full backup</div>
                    </div>
                  </button>
                  
                  <button onClick={handleRestore} className="flex items-center justify-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <div className="text-center">
                      <UploadIcon className="h-6 w-6 text-warning-600 mx-auto mb-2" />
                      <div className="text-sm font-medium text-gray-900">Restore Database</div>
                      <div className="text-xs text-gray-500">Restore from backup</div>
                    </div>
                  </button>
                  
                  <button className="flex items-center justify-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <div className="text-center">
                      <RefreshCwIcon className="h-6 w-6 text-success-600 mx-auto mb-2" />
                      <div className="text-sm font-medium text-gray-900">System Restart</div>
                      <div className="text-xs text-gray-500">Restart all services</div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </SettingCard>
        </div>
      )}
    </div>
  )
}

export default Settings