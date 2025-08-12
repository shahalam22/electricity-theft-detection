import { User, DonationRecord, SearchRecord } from '../types';

const USERS_KEY = 'lifeblood_users';
const DONATIONS_KEY = 'lifeblood_donations';
const CURRENT_USER_KEY = 'lifeblood_current_user';

export const storageUtils = {
  // User management
  getUsers(): User[] {
    const users = localStorage.getItem(USERS_KEY);
    return users ? JSON.parse(users) : [];
  },

  saveUsers(users: User[]): void {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  },

  getUserById(id: string): User | null {
    const users = this.getUsers();
    return users.find(user => user.id === id) || null;
  },

  getUserByEmail(email: string): User | null {
    const users = this.getUsers();
    return users.find(user => user.email === email) || null;
  },

  saveUser(user: User): void {
    const users = this.getUsers();
    const existingIndex = users.findIndex(u => u.id === user.id);
    
    if (existingIndex >= 0) {
      users[existingIndex] = user;
    } else {
      users.push(user);
    }
    
    this.saveUsers(users);
  },

  deleteUser(userId: string): void {
    const users = this.getUsers().filter(user => user.id !== userId);
    this.saveUsers(users);
  },

  // Current user session
  getCurrentUser(): User | null {
    const userJson = localStorage.getItem(CURRENT_USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
  },

  setCurrentUser(user: User | null): void {
    if (user) {
      localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(CURRENT_USER_KEY);
    }
  },

  // Donation records
  getDonations(): DonationRecord[] {
    const donations = localStorage.getItem(DONATIONS_KEY);
    return donations ? JSON.parse(donations) : [];
  },

  saveDonation(donation: DonationRecord): void {
    const donations = this.getDonations();
    donations.push(donation);
    localStorage.setItem(DONATIONS_KEY, JSON.stringify(donations));
  },

  getDonationsByDonor(donorId: string): DonationRecord[] {
    return this.getDonations().filter(donation => donation.donorId === donorId);
  },

  // Initialize with sample data
  initializeSampleData(): void {
    if (this.getUsers().length === 0) {
      const sampleUsers: User[] = [
        {
          id: '1',
          name: 'John Smith',
          email: 'john@example.com',
          password: 'password123',
          bloodGroup: 'O+',
          phone: '+1-555-0101',
          address: '123 Main St',
          city: 'New York',
          state: 'NY',
          zipCode: '10001',
          latitude: 40.7128,
          longitude: -74.0060,
          role: 'donor',
          isVerified: true,
          isActive: true,
          isAvailable: true,
          registrationDate: '2024-01-15',
        },
        {
          id: '2',
          name: 'Sarah Johnson',
          email: 'sarah@example.com',
          password: 'password123',
          bloodGroup: 'A+',
          phone: '+1-555-0102',
          address: '456 Oak Ave',
          city: 'New York',
          state: 'NY',
          zipCode: '10002',
          latitude: 40.7589,
          longitude: -73.9851,
          role: 'donor',
          isVerified: true,
          isActive: true,
          isAvailable: true,
          registrationDate: '2024-02-10',
        },
        {
          id: '3',
          name: 'Admin User',
          email: 'admin@lifeblood.com',
          password: 'admin123',
          bloodGroup: 'AB+',
          phone: '+1-555-0000',
          address: '789 Admin St',
          city: 'New York',
          state: 'NY',
          zipCode: '10003',
          role: 'admin',
          isVerified: true,
          isActive: true,
          isAvailable: false,
          registrationDate: '2024-01-01',
        }
      ];
      
      this.saveUsers(sampleUsers);
    }
  }
};