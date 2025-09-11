import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  AlertTriangleIcon, 
  TrendingUpIcon, 
  DatabaseIcon, 
  SettingsIcon,
  MenuIcon,
  XIcon,
  ZapIcon,
  UserIcon,
  BellIcon
} from 'lucide-react'
import { useQuery } from 'react-query'
import { apiService } from '../utils/api'

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  // Get system info for header
  const { data: systemInfo } = useQuery('systemInfo', apiService.systemInfo, {
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  // Get dashboard summary for notification count
  const { data: dashboardData } = useQuery('dashboardSummary', 
    () => apiService.alerts.getDashboardSummary(),
    {
      refetchInterval: 10000, // Refetch every 10 seconds
    }
  )

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, current: location.pathname === '/' || location.pathname === '/dashboard' },
    { name: 'Alerts', href: '/alerts', icon: AlertTriangleIcon, current: location.pathname.startsWith('/alerts'), badge: dashboardData?.data?.summary?.pending_alerts },
    { name: 'Predictions', href: '/predictions', icon: TrendingUpIcon, current: location.pathname === '/predictions' },
    { name: 'Data Management', href: '/data', icon: DatabaseIcon, current: location.pathname === '/data' },
    { name: 'Settings', href: '/settings', icon: SettingsIcon, current: location.pathname === '/settings' },
  ]

  const pendingAlerts = dashboardData?.data?.summary?.pending_alerts || 0

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <div className="flex items-center">
            <ZapIcon className="h-8 w-8 text-primary-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">TheftGuard</span>
          </div>
          <button
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <XIcon className="h-6 w-6 text-gray-500" />
          </button>
        </div>

        <nav className="mt-8 px-4">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    className={({ isActive }) =>
                      `group flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                        isActive
                          ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-600'
                          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                      }`
                    }
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
                    {item.name}
                    {item.badge && item.badge > 0 && (
                      <span className="ml-auto bg-danger-100 text-danger-600 text-xs font-medium px-2 py-1 rounded-full">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                </li>
              )
            })}
          </ul>
        </nav>

        {/* System Status */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-1">System Status</div>
           
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-2 ${
                systemInfo?.data?.status === 'healthy' ? 'bg-success-500' : 'bg-warning-500'
              }`} />
              <span className="text-sm font-medium text-gray-700">
                {systemInfo?.data?.status === 'healthy' ? 'Operational' : 'Degraded'}
              </span>
            </div>
            {systemInfo?.data?.version && (
              <div className="text-xs text-gray-400 mt-1">
                v{systemInfo.data.version}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:ml-64 flex flex-col min-h-screen">
        {/* Top navigation */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex items-center">

              <button
                className="lg:hidden"
                onClick={() => setSidebarOpen(true)}
              >
                <MenuIcon className="h-6 w-6 text-gray-500" />
              </button>
              <h1 className="ml-4 lg:ml-0 text-2xl font-bold text-gray-900">
                {navigation.find(item => item.current)?.name || 'Dashboard'}
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <div className="relative">
                <BellIcon className="h-6 w-6 text-gray-500" />
                {pendingAlerts > 0 && (
                  <span className="absolute -top-1 -right-1 bg-danger-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {pendingAlerts > 99 ? '99+' : pendingAlerts}
                  </span>
                )}
              </div>

              {/* User menu */}
              <div className="flex items-center">
                <UserIcon className="h-6 w-6 text-gray-500" />
                <span className="ml-2 text-sm font-medium text-gray-700">
                  Utility Staff
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>
              © 2024 Electricity Theft Detection System. All rights reserved.
            </div>
            <div className="flex items-center space-x-4">
              <span>Powered by FA-XGBoost</span>
              {systemInfo?.data?.model_info?.status === 'loaded' && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-success-500 rounded-full mr-1" />
                  <span>AI Model Active</span>
                </div>
              )}
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default Layout