export interface Coordinates {
  latitude: number;
  longitude: number;
}

export const locationUtils = {
  // Calculate distance between two points using Haversine formula
  calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): number {
    const R = 3959; // Earth's radius in miles
    const dLat = this.toRad(lat2 - lat1);
    const dLon = this.toRad(lon2 - lon1);
    
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(lat1)) *
        Math.cos(this.toRad(lat2)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  },

  toRad(degrees: number): number {
    return degrees * (Math.PI / 180);
  },

  // Mock geocoding for demo purposes
  async geocodeAddress(address: string, city: string, state: string): Promise<Coordinates | null> {
    // In a real app, you'd use a geocoding service like Google Maps API
    const mockCoordinates: { [key: string]: Coordinates } = {
      'New York, NY': { latitude: 40.7128, longitude: -74.0060 },
      'Los Angeles, CA': { latitude: 34.0522, longitude: -118.2437 },
      'Chicago, IL': { latitude: 41.8781, longitude: -87.6298 },
      'Houston, TX': { latitude: 29.7604, longitude: -95.3698 },
      'Phoenix, AZ': { latitude: 33.4484, longitude: -112.0740 },
    };

    const key = `${city}, ${state}`;
    return mockCoordinates[key] || mockCoordinates['New York, NY'];
  },

  async getCurrentLocation(): Promise<Coordinates | null> {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        () => {
          resolve(null);
        }
      );
    });
  }
};