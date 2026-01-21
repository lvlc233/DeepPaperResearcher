import request from '@/lib/request';
import { CollectionResponse } from '@/types/api';

export const collectionService = {
  getAll: async (): Promise<CollectionResponse[]> => {
    return request.get('/collections');
  },

  getById: async (collectionId: string): Promise<CollectionResponse> => {
    return request.get(`/collections/${collectionId}`);
  },

  create: async (name: string): Promise<CollectionResponse> => {
    return request.post('/collections', { name });
  },

  update: async (collectionId: string, name: string): Promise<void> => {
    return request.patch(`/collections/${collectionId}`, { new_name: name });
  },

  delete: async (collectionId: string): Promise<void> => {
    return request.delete(`/collections/${collectionId}`);
  },

  movePaper: async (collectionId: string, paperId: string): Promise<void> => {
    return request.patch(`/collections/${collectionId}/papers/move/${paperId}`);
  },

  removePaper: async (paperId: string): Promise<void> => {
    return request.delete(`/collections/papers/${paperId}`);
  },
};
