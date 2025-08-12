import axios from 'axios';
import { API_BASE_URL } from '../config/apiConfig'; // Adjust path as needed

// ------------------------
// Interfaces
// ------------------------

interface User {
  email: string;
  password: string;
}

interface DonationRecord {
  donorId: number;
  // Add other required fields if needed
}

interface SearchParams {
  bloodGroup?: string;
  division?: string;
  district?: string;
  upazila?: string;
}

// ------------------------
// Axios Instance
// ------------------------

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ------------------------
// Token Interceptor
// ------------------------

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ------------------------
// API Service
// ------------------------

export const apiService = {
  // Auth
  register: async (user: User) => {
    const response = await api.post('/auth/register', user);
    return response.data;
  },

  login: async (user: User) => {
  try {
    console.log('Sending login request:', { email: user.email, passwordHash: user.password });
    
    const response = await api.post('/auth/login', {
      email: user.email,
      passwordHash: user.password,
    });

    console.log('Login response:', response);
    console.log('Response headers:', response.headers);
    
    // Case-insensitive header check
    const authHeader = response.headers['authorization'] || 
                      response.headers['Authorization'] ||
                      response.headers['AUTHORIZATION'];
                      
    console.log('Found auth header:', authHeader);
    
    const token = authHeader?.startsWith('Bearer ') ? authHeader.split(' ')[1] : null;

    if (token) {
      localStorage.setItem('token', token);
      console.log('Token saved successfully:', token);
    } else {
      console.warn('Authorization token not found in headers');
      console.log('All available headers:', Object.keys(response.headers));
    }

    return response.data;
  } catch (error: any) {
    console.error('Login error details:', error);
    throw error;
  }
 },
 
  logout: () => {
    localStorage.removeItem('token');
  },

  // Donations
  addDonation: async (record: DonationRecord) => {
    const response = await api.post('/donations', record);
    return response.data;
  },

  getDonations: async (donorId: number) => {
    const response = await api.get(`/donations/${donorId}`);
    return response.data;
  },

  // Users
  updateUser: async (id: number, user: User) => {
    const response = await api.put(`/users/${id}`, user);
    return response.data;
  },

  getUser: async (id: number) => {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },

  // Admin
  getAllUsers: async () => {
    const response = await api.get('/admin/users');
    return response.data;
  },

  verifyUser: async (id: number) => {
    const response = await api.put(`/admin/verify/${id}`);
    return response.data;
  },

  disableUser: async (id: number) => {
    const response = await api.put(`/admin/disable/${id}`);
    return response.data;
  },

  // Search
  searchDonors: async (params: SearchParams) => {
    const response = await api.get('/search', { params });
    return response.data;
  },
};
