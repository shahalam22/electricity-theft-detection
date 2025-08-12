import React, { useState, useEffect } from 'react';
import { Header } from './components/Layout/Header';
import { Footer } from './components/Layout/Footer';
import { HomePage } from './components/Home/HomePage';
import { LoginForm } from './components/Auth/LoginForm';
import { RegisterForm } from './components/Auth/RegisterForm';
import { DonorSearch } from './components/Search/DonorSearch';
import { UserDashboard } from './components/Dashboard/UserDashboard';
import { AdminPanel } from './components/Admin/AdminPanel';
import { useAuth } from './hooks/useAuth';
import { storageUtils } from './utils/storage';

function App() {
  const { user, isAuthenticated, loading, login, register, logout, updateUser } = useAuth();
  const [currentPage, setCurrentPage] = useState('home');

  useEffect(() => {
    // Initialize sample data
    storageUtils.initializeSampleData();
  }, []);

  const handleLogin = async (email: string, password: string) => {
  const result = await login(email, password);
  if (result.success) {
    // User রোল অনুযায়ী redirect করুন
    if (user?.role === 'admin') {
      setCurrentPage('admin');
    } else if (user?.role === 'donor' || user?.role === 'recipient') {
      setCurrentPage('dashboard');
    } else {
      setCurrentPage('home');
    }
  }
  return result;
};

  const handleRegister = async (userData: any) => {
    const result = await register(userData);
    if (result.success) {
      setCurrentPage('login');
    }
    return result;
  };

  const handleLogout = () => {
    logout();
    setCurrentPage('home');
  };

  const handleNavigate = (page: string) => {
    setCurrentPage(page);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading LifeBlood...</p>
        </div>
      </div>
    );
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'login':
        return (
          <LoginForm
            onLogin={handleLogin}
            onNavigateToRegister={() => setCurrentPage('register')}
          />
        );
      case 'register':
        return (
          <RegisterForm
            onRegister={handleRegister}
            onNavigateToLogin={() => setCurrentPage('login')}
          />
        );
      case 'search':
        return <DonorSearch currentUser={user} />;
      case 'dashboard':
        return user ? (
          <UserDashboard user={user} onUpdateUser={updateUser} />
        ) : (
          <div>Please log in to view your dashboard</div>
        );
      case 'admin':
        return user?.role === 'admin' ? (
          <AdminPanel currentUser={user} />
        ) : (
          <div>Access denied. Admin only.</div>
        );
      case 'home':
      default:
        return (
          <HomePage
            onNavigate={handleNavigate}
            isAuthenticated={isAuthenticated}
          />
        );
    }
  };

  const showHeaderFooter = !['login', 'register'].includes(currentPage);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {showHeaderFooter && (
        <Header
          user={user}
          onLogout={handleLogout}
          currentPage={currentPage}
          onNavigate={handleNavigate}
        />
      )}
      
      <main className="flex-1">
        {renderPage()}
      </main>
      
      {showHeaderFooter && <Footer />}
    </div>
  );
}

export default App;