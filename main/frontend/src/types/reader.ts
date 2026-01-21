export type AnnotationType = 'highlight' | 'note' | 'translate';

export interface Rect {
  x: number; // Percentage 0-100
  y: number; // Percentage 0-100
  width: number; // Percentage 0-100
  height: number; // Percentage 0-100
  pageIndex: number; // 0-based index
}

export interface Annotation {
  annotation_id: string;
  type: AnnotationType;
  rects: Rect[]; // Support multi-line highlights
  content?: string; // For notes or translation
  color?: string;
  createdAt: number;
}

export interface Layer {
  view_id: string;
  name: string;
  type: 'system' | 'user';
  visible: boolean;
  annotations: Annotation[];
  color?: string; // Representative color for the layer
}
