import request from '@/lib/request';
import { PapersUploadResponse, PaperReaderMetaResponse, JobListResponse, JobResponse, SearchedPaperMetaResponse } from '@/types/api';
import { Paper, Job } from '@/types/models';

export const paperService = {
  uploadLocal: async (files: File[], collectionId?: string): Promise<PapersUploadResponse[]> => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    if (collectionId) {
      formData.append('collection_id', collectionId);
    }
    return request.post('/papers/upload/local', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  uploadWeb: async (urls: string[], collectionId?: string): Promise<PapersUploadResponse[]> => {
    return request.post('/papers/upload/web', { urls, collection_id: collectionId });
  },

  // Get list of papers from backend
  getList: async (page = 1, limit = 10): Promise<Paper[]> => {
     const offset = (page - 1) * limit;
     const items: any[] = await request.get('/papers/list', { 
        params: { limit, offset } 
    });

    return items.map(item => ({
         paper_id: item.paper_id,
          title: item.title,
          url: item.file_url,
          authors: item.authors || [],
          summary: item.abstract,
          published_at: item.created_at,
          source: 'Upload',
          tags: [],
          status: item.status === 'completed' ? 'success' : (item.status === 'pending' ? 'processing' : item.status)
      }));
  },

  getMeta: async (paperId: string): Promise<PaperReaderMetaResponse> => {
    return request.get(`/papers/${paperId}/meta`);
  },

  getJobs: async (paperId: string): Promise<JobListResponse> => {
    return request.get(`/papers/${paperId}/jobs`);
  },

  createJob: async (paperId: string, type: Job['type'], options?: any): Promise<JobResponse> => {
    return request.post(`/papers/${paperId}/jobs`, { type, options });
  },

  getJob: async (jobId: string): Promise<JobResponse> => {
    return request.get(`/jobs/${jobId}`);
  },
};
