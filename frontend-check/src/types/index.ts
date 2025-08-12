export interface User {
  id: string;
  name: string;
  email: string;
  password: string;
  bloodGroup: BloodGroup;
  phone: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  latitude?: number;
  longitude?: number;
  role: 'donor' | 'recipient' | 'admin';
  isVerified: boolean;
  isActive: boolean;
  lastDonationDate?: string;
  isAvailable: boolean;
  registrationDate: string;
  searchHistory?: SearchRecord[];
}

export interface DonationRecord {
  id: string;
  donorId: string;
  date: string;
  location: string;
  notes?: string;
  recipientId?: string;
}

export interface SearchRecord {
  id: string;
  bloodGroup: BloodGroup;
  location: string;
  timestamp: string;
  resultsCount: number;
}

export type BloodGroup = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-';

export interface SearchFilters {
  bloodGroup: BloodGroup;
  city: string;
  state: string;
  maxDistance?: number;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
}