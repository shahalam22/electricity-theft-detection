import React, { useState, useEffect } from 'react';
import { User, Heart, Clock, MapPin, Calendar, Plus, Edit, Check } from 'lucide-react';
import { User as UserType, DonationRecord } from '../../types';
import { storageUtils } from '../../utils/storage';
import { dateUtils } from '../../utils/dateUtils';

interface UserDashboardProps {
  user: UserType;
  onUpdateUser: (user: UserType) => void;
}

export const UserDashboard: React.FC<UserDashboardProps> = ({ user, onUpdateUser }) => {
  const [donations, setDonations] = useState<DonationRecord[]>([]);
  const [showAddDonation, setShowAddDonation] = useState(false);
  const [newDonation, setNewDonation] = useState({
    date: new Date().toISOString().split('T')[0],
    location: '',
    notes: ''
  });

  useEffect(() => {
    if (user.role === 'donor') {
      const userDonations = storageUtils.getDonationsByDonor(user.id);
      setDonations(userDonations);
    }
  }, [user.id, user.role]);

  const handleAddDonation = () => {
    if (!newDonation.date || !newDonation.location) return;

    const donation: DonationRecord = {
      id: Date.now().toString(),
      donorId: user.id,
      date: newDonation.date,
      location: newDonation.location,
      notes: newDonation.notes
    };

    storageUtils.saveDonation(donation);
    
    // Update user's last donation date and availability
    const updatedUser: UserType = {
      ...user,
      lastDonationDate: newDonation.date,
      isAvailable: false
    };

    onUpdateUser(updatedUser);
    setDonations(prev => [...prev, donation]);
    setShowAddDonation(false);
    setNewDonation({ date: new Date().toISOString().split('T')[0], location: '', notes: '' });
  };

  const getAvailabilityStatus = () => {
    if (user.role !== 'donor') return null;
    
    if (!user.lastDonationDate) {
      return { status: 'available', message: 'Ready to donate', color: 'green' };
    }

    const isAvailable = dateUtils.isDonorAvailable(user.lastDonationDate);
    
    if (isAvailable) {
      return { status: 'available', message: 'Ready to donate', color: 'green' };
    } else {
      const daysLeft = dateUtils.getDaysUntilAvailable(user.lastDonationDate);
      return { 
        status: 'unavailable', 
        message: `Available in ${daysLeft} days`, 
        color: 'red' 
      };
    }
  };

  const availabilityStatus = getAvailabilityStatus();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user.name}!
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          {user.role === 'donor' ? 'Thank you for being a life saver' : 'Find the help you need'}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Card */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center space-x-4 mb-6">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
              <User className="h-8 w-8 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{user.name}</h2>
              <p className="text-gray-600">{user.email}</p>
              <div className="flex items-center space-x-2 mt-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  {user.bloodGroup}
                </span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user.role === 'donor' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                }`}>
                  {user.role === 'donor' ? 'Donor' : 'Recipient'}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center text-sm text-gray-600">
              <MapPin className="h-4 w-4 mr-2" />
              <span>{user.city}, {user.state}</span>
            </div>
            <div className="flex items-center text-sm text-gray-600">
              <Calendar className="h-4 w-4 mr-2" />
              <span>Member since {dateUtils.formatDate(user.registrationDate)}</span>
            </div>
          </div>

          {availabilityStatus && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Donation Status</span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  availabilityStatus.color === 'green' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {availabilityStatus.message}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {user.role === 'donor' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  Donation History
                </h3>
                <button
                  onClick={() => setShowAddDonation(true)}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Donation
                </button>
              </div>

              {showAddDonation && (
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h4 className="font-medium text-gray-900 mb-4">Record New Donation</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Donation Date
                      </label>
                      <input
                        type="date"
                        value={newDonation.date}
                        onChange={(e) => setNewDonation(prev => ({ ...prev, date: e.target.value }))}
                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Location
                      </label>
                      <input
                        type="text"
                        value={newDonation.location}
                        onChange={(e) => setNewDonation(prev => ({ ...prev, location: e.target.value }))}
                        placeholder="Hospital/Blood Bank name"
                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                      />
                    </div>
                  </div>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Notes (Optional)
                    </label>
                    <textarea
                      value={newDonation.notes}
                      onChange={(e) => setNewDonation(prev => ({ ...prev, notes: e.target.value }))}
                      rows={2}
                      className="w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
                      placeholder="Any additional notes..."
                    />
                  </div>
                  <div className="flex space-x-3 mt-4">
                    <button
                      onClick={handleAddDonation}
                      className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
                    >
                      <Check className="h-4 w-4 mr-2" />
                      Save Donation
                    </button>
                    <button
                      onClick={() => setShowAddDonation(false)}
                      className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {donations.length === 0 ? (
                <div className="text-center py-8">
                  <Heart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    No donations recorded yet
                  </h4>
                  <p className="text-gray-500">
                    Start saving lives by recording your first donation!
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {donations.map((donation) => (
                    <div key={donation.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-4">
                            <span className="font-medium text-gray-900">
                              {dateUtils.formatDate(donation.date)}
                            </span>
                            <span className="text-gray-600">{donation.location}</span>
                          </div>
                          {donation.notes && (
                            <p className="text-sm text-gray-500 mt-1">{donation.notes}</p>
                          )}
                        </div>
                        <div className="flex items-center text-red-600">
                          <Heart className="h-5 w-5" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Search History */}
          {user.searchHistory && user.searchHistory.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">
                Recent Searches
              </h3>
              <div className="space-y-4">
                {user.searchHistory.slice(-5).reverse().map((search) => (
                  <div key={search.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            {search.bloodGroup}
                          </span>
                          <span className="text-gray-600">{search.location}</span>
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          {search.resultsCount} donors found
                        </p>
                      </div>
                      <div className="text-sm text-gray-500">
                        {dateUtils.formatDate(search.timestamp)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};