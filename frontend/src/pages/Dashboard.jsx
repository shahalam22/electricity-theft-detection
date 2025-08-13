import React from 'react'
import { useQuery } from 'react-query'
import { 
  AlertTriangleIcon, 
  TrendingUpIcon, 
  TrendingDownIcon,
  ZapIcon,
  DollarSignIcon,
  ShieldCheckIcon,
  EyeIcon,
  ClockIcon
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { apiService, apiUtils } from '../utils/api'

const MetricCard = ({ title, value, change, changeType, icon: Icon, color = 'primary' }) => {
  const colorClasses = {
    primary: 'bg-primary-50 text-primary-600',
    success: 'bg-success-50 text-success-600',
    warning: 'bg-warning-50 text-warning-600',
    danger: 'bg-danger-50 text-danger-600',
  }

  const changeColorClasses = {
    increase: changeType === 'positive' ? 'text-success-600' : 'text-danger-600',
    decrease: changeType === 'positive' ? 'text-danger-600' : 'text-success-600',
    neutral: 'text-gray-500'
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change !== undefined && (
            <div className="flex items-center mt-2">
              {change > 0 ? (
                <TrendingUpIcon className={`h-4 w-4 mr-1 ${changeColorClasses.increase}`} />
              ) : change < 0 ? (
                <TrendingDownIcon className={`h-4 w-4 mr-1 ${changeColorClasses.decrease}`} />
              ) : (
                <div className="h-4 w-4 mr-1" />
              )}
              <span className={`text-sm font-medium ${
                change > 0 ? changeColorClasses.increase : 
                change < 0 ? changeColorClasses.decrease : 
                changeColorClasses.neutral
              }`}>
                {change !== 0 ? `${Math.abs(change)}%` : 'No change'}
              </span>
              <span className="text-sm text-gray-500 ml-1">vs last month</span>
            </div>
          )}
        </div>
       
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="h-8 w-8" />
        </div>
      </div>
    </div>
  )
}

const RecentAlert = ({ alert }) => (
  <div className="flex items-center justify-between p-4 border-l-4 border-warning-400 bg-warning-50 rounded-r-lg">
    <div className="flex-1">
      <div className="flex items-center">
        <AlertTriangleIcon className="h-5 w-5 text-warning-600 mr-2" />
        <p className="font-medium text-gray-900">Meter {alert.meter_id}</p>
        <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
          apiUtils.getRiskLevelColor(alert.risk_level)
        }`}>
          {alert.risk_level}
        </span>
      </div>
      <p className="text-sm text-gray-600 mt-1">
        Risk Score: {(alert.risk_score * 100).toFixed(1)}% • {alert.location}
      </p>
      <p className="text-xs text-gray-500 mt-1">
        {apiUtils.parseDate(alert.created_at)?.toLocaleString()}
      </p>
    </div>
   
    <div className="ml-4">
      <button className="btn-primary text-sm">
        View Details
      </button>
    </div>
  </div>
)

const Dashboard = () => {
  // Fetch dashboard data
  const { data: dashboardData, isLoading: dashboardLoading } = useQuery(
    'dashboardSummary',
    () => apiService.alerts.getDashboardSummary(),
    { refetchInterval: 30000 }
  )

  const { data: systemStats, isLoading: statsLoading } = useQuery(
    'systemStats',
    apiService.systemStats,
    { refetchInterval: 60000 }
  )

  const { data: recentAlerts, isLoading: alertsLoading } = useQuery(
    'recentAlerts',
    () => apiService.alerts.getAlerts({ limit: 10, status: 'pending' }),
    { refetchInterval: 15000 }
  )

  const summary = dashboardData?.data?.summary || {}
  const stats = systemStats?.data || {}
  const alerts = recentAlerts?.data?.alerts || []

  // Sample chart data (would come from API in real implementation)
  const detectionTrendData = [
    { month: 'Jan', detections: 45, investigations: 38, confirmed: 22 },
    { month: 'Feb', detections: 52, investigations: 41, confirmed: 28 },
    { month: 'Mar', detections: 48, investigations: 35, confirmed: 19 },
    { month: 'Apr', detections: 61, investigations: 47, confirmed: 34 },
    { month: 'May', detections: 55, investigations: 43, confirmed: 31 },
    { month: 'Jun', detections: 67, investigations: 52, confirmed: 38 }
  ]

  const riskDistributionData = [
    { name: 'Low', value: summary.low_risk_alerts || 0, color: '#10b981' },
    { name: 'Medium', value: summary.medium_risk_alerts || 0, color: '#f59e0b' },
    { name: 'High', value: summary.high_risk_alerts || 0, color: '#ef4444' },
    { name: 'Critical', value: summary.critical_risk_alerts || 0, color: '#dc2626' }
  ]

  const dailyActivityData = [
    { time: '00:00', activity: 12 },
    { time: '04:00', activity: 8 },
    { time: '08:00', activity: 25 },
    { time: '12:00', activity: 35 },
    { time: '16:00', activity: 28 },
    { time: '20:00', activity: 22 }
  ]

  if (dashboardLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Overview</h1>
          <p className="text-gray-600 mt-1">
            Real-time monitoring of electricity theft detection system
          </p>
        </div>
       
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Last Updated</p>
            <p className="text-sm font-medium text-gray-900">
              {new Date().toLocaleTimeString()}
            </p>
          </div>
        
          <div className="w-3 h-3 bg-success-500 rounded-full animate-pulse" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Active Alerts"
          value={apiUtils.formatNumber(summary.pending_alerts || 0)}
          change={summary.alert_change_percentage}
          changeType="negative"
          icon={AlertTriangleIcon}
          color="warning"
        />
        <MetricCard
          title="Total Meters"
          value={apiUtils.formatNumber(summary.total_meters || 0)}
          change={summary.meter_growth_percentage}
          changeType="positive"
          icon={ZapIcon}
          color="primary"
        />
        <MetricCard
          title="Potential Savings"
          value={apiUtils.formatCurrency(summary.potential_savings || 0)}
          change={summary.savings_change_percentage}
          changeType="positive"
          icon={DollarSignIcon}
          color="success"
        />
        <MetricCard
          title="Detection Rate"
          value={apiUtils.formatPercentage(summary.detection_rate || 0)}
          change={summary.detection_improvement}
          changeType="positive"
          icon={ShieldCheckIcon}
          color="success"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Trends */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Detection Trends</h3>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-primary-500 rounded mr-2" />
                <span>Detections</span>
              </div>
             
              <div className="flex items-center">
                <div className="w-3 h-3 bg-warning-500 rounded mr-2" />
                <span>Investigations</span>
              </div>
             
              <div className="flex items-center">
                <div className="w-3 h-3 bg-danger-500 rounded mr-2" />
                <span>Confirmed</span>
              </div>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={detectionTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" stroke="#6b7280" />
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
                dataKey="detections" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 5 }}
              />
              <Line 
                type="monotone" 
                dataKey="investigations" 
                stroke="#f59e0b" 
                strokeWidth={2}
                dot={{ fill: '#f59e0b', strokeWidth: 2, r: 5 }}
              />
              <Line 
                type="monotone" 
                dataKey="confirmed" 
                stroke="#ef4444" 
                strokeWidth={2}
                dot={{ fill: '#ef4444', strokeWidth: 2, r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Distribution */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Level Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskDistributionData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                paddingAngle={2}
                dataKey="value"
              >
                {riskDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Activity Chart */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily System Activity</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={dailyActivityData}>
            <defs>
              <linearGradient id="activityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="time" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#fff', 
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Area
              type="monotone"
              dataKey="activity"
              stroke="#3b82f6"
              fillOpacity={1}
              fill="url(#activityGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Alerts and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Alerts */}
        <div className="lg:col-span-2 card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Alerts</h3>
            <button className="btn-primary text-sm">
              <EyeIcon className="h-4 w-4 mr-2" />
              View All
            </button>
          </div>
          
          {alertsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="loading-spinner" />
            </div>
          ) : alerts.length > 0 ? (
            <div className="space-y-3">
              {alerts.slice(0, 5).map((alert, index) => (
                <RecentAlert key={alert.id || index} alert={alert} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertTriangleIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No recent alerts</p>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="w-full btn-primary">
              <TrendingUpIcon className="h-4 w-4 mr-2" />
              Run Predictions
            </button>
            <button className="w-full btn-secondary">
              <ZapIcon className="h-4 w-4 mr-2" />
              Upload Data
            </button>
            <button className="w-full btn-secondary">
              <AlertTriangleIcon className="h-4 w-4 mr-2" />
              Review Alerts
            </button>
            <button className="w-full btn-secondary">
              <ClockIcon className="h-4 w-4 mr-2" />
              System Reports
            </button>
          </div>

          {/* System Info */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-3">System Status</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Model Version</span>
                <span className="font-medium">FA-XGBoost v2.1</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Last Training</span>
                <span className="font-medium">2 days ago</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Accuracy</span>
                <span className="font-medium text-success-600">94.2%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Precision</span>
                <span className="font-medium text-success-600">91.8%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard