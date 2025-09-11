import React from 'react'
import { Link } from 'react-router-dom'
import { HomeIcon, ArrowLeftIcon, SearchIcon } from 'lucide-react'

const NotFound = () => {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        {/* 404 Illustration */}
        <div className="mb-8">
          <div className="text-9xl font-bold text-primary-200 mb-4">404</div>
         
          <div className="relative">
            <SearchIcon className="h-16 w-16 text-gray-300 mx-auto" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-4 h-4 bg-danger-500 rounded-full animate-ping" />
            </div>
          </div>
        </div>

        {/* Error Message */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Page Not Found
          </h1>
          <p className="text-lg text-gray-600 mb-2">
            Oops! The page you're looking for doesn't exist.
          </p>
          <p className="text-gray-500">
            It might have been moved, deleted, or you entered the wrong URL.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center space-y-3 sm:space-y-0 sm:space-x-4">
          <Link
            to="/dashboard"
            className="btn-primary"
          >
            <HomeIcon className="h-4 w-4 mr-2" />
            Go to Dashboard
          </Link>
          
          <button
            onClick={() => window.history.back()}
            className="btn-secondary"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Go Back
          </button>
        </div>

        {/* Quick Links */}
        <div className="mt-12 pt-8 border-t border-gray-200">
          <p className="text-sm text-gray-500 mb-4">You might be looking for:</p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/alerts"
              className="text-sm text-primary-600 hover:text-primary-800 hover:underline"
            >
              Alert Management
            </Link>
            <Link
              to="/predictions"
              className="text-sm text-primary-600 hover:text-primary-800 hover:underline"
            >
              Theft Predictions
            </Link>
            <Link
              to="/data"
              className="text-sm text-primary-600 hover:text-primary-800 hover:underline"
            >
              Data Management
            </Link>
            <Link
              to="/settings"
              className="text-sm text-primary-600 hover:text-primary-800 hover:underline"
            >
              System Settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotFound