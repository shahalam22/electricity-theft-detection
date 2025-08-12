import React from 'react';
import { Heart, Search, Shield, Users, Clock, MapPin, Phone, ArrowRight } from 'lucide-react';

interface HomePageProps {
  onNavigate: (page: string) => void;
  isAuthenticated: boolean;
}

export const HomePage: React.FC<HomePageProps> = ({ onNavigate, isAuthenticated }) => {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-r from-red-600 to-red-700 overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
            <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
              <div className="sm:text-center lg:text-left">
                <h1 className="text-4xl tracking-tight font-extrabold text-white sm:text-5xl md:text-6xl">
                  <span className="block">Save Lives with</span>
                  <span className="block text-red-200">LifeBlood</span>
                </h1>
                <p className="mt-3 text-base text-red-100 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                  Connect blood donors with those in need. Fast, reliable, and organized. 
                  Every donation saves a life - join our community of heroes today.
                </p>
                <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                  <div className="rounded-md shadow">
                    <button
                      onClick={() => onNavigate('search')}
                      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-red-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10 transition-colors"
                    >
                      <Search className="h-5 w-5 mr-2" />
                      Find Donors Now
                    </button>
                  </div>
                  <div className="mt-3 sm:mt-0 sm:ml-3">
                    <button
                      onClick={() => onNavigate(isAuthenticated ? 'dashboard' : 'register')}
                      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-red-500 hover:bg-red-400 md:py-4 md:text-lg md:px-10 transition-colors"
                    >
                      <Heart className="h-5 w-5 mr-2" />
                      {isAuthenticated ? 'My Dashboard' : 'Become a Donor'}
                    </button>
                  </div>
                </div>
              </div>
            </main>
          </div>
        </div>
        <div className="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2">
          <img
            className="h-56 w-full object-cover sm:h-72 md:h-96 lg:w-full lg:h-full opacity-20"
            src="https://images.pexels.com/photos/6824324/pexels-photo-6824324.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
            alt="Blood donation hero"
          />
        </div>
      </div>

      {/* Features Section */}
      <div className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-red-600 font-semibold tracking-wide uppercase">Features</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Why Choose LifeBlood?
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-500 lg:mx-auto">
              Our platform makes blood donation and finding donors simple, fast, and secure.
            </p>
          </div>

          <div className="mt-10">
            <div className="space-y-10 md:space-y-0 md:grid md:grid-cols-2 md:gap-x-8 md:gap-y-10">
              <div className="relative">
                <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-red-500 text-white">
                  <Search className="h-6 w-6" />
                </div>
                <p className="ml-16 text-lg leading-6 font-medium text-gray-900">Smart Search</p>
                <p className="mt-2 ml-16 text-base text-gray-500">
                  Find donors by blood group and location. Results sorted by distance to connect you with the nearest available donors.
                </p>
              </div>

              <div className="relative">
                <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-red-500 text-white">
                  <MapPin className="h-6 w-6" />
                </div>
                <p className="ml-16 text-lg leading-6 font-medium text-gray-900">Location-Based</p>
                <p className="mt-2 ml-16 text-base text-gray-500">
                  GPS-enabled search to find the closest donors. Share donation locations for convenient meetups.
                </p>
              </div>

              <div className="relative">
                <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-red-500 text-white">
                  <Clock className="h-6 w-6" />
                </div>
                <p className="ml-16 text-lg leading-6 font-medium text-gray-900">Smart Availability</p>
                <p className="mt-2 ml-16 text-base text-gray-500">
                  Automatic 4-month cooldown system ensures donor health while maintaining accurate availability status.
                </p>
              </div>

              <div className="relative">
                <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-red-500 text-white">
                  <Shield className="h-6 w-6" />
                </div>
                <p className="ml-16 text-lg leading-6 font-medium text-gray-900">Verified & Secure</p>
                <p className="mt-2 ml-16 text-base text-gray-500">
                  All users are verified by administrators. Secure platform with role-based access and data protection.
                </p>
              </div>

              <div className="relative">
                <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-red-500 text-white">
                  <Phone className="h-6 w-6" />
                </div>
                <p className="ml-16 text-lg leading-6 font-medium text-gray-900">Direct Communication</p>
                <p className="mt-2 ml-16 text-base text-gray-500">
                  Connect directly with donors through phone calls and SMS. No intermediaries - just direct communication.
                </p>
              </div>

              <div className="relative">
                <div className="absolute flex items-center justify-center h-12 w-12 rounded-md bg-red-500 text-white">
                  <Users className="h-6 w-6" />
                </div>
                <p className="ml-16 text-lg leading-6 font-medium text-gray-900">Community Driven</p>
                <p className="mt-2 ml-16 text-base text-gray-500">
                  Join a community of heroes. Track your donation history and help build a network of life-savers.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Blood Types Section */}
      <div className="bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">Blood Type Compatibility</h2>
            <p className="mt-4 text-lg text-gray-600">
              Understanding blood compatibility is crucial for safe donations
            </p>
          </div>
          
          <div className="mt-10 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
            {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((type) => (
              <div key={type} className="bg-white rounded-lg shadow-md p-6 text-center hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-white font-bold text-lg">{type}</span>
                </div>
                <p className="text-sm text-gray-600">
                  {type === 'O-' ? 'Universal Donor' : 
                   type === 'AB+' ? 'Universal Recipient' : 
                   'Compatible Types'}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-red-600 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-white">1M+</div>
              <div className="text-red-200 text-lg">Lives Saved</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-white">50K+</div>
              <div className="text-red-200 text-lg">Active Donors</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-white">24/7</div>
              <div className="text-red-200 text-lg">Emergency Support</div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-extrabold text-gray-900">
            Ready to Save Lives?
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            Join thousands of heroes who are making a difference in their communities
          </p>
          <div className="mt-8 flex justify-center space-x-4">
            <button
              onClick={() => onNavigate('register')}
              className="bg-red-600 hover:bg-red-700 text-white px-8 py-3 rounded-md font-medium transition-colors flex items-center"
            >
              Register Now
              <ArrowRight className="h-5 w-5 ml-2" />
            </button>
            <button
              onClick={() => onNavigate('search')}
              className="bg-gray-600 hover:bg-gray-700 text-white px-8 py-3 rounded-md font-medium transition-colors"
            >
              Find Donors
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};