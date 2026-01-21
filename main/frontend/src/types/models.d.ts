/**
 * Data models matching the backend API documentation v1.1
 * Ref: PROJECT/DOCUMENTS/项目统一技术架构文档(重要).md
 */

export interface User {
  user_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  settings?: any; // Define Settings type if needed
}

export interface Paper {
  paper_id: string;
  title: string;
  url?: string; // Web URL or Proxy URL
  authors: string[];
  summary?: string; // Abstract/Summary
  published_at?: string;
  source: string; // 'arXiv', 'PDF', etc.
  tags: string[];
  references_number?: number;
  // Extra fields that might come from status or other contexts
  status?: 'processing' | 'success' | 'failed'; // From upload response
}

export interface Collection {
  collection_id: string;
  name: string;
  total: number;
}

export interface TocItem {
  title: string;
  page: number;
}

export interface Toc {
  items: TocItem[];
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
  page_index: number;
}

export interface Annotation {
  annotation_id: string;
  type: 'highlight' | 'translation' | 'note';
  rect: Rect;
  content: string;
  color: string;
}

export interface View {
  view_id: string;
  name: string;
  enable: boolean;
  annotations: Annotation[];
}

export interface NoteMeta {
  note_id: string;
  title: string;
  page?: number;
  created_at: string;
}

export interface Note extends NoteMeta {
  content: string; // Markdown
}

export interface MindMapNode {
  id: string;
  text: string;
  type?: string;
  meta?: Record<string, string>;
}

export interface MindMapEdge {
  from_id: string;
  to_id: string;
  label?: string;
}

export interface MindMap {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
}

export interface AISummary {
  summary_config: Record<string, string>;
}

export interface RecordItem {
  record_id: string;
  title: string;
  created_at: string;
  updated_at?: string;
}

export interface Message {
  message_id: string;
  type: 'HUMAN' | 'AI' | 'TOOL_CALL' | 'TOOL_RESPONSE';
  context: string;
  created_at: string;
}

export interface Job {
  job_id: string;
  type: 'toc' | 'summary' | 'mind_map' | 'deep_research' | 'chat';
  status: 'queued' | 'running' | 'blocked' | 'succeeded' | 'failed' | 'canceled' | 'expired';
  progress?: number;
  stage?: string;
  result?: any; // JobResult
  error?: string;
  created_at: string;
  end_at?: string;
}
