import React from 'react';
import { Heart, User, LogOut, Users, Search } from 'lucide-react';
import { User as UserType } from '../../types';

interface HeaderProps {
  user: UserType | null;
  onLogout: () => void;
  currentPage: string;
  onNavigate: (page: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ user, onLogout, currentPage, onNavigate }) => {
  const isAdmin = user?.role === 'admin';

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <div 
              className="flex items-center space-x-2 cursor-pointer"
              onClick={() => onNavigate('home')}
            >
              <Heart className="h-8 w-8 text-red-600" />
              <span className="text-2xl font-bold text-gray-900">LifeBlood</span>
            </div>
            
            <nav className="hidden md:flex space-x-6">
              <button
                onClick={() => onNavigate('search')}
                className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  currentPage === 'search'
                    ? 'bg-red-100 text-red-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Search className="h-4 w-4" />
                <span>Find Donors</span>
              </button>
              
              {user && (
                <button
                  onClick={() => onNavigate('dashboard')}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentPage === 'dashboard'
                      ? 'bg-red-100 text-red-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <User className="h-4 w-4" />
                  <span>Dashboard</span>
                </button>
              )}
              
              {isAdmin && (
                <button
                  onClick={() => onNavigate('admin')}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentPage === 'admin'
                      ? 'bg-red-100 text-red-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Users className="h-4 w-4" />
                  <span>Admin</span>
                </button>
              )}
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-red-700 font-medium text-sm">
                      {user.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="hidden md:block">
                    <p className="text-sm font-medium text-gray-900">{user.name}</p>
                    <p className="text-xs text-gray-500">{user.bloodGroup}</p>
                  </div>
                </div>
                <button
                  onClick={onLogout}
                  className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-md transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden md:inline">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onNavigate('login')}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Login
                </button>
                <button
                  onClick={() => onNavigate('register')}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Register
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};