import request from '@/lib/request';
import { 
  PaperReaderMetaResponse, TocResponse, ViewResponse, AnnotationResponse, 
  NoteMetaResponse, NoteResponse, AISummaryResponse, MindMapResponse, 
  RecordResponse, MessageResponse, Annotation
} from '@/types/api';
import { View } from '@/types/models';

export const readerService = {
  getMeta: async (paperId: string): Promise<PaperReaderMetaResponse> => {
    return request.get(`/papers/${paperId}/meta`);
  },

  getToc: async (paperId: string): Promise<TocResponse> => {
    return request.get(`/papers/${paperId}/toc`);
  },

  // Views
  getViews: async (paperId: string): Promise<ViewResponse[]> => {
    return request.get(`/papers/${paperId}/views`);
  },

  createView: async (paperId: string, name: string): Promise<ViewResponse> => {
    return request.post(`/papers/${paperId}/views`, { name });
  },

  updateView: async (paperId: string, viewId: string, enable: boolean): Promise<void> => {
    return request.patch(`/papers/${paperId}/views/${viewId}/enable`, { enable });
  },

  renameView: async (paperId: string, viewId: string, name: string): Promise<void> => {
    return request.patch(`/papers/${paperId}/views/${viewId}/rename`, { name });
  },

  deleteView: async (paperId: string, viewId: string): Promise<void> => {
    return request.delete(`/papers/${paperId}/views/${viewId}`);
  },

  // Annotations
  getAnnotations: async (paperId: string, viewId: string): Promise<AnnotationResponse> => {
    return request.get(`/papers/${paperId}/views/${viewId}/annotations`);
  },

  addAnnotation: async (paperId: string, viewId: string, data: Omit<Annotation, 'annotation_id'>): Promise<void> => {
    return request.post(`/papers/${paperId}/views/${viewId}/annotations`, data);
  },

  updateAnnotation: async (paperId: string, viewId: string, annotationId: string, data: Omit<Annotation, 'annotation_id'>): Promise<void> => {
    return request.put(`/papers/${paperId}/views/${viewId}/annotations/${annotationId}`, data);
  },

  deleteAnnotation: async (paperId: string, viewId: string, annotationId: string): Promise<void> => {
    return request.delete(`/papers/${paperId}/views/${viewId}/annotations/${annotationId}`);
  },

  // Notes
  getNotes: async (paperId: string): Promise<NoteMetaResponse> => {
    return request.get(`/papers/${paperId}/notes`);
  },

  getNote: async (paperId: string, noteId: string): Promise<NoteResponse> => {
    return request.get(`/papers/${paperId}/notes/${noteId}`);
  },

  // AI
  getSummary: async (paperId: string): Promise<AISummaryResponse> => {
    return request.get(`/papers/${paperId}/ai/summary`);
  },

  getMindMap: async (paperId: string): Promise<MindMapResponse> => {
    return request.get(`/papers/${paperId}/ai/mind_map`);
  },

  getHistory: async (paperId: string): Promise<RecordResponse[]> => {
    return request.get(`/papers/${paperId}/ai/history`);
  },

  getRecord: async (paperId: string, recordId: string): Promise<MessageResponse> => {
    return request.get(`/papers/${paperId}/ai/record/${recordId}`);
  }
};
