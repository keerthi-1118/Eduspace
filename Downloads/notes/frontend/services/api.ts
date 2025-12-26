import axios from 'axios';
import { Resource } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Get auth token helper
const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken');
};

// Axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface UploadProgressCallback {
  (progressEvent: ProgressEvent): void;
}

export const uploadFile = async (
  formData: FormData, 
  onUploadProgress?: UploadProgressCallback
) => {
  const token = getAuthToken();
  const config = {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    onUploadProgress,
  };

  const response = await axios.post(`${API_BASE_URL}/upload`, formData, config);
  return response;
};

export const generateSummary = async (text: string, resourceId?: number): Promise<string> => {
  try {
    const response = await apiClient.post('/summarize', { text, resourceId });
    return response.data.summary;
  } catch (error: any) {
    console.error('Error generating summary:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to generate summary');
    }
    throw error;
  }
};

export const getNotes = async (): Promise<any[]> => {
  try {
    const response = await apiClient.get('/notes');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching notes:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to fetch notes');
    }
    throw error;
  }
};

export const createNote = async (note: any): Promise<any> => {
  try {
    const response = await apiClient.post('/notes', note);
    return response.data;
  } catch (error: any) {
    console.error('Error creating note:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to create note');
    }
    throw error;
  }
};

export const deleteNote = async (noteId: number): Promise<void> => {
  try {
    await apiClient.delete(`/notes/${noteId}`);
  } catch (error: any) {
    console.error('Error deleting note:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to delete note');
    }
    throw error;
  }
};

export const rateResource = async (resourceId: number, rating: number): Promise<void> => {
  try {
    await apiClient.post('/rate', { resourceId, rating });
  } catch (error: any) {
    console.error('Error rating resource:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to rate resource');
    }
    throw error;
  }
};

export const searchResources = async (query: string): Promise<Resource[]> => {
  try {
    const response = await apiClient.get('/search', {
      params: { q: query }
    });
    return response.data;
  } catch (error: any) {
    console.error('Error searching resources:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to search resources');
    }
    throw error;
  }
};

// Projects API
export const getProjects = async (): Promise<any[]> => {
  try {
    const response = await apiClient.get('/projects');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching projects:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to fetch projects');
    }
    throw error;
  }
};

export const createProject = async (project: any): Promise<any> => {
  try {
    const response = await apiClient.post('/projects', project);
    return response.data;
  } catch (error: any) {
    console.error('Error creating project:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to create project');
    }
    throw error;
  }
};

export const deleteProject = async (projectId: number): Promise<void> => {
  try {
    await apiClient.delete(`/projects/${projectId}`);
  } catch (error: any) {
    console.error('Error deleting project:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to delete project');
    }
    throw error;
  }
};

export const searchProjects = async (query: string): Promise<any[]> => {
  try {
    const response = await apiClient.get('/projects/search', {
      params: { q: query }
    });
    return response.data;
  } catch (error: any) {
    console.error('Error searching projects:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to search projects');
    }
    throw error;
  }
};

// Tasks API
export const getTasks = async (): Promise<any[]> => {
  try {
    const response = await apiClient.get('/tasks');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching tasks:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to fetch tasks');
    }
    throw error;
  }
};

export const createTask = async (task: any): Promise<any> => {
  try {
    const response = await apiClient.post('/tasks', task);
    return response.data;
  } catch (error: any) {
    console.error('Error creating task:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to create task');
    }
    throw error;
  }
};

export const deleteTask = async (taskId: number): Promise<void> => {
  try {
    await apiClient.delete(`/tasks/${taskId}`);
  } catch (error: any) {
    console.error('Error deleting task:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to delete task');
    }
    throw error;
  }
};

export const searchTasks = async (query: string): Promise<any[]> => {
  try {
    const response = await apiClient.get('/tasks/search', {
      params: { q: query }
    });
    return response.data;
  } catch (error: any) {
    console.error('Error searching tasks:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to search tasks');
    }
    throw error;
  }
};

