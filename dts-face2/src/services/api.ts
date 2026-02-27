import axios from 'axios';

// Define the base URL for the DTS Service API
const API_BASE_URL = '/dts-face2/api'; // Use relative path for proxying via Nginx

// Create an Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000, // Request timeout in milliseconds
});

// Function to fetch system health
export const fetchSystemHealth = async () => {
  try {
    const response = await apiClient.get('/system/health');
    return response.data;
  } catch (error) {
    console.error('Error fetching system health:', error);
    throw error; // Re-throw to be handled by the component
  }
};

// Function to fetch account info
export const fetchAccountInfo = async () => {
  try {
    const response = await apiClient.get('/account/info');
    return response.data;
  } catch (error) {
    console.error('Error fetching account info:', error);
    throw error;
  }
};

// Function to fetch market quotes
export const fetchMarketQuotes = async (symbols: string[]) => {
  if (symbols.length === 0) {
    return [];
  }
  try {
    const symbolString = symbols.join(',');
    const response = await apiClient.get(`/data/quotes?symbols=${symbolString}`);
    // API returns {"quotes": [...]} but we need just the array
    return response.data.quotes || [];
  } catch (error) {
    console.error('Error fetching market quotes:', error);
    throw error;
  }
};

// Optional: Function to fetch symbols if needed, for now we'll hardcode
// export const fetchSymbols = async () => {
//   try {
//     const response = await apiClient.get('/account/symbols');
//     return response.data;
//   } catch (error) {
//     console.error('Error fetching symbols:', error);
//     throw error;
//   }
// };

// Function to fetch deals history
export const fetchDealsHistory = async (days: number = 7) => {
  try {
    // Use /api/account/history as it's public and doesn't require API key
    const response = await apiClient.get(`/account/history?days=${days}`);
    return response.data.deals || [];
  } catch (error) {
    console.error('Error fetching deals history:', error);
    throw error;
  }
};

export default apiClient;
