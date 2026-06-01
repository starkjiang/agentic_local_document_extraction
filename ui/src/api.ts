import axios from 'axios';
import type { HealthStatus } from './types';

const API_URL = 'http://localhost:8000';

export const api = {
  getHealth: () => axios.get<HealthStatus>(`${API_URL}/health`).then(r => r.data),
  
  uploadPDF: (file: File, strategy: string = 'auto') => {
    const form = new FormData();
    form.append('file', file);
    return axios.post(`${API_URL}/extract?strategy=${strategy}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data);
  },
  
  getStatus: (jobId: string) => axios.get(`${API_URL}/status/${jobId}`).then(r => r.data),
  
  getMarkdown: (jobId: string) => axios.get(`${API_URL}/result/${jobId}/markdown`).then(r => r.data.markdown),
  
  getJSON: (jobId: string) => axios.get(`${API_URL}/result/${jobId}/json`).then(r => r.data),
  
  search: (query: string, nResults: number = 5) => 
    axios.post(`${API_URL}/query`, { query, n_results: nResults }).then(r => r.data.results),
  
  listJobs: () => axios.get(`${API_URL}/jobs`).then(r => r.data.jobs),
  
  deleteJob: (jobId: string) => axios.delete(`${API_URL}/jobs/${jobId}`),
};