export const updateTask = async (taskId: number, task: any): Promise<any> => {
  try {
    const response = await apiClient.put(`/tasks/${taskId}`, task);
    return response.data;
  } catch (error: any) {
    console.error('Error updating task:', error);
    if (error.response) {
      throw new Error(error.response.data.detail || 'Failed to update task');
    }
    throw error;
  }
};

// Collaboration API
export const getProjectMembers = async (projectId: number): Promise<any[]> => {
  try {
    const response = await apiClient.get(`/collaboration/projects/${projectId}/members`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching project members:', error);
    throw error;
  }
};

export const addProjectMember = async (projectId: number, member: any): Promise<any> => {
  try {
    const response = await apiClient.post(`/collaboration/projects/${projectId}/members`, member);
    return response.data;
  } catch (error: any) {
    console.error('Error adding project member:', error);
    throw error;
  }
};

export const updateMemberRole = async (projectId: number, memberId: number, role: string): Promise<any> => {
  try {
    const response = await apiClient.put(`/collaboration/projects/${projectId}/members/${memberId}`, { role });
    return response.data;
  } catch (error: any) {
    console.error('Error updating member role:', error);
    throw error;
  }
};

export const removeProjectMember = async (projectId: number, memberId: number): Promise<void> => {
  try {
    await apiClient.delete(`/collaboration/projects/${projectId}/members/${memberId}`);
  } catch (error: any) {
    console.error('Error removing project member:', error);
    throw error;
  }
};

export const createProjectInvite = async (projectId: number, invite: any): Promise<any> => {
  try {
    const response = await apiClient.post(`/collaboration/projects/${projectId}/invites`, invite);
    return response.data;
  } catch (error: any) {
    console.error('Error creating project invite:', error);
    throw error;
  }
};

export const getProjectInvites = async (projectId: number): Promise<any[]> => {
  try {
    const response = await apiClient.get(`/collaboration/projects/${projectId}/invites`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching project invites:', error);
    throw error;
  }
};

export const acceptInvite = async (token: string): Promise<any> => {
  try {
    const response = await apiClient.post(`/collaboration/invites/${token}/accept`);
    return response.data;
  } catch (error: any) {
    console.error('Error accepting invite:', error);
    throw error;
  }
};

export const deleteInvite = async (inviteId: number): Promise<void> => {
  try {
    await apiClient.delete(`/collaboration/invites/${inviteId}`);
  } catch (error: any) {
    console.error('Error deleting invite:', error);
    throw error;
  }
};

// Project Files API
export const getProjectFiles = async (projectId: number): Promise<any[]> => {
  try {
    const response = await apiClient.get(`/projects/${projectId}/files`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching project files:', error);
    throw error;
  }
};

export const createProjectFile = async (projectId: number, file: any): Promise<any> => {
  try {
    const response = await apiClient.post(`/projects/${projectId}/files`, file);
    return response.data;
  } catch (error: any) {
    console.error('Error creating project file:', error);
    throw error;
  }
};

export const getProjectFile = async (projectId: number, fileId: number): Promise<any> => {
  try {
    const response = await apiClient.get(`/projects/${projectId}/files/${fileId}`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching project file:', error);
    throw error;
  }
};

export const updateProjectFile = async (projectId: number, fileId: number, file: any): Promise<any> => {
  try {
    const response = await apiClient.put(`/projects/${projectId}/files/${fileId}`, file);
    return response.data;
  } catch (error: any) {
    console.error('Error updating project file:', error);
    throw error;
  }
};

export const deleteProjectFile = async (projectId: number, fileId: number): Promise<void> => {
  try {
    await apiClient.delete(`/projects/${projectId}/files/${fileId}`);
  } catch (error: any) {
    console.error('Error deleting project file:', error);
    throw error;
  }
};

export const getFileVersions = async (projectId: number, fileId: number): Promise<any[]> => {
  try {
    const response = await apiClient.get(`/projects/${projectId}/files/${fileId}/versions`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching file versions:', error);
    throw error;
  }
};

export const restoreFileVersion = async (projectId: number, fileId: number, versionId: number): Promise<any> => {
  try {
    const response = await apiClient.post(`/projects/${projectId}/files/${fileId}/versions/${versionId}/restore`);
    return response.data;
  } catch (error: any) {
    console.error('Error restoring file version:', error);
    throw error;
  }
};

export const createProjectVersion = async (projectId: number, version: any): Promise<any> => {
  try {
    const response = await apiClient.post(`/projects/${projectId}/versions`, version);
    return response.data;
  } catch (error: any) {
    console.error('Error creating project version:', error);
    throw error;
  }
};

export const getProjectVersions = async (projectId: number): Promise<any[]> => {
  try {
    const response = await apiClient.get(`/projects/${projectId}/versions`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching project versions:', error);
    throw error;
  }
};

export const restoreProjectVersion = async (projectId: number, versionId: number): Promise<void> => {
  try {
    await apiClient.post(`/projects/${projectId}/versions/${versionId}/restore`);
  } catch (error: any) {
    console.error('Error restoring project version:', error);
    throw error;
  }
};

// Chat API
export const getChatMessages = async (projectId: number, limit: number = 100): Promise<any[]> => {
  try {
    const response = await apiClient.get(`/projects/${projectId}/chat`, {
      params: { limit }
    });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching chat messages:', error);
    throw error;
  }
};

export const sendChatMessage = async (projectId: number, message: string): Promise<any> => {
  try {
    const response = await apiClient.post(`/projects/${projectId}/chat`, { message });
    return response.data;
  } catch (error: any) {
    console.error('Error sending chat message:', error);
    throw error;
  }
};

export const deleteChatMessage = async (projectId: number, messageId: number): Promise<void> => {
  try {
    await apiClient.delete(`/projects/${projectId}/chat/${messageId}`);
  } catch (error: any) {
    console.error('Error deleting chat message:', error);
    throw error;
  }
};

// AI API
export const aiMentor = async (prompt: string, projectId?: number, contextFiles?: string[]): Promise<any> => {
  try {
    const response = await apiClient.post('/ai/mentor', {
      prompt,
      project_id: projectId,
      context_files: contextFiles
    });
    return response.data;
  } catch (error: any) {
    console.error('Error calling AI mentor:', error);
    throw error;
  }
};

export const aiSummarize = async (text?: string, resourceId?: number, resourceType?: string): Promise<any> => {
  try {
    const response = await apiClient.post('/ai/summarize', {
      text,
      resource_id: resourceId,
      resource_type: resourceType
    });
    return response.data;
  } catch (error: any) {
    console.error('Error calling AI summarizer:', error);
    throw error;
  }
};

export const aiStudyFlow = async (noteId: number, format: string = 'summary'): Promise<any> => {
  try {
    const response = await apiClient.post('/ai/studyflow', {
      note_id: noteId,
      format
    });
    return response.data;
  } catch (error: any) {
    console.error('Error calling AI StudyFlow:', error);
    throw error;
  }
};

export const aiResourceFinder = async (query: string, projectId?: number): Promise<any> => {
  try {
    const response = await apiClient.post('/ai/resource-finder', {
      query,
      project_id: projectId
    });
    return response.data;
  } catch (error: any) {
    console.error('Error calling AI resource finder:', error);
    throw error;
  }
};

// Analytics API
export const getProgressAnalytics = async (projectId: number): Promise<any> => {
  try {
    const response = await apiClient.get(`/analytics/projects/${projectId}/progress`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching progress analytics:', error);
    throw error;
  }
};

export const getWeeklyReport = async (projectId: number): Promise<any> => {
  try {
    const response = await apiClient.get(`/analytics/projects/${projectId}/weekly-report`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching weekly report:', error);
    throw error;
  }
};

export const getProjectTimeline = async (projectId: number, limit: number = 50): Promise<any> => {
  try {
    const response = await apiClient.get(`/analytics/projects/${projectId}/timeline`, {
      params: { limit }
    });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching project timeline:', error);
    throw error;
  }
};
