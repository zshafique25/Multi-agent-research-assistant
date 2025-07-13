// frontend/src/services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const submitResearch = async (researchData) => {
  try {
    const response = await api.post('/research', researchData);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to start research. Please try again.'
    );
  }
};

export const getResearchStatus = async (researchId) => {
  try {
    const response = await api.get(`/research/${researchId}`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to get research status. Please try again.'
    );
  }
};

export const getResearchMessages = async (researchId) => {
  try {
    const response = await api.get(`/research/${researchId}/messages`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to get research messages. Please try again.'
    );
  }
};

export default api;