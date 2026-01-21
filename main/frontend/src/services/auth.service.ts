import request from '@/lib/request';
import { LoginResponse, TokenPairResponse } from '@/types/api';
import { User } from '@/types/models';

export const authService = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    return request.post('/auth/login', { email, password });
  },

  register: async (email: string, password: string, fullName: string): Promise<User> => {
    return request.post('/auth/register', { email, password, full_name: fullName });
  },

  refreshToken: async (refreshToken: string): Promise<TokenPairResponse> => {
    return request.get('/auth/refresh', { params: { refresh_token: refreshToken } });
  }
};
