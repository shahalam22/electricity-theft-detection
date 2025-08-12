import { useState, useEffect } from 'react';
import { User, AuthState } from '../types';
import { apiService } from '../services/apiService';

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    loading: true,
  });

  useEffect(() => {
    // Check for existing session on app load using token
    const token = localStorage.getItem('token');
    if (token) {
      // Optionally validate token with backend (e.g., /auth/validate)
      setAuthState({
        user: { id: '', email: '', role: '', name: '', bloodGroup: '' }, // Placeholder; fetch user data if needed
        isAuthenticated: true,
        loading: false,
      });
    } else {
      setAuthState({
        user: null,
        isAuthenticated: false,
        loading: false,
      });
    }
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
  try {
    // passwordHash field দিয়ে পাঠান (backend এ passwordHash expect করছে)
    const response = await apiService.login({ email, password }); // apiService এ আগেই passwordHash হিসেবে পাঠাচ্ছে
    const userData = response;
    
    setAuthState({
      user: userData,
      isAuthenticated: true,
      loading: false,
    });
    
    return { success: true };
  } catch (error: any) {
    const errorMessage = error.response?.status === 401 ? 'Invalid email or password' : 'Login failed';
    setAuthState({
      user: null,
      isAuthenticated: false,
      loading: false,
    });
    return { success: false, error: errorMessage };
  }
};
  const register = async (userData: Omit<User, 'id' | 'registrationDate' | 'isVerified' | 'isActive' | 'isAvailable'>): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await apiService.register({
        ...userData,
        passwordHash: userData.password, // Assume password is hashed or sent as is
      });
      return { success: true, message: 'Registration successful' };
    } catch (error: any) {
      const errorMessage = error.response?.status === 409 ? 'User already exists' : 'Registration failed';
      return { success: false, error: errorMessage };
    }
  };

  const logout = () => {
    apiService.logout();
    setAuthState({
      user: null,
      isAuthenticated: false,
      loading: false,
    });
  };

  const updateUser = async (updatedUser: User) => {
    if (authState.user) {
      const response = await apiService.updateUser(parseInt(authState.user.id), updatedUser);
      setAuthState(prev => ({
        ...prev,
        user: response,
      }));
    }
  };

  return {
    ...authState,
    login,
    register,
    logout,
    updateUser,
  };
};