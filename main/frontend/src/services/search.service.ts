import request from '@/lib/request';
import { SearchedPaperMetaResponse } from '@/types/api';

export interface SearchParams {
  query: string;
  page: number;
  limit: number;
}

export const searchService = {
  search: async (params: SearchParams): Promise<SearchedPaperMetaResponse> => {
    return request.post('/search', params);
  },
};
