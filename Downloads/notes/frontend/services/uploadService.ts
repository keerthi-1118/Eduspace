// frontend/services/uploadService.ts
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface UploadResponse {
  id: string;
  url: string;
  title: string;
  type: string;
  tags: string[];
  size: string;
  uploadDate: string;
  message?: string;
}

export const uploadFile = async (formData: FormData): Promise<UploadResponse> => {
  try {
    console.log('=== uploadFile called ===');
    console.log('API_URL:', API_URL);
    
    // Get auth token from localStorage if available
    const token = localStorage.getItem('authToken');
    console.log('Auth token:', token ? 'Present' : 'Not found');
    
    const headers: Record<string, string> = {};
    // Don't set Content-Type for FormData - axios will set it automatically with the correct boundary
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    console.log('Uploading file with FormData:', {
      title: formData.get('title'),
      type: formData.get('type'),
      subject: formData.get('subject'),
      hasFile: formData.has('file'),
      hasContent: formData.has('content'),
      content: formData.get('content'),
    });

    console.log('Making POST request to:', `${API_URL}/upload`);
    const response = await axios.post<UploadResponse>(`${API_URL}/upload`, formData, {
      headers,
      timeout: 60000, // 60 second timeout for large files
    });
    console.log('Upload response status:', response.status);
    console.log('Upload response data:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('=== UPLOAD ERROR ===');
    console.error('Error object:', error);
    console.error('Error message:', error.message);
    console.error('Error code:', error.code);
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText,
      config: {
        url: error.config?.url,
        method: error.config?.method,
        headers: error.config?.headers,
      },
    });
    
    if (error.response) {
      // Server responded with error
      const errorMessage = error.response.data?.detail || error.response.data?.message || 'Upload failed';
      console.error('Server error:', errorMessage);
      throw new Error(errorMessage);
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network error: No response from server');
      console.error('Request details:', error.request);
      throw new Error('Network error: Could not connect to server. Please make sure the backend is running on http://localhost:8000');
    } else {
      // Something else happened
      console.error('Unknown error:', error.message);
      throw new Error(`Upload failed: ${error.message}`);
    }
  }
};