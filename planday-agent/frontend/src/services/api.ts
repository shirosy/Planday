import axios from 'axios';
import { ChatResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatAPI = {
  sendMessage: async (message: string, sessionId: string, image?: File): Promise<ChatResponse> => {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('session_id', sessionId);
    
    if (image) {
      formData.append('image', image);
    }

    const response = await api.post('/api/chat', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  getHistory: async (sessionId: string) => {
    const response = await api.get(`/api/history/${sessionId}`);
    return response.data;
  },

  uploadImage: async (file: File): Promise<{ url: string; description?: string }> => {
    const formData = new FormData();
    formData.append('image', file);

    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
};

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 500) {
      console.error('Server error:', error.response.data);
    } else if (error.code === 'ECONNABORTED') {
      console.error('Request timeout');
    }
    return Promise.reject(error);
  }
);

export default api;