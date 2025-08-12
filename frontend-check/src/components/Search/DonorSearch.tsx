import React, { useState, useEffect } from 'react';
import { Search, MapPin, Phone, Clock, Droplet, Filter } from 'lucide-react';
import { BloodGroup, User } from '../../types';
import { storageUtils } from '../../utils/storage';
import { locationUtils } from '../../utils/location';
import { dateUtils } from '../../utils/dateUtils';

interface DonorSearchProps {
  currentUser: User | null;
}

interface DonorWithDistance extends User {
  distance?: number;
}

export const DonorSearch: React.FC<DonorSearchProps> = ({ currentUser }) => {
  const [searchFilters, setSearchFilters] = useState({
    bloodGroup: 'O+' as BloodGroup,
    city: '',
    state: '',
    maxDistance: 50
  });
  const [donors, setDonors] = useState<DonorWithDistance[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const bloodGroups: BloodGroup[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

  const searchDonors = async () => {
    setLoading(true);
    setHasSearched(true);

    try {
      // Get all users who are donors
      const allUsers = storageUtils.getUsers();
      let availableDonors = allUsers.filter(user => 
        user.role === 'donor' && 
        user.isActive && 
        user.isVerified &&
        user.bloodGroup === searchFilters.bloodGroup
      );

      // Filter by availability (4-month rule)
      availableDonors = availableDonors.filter(donor => 
        dateUtils.isDonorAvailable(donor.lastDonationDate)
      );

      // Filter by location if provided
      if (searchFilters.city || searchFilters.state) {
        availableDonors = availableDonors.filter(donor => {
          const cityMatch = !searchFilters.city || 
            donor.city.toLowerCase().includes(searchFilters.city.toLowerCase());
          const stateMatch = !searchFilters.state || 
            donor.state.toLowerCase().includes(searchFilters.state.toLowerCase());
          return cityMatch && stateMatch;
        });
      }

      // Calculate distances and sort by proximity
      const donorsWithDistance: DonorWithDistance[] = [];
      const userLocation = await locationUtils.getCurrentLocation();
      
      for (const donor of availableDonors) {
        let distance: number | undefined;
        
        if (userLocation && donor.latitude && donor.longitude) {
          distance = locationUtils.calculateDistance(
            userLocation.latitude,
            userLocation.longitude,
            donor.latitude,
            donor.longitude
          );
        }

        // Filter by max distance if we have location data
        if (distance !== undefined && distance <= searchFilters.maxDistance) {
          donorsWithDistance.push({ ...donor, distance });
        } else if (distance === undefined) {
          // Include donors without location data
          donorsWithDistance.push({ ...donor });
        }
      }

      // Sort by distance (nearest first)
      donorsWithDistance.sort((a, b) => {
        if (a.distance === undefined && b.distance === undefined) return 0;
        if (a.distance === undefined) return 1;
        if (b.distance === undefined) return -1;
        return a.distance - b.distance;
      });

      setDonors(donorsWithDistance);

      // Save search to history if user is logged in
      if (currentUser) {
        const searchRecord = {
          id: Date.now().toString(),
          bloodGroup: searchFilters.bloodGroup,
          location: `${searchFilters.city}, ${searchFilters.state}`,
          timestamp: new Date().toISOString(),
          resultsCount: donorsWithDistance.length
        };

        const updatedUser = {
          ...currentUser,
          searchHistory: [...(currentUser.searchHistory || []), searchRecord]
        };

        storageUtils.saveUser(updatedUser);
      }

    } catch (error) {
      console.error('Search failed:', error);
    }

    setLoading(false);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Find Blood Donors</h1>
        <p className="mt-2 text-lg text-gray-600">
          Connect with verified blood donors in your area
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Blood Group
            </label>
            <div className="relative">
              <Droplet className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <select
                value={searchFilters.bloodGroup}
                onChange={(e) => setSearchFilters(prev => ({ 
                  ...prev, 
                  bloodGroup: e.target.value as BloodGroup 
                }))}
                className="pl-10 w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
              >
                {bloodGroups.map((group) => (
                  <option key={group} value={group}>{group}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              City
            </label>
            <input
              type="text"
              value={searchFilters.city}
              onChange={(e) => setSearchFilters(prev => ({ ...prev, city: e.target.value }))}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
              placeholder="Enter city"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              State
            </label>
            <input
              type="text"
              value={searchFilters.state}
              onChange={(e) => setSearchFilters(prev => ({ ...prev, state: e.target.value }))}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
              placeholder="Enter state"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Distance (miles)
            </label>
            <input
              type="number"
              value={searchFilters.maxDistance}
              onChange={(e) => setSearchFilters(prev => ({ 
                ...prev, 
                maxDistance: parseInt(e.target.value) || 50 
              }))}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
              min="1"
              max="500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={searchDonors}
              disabled={loading}
              className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Search className="h-5 w-5 mr-2" />
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>
      </div>

      {/* Search Results */}
      {hasSearched && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              Search Results ({donors.length} donors found)
            </h2>
            <div className="flex items-center text-sm text-gray-500">
              <Filter className="h-4 w-4 mr-1" />
              Blood Type: {searchFilters.bloodGroup}
            </div>
          </div>

          {donors.length === 0 ? (
            <div className="text-center py-12">
              <Droplet className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No donors found
              </h3>
              <p className="text-gray-500">
                Try adjusting your search criteria or expanding the search area.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {donors.map((donor) => (
                <div key={donor.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{donor.name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {donor.bloodGroup}
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Available
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center text-sm text-gray-600">
                      <MapPin className="h-4 w-4 mr-2" />
                      <span>{donor.city}, {donor.state}</span>
                      {donor.distance && (
                        <span className="ml-2 text-blue-600 font-medium">
                          ({donor.distance.toFixed(1)} mi)
                        </span>
                      )}
                    </div>

                    <div className="flex items-center text-sm text-gray-600">
                      <Phone className="h-4 w-4 mr-2" />
                      <a 
                        href={`tel:${donor.phone}`}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
                        {donor.phone}
                      </a>
                    </div>

                    {donor.lastDonationDate && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Clock className="h-4 w-4 mr-2" />
                        <span>
                          Last donated: {dateUtils.formatDate(donor.lastDonationDate)}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex space-x-2">
                      <a
                        href={`tel:${donor.phone}`}
                        className="flex-1 bg-red-600 hover:bg-red-700 text-white text-center px-3 py-2 rounded-md text-sm font-medium transition-colors"
                      >
                        Call Now
                      </a>
                      <a
                        href={`sms:${donor.phone}`}
                        className="flex-1 bg-gray-600 hover:bg-gray-700 text-white text-center px-3 py-2 rounded-md text-sm font-medium transition-colors"
                      >
                        SMS
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};