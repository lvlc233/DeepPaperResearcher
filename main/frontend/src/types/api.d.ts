import { User, Paper, Collection, View, Annotation, NoteMeta, Note, MindMap, AISummary, RecordItem, Message, Job, TocItem } from './models';

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// Auth
export interface LoginResponse extends User {
  access_token: string;
  refresh_token?: string;
  settings?: any;
}

export interface TokenPairResponse {
  access_token: string;
  refresh_token?: string;
}

// Papers
export interface PapersUploadResponse {
  paper_id: string;
  title: string;
  status: 'processing' | 'success' | 'failed';
}

export interface SearchedPaperMetaResponse {
  items: Paper[];
  total: number;
}

export interface PaperReaderMetaResponse {
  paper_id: string;
  url: string;
  summary?: AISummary;
  toc?: { items: TocItem[] };
  views: View[];
  notes: NoteMeta[];
  mind_map?: MindMap;
  history: RecordItem[];
  jobs: Job[];
}

// Collections
export interface CollectionResponse extends Collection {}

// Views
export interface ViewResponse {
  view_id: string;
  name: string;
  enable: boolean;
}

export interface AnnotationResponse {
  items: Annotation[];
}

// Notes
export interface NoteMetaResponse {
  items: NoteMeta[];
}

export interface NoteResponse extends Note {}

// AI
export interface AISummaryResponse extends AISummary {}
export interface MindMapResponse extends MindMap {}
export interface RecordResponse extends RecordItem {}
export interface MessageResponse {
  items: Message[];
}
export interface JobListResponse {
  items: Job[];
}
export interface JobResponse {
  job: Job;
}
