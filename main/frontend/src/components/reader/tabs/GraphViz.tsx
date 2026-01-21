'use client';

import React, { useRef, useEffect } from 'react';
import { GraphCanvas, GraphNode, GraphEdge, GraphCanvasRef } from 'reagraph';
import { RotateCcw, Focus } from 'lucide-react';

// ----------------------------------------------------------------------
// Mock Data
// ----------------------------------------------------------------------

const MOCK_NODES: GraphNode[] = [
  { id: '1', label: 'DeepPaperResearcher', fill: '#4F46E5', size: 25 }, 
  { id: '2', label: 'LLM', fill: '#8B5CF6', size: 15 },
  { id: '3', label: 'Knowledge Graph', fill: '#EC4899', size: 15 }, 
  { id: '4', label: 'Multi-Agent', fill: '#10B981', size: 15 }, 
  { id: '5', label: 'RAG', fill: '#F59E0B', size: 15 }, 
  { id: '6', label: 'Citation Analysis', fill: '#6366F1' },
  { id: '7', label: 'Summarization', fill: '#6366F1' },
  { id: '8', label: 'Q&A System', fill: '#6366F1' },
];

const MOCK_EDGES: GraphEdge[] = [
  { id: 'e1-2', source: '1', target: '2', label: 'uses' },
  { id: 'e1-3', source: '1', target: '3', label: 'builds' },
  { id: 'e1-4', source: '1', target: '4', label: 'employs' },
  { id: 'e2-5', source: '2', target: '5', label: 'enhances' },
  { id: 'e3-5', source: '3', target: '5', label: 'supports' },
  { id: 'e1-6', source: '1', target: '6', label: 'performs' },
  { id: 'e4-7', source: '4', target: '7', label: 'generates' },
  { id: 'e4-8', source: '4', target: '8', label: 'enables' },
];

// ----------------------------------------------------------------------
// Component
// ----------------------------------------------------------------------

interface GraphVizProps {
  paperId: string;
}

export default function GraphViz({ paperId }: GraphVizProps) {
  // 使用 useRef 确保容器引用
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<GraphCanvasRef | null>(null);

  const handleReset = () => {
    if (graphRef.current) {
      graphRef.current.centerGraph();
    }
  };

  const handleFit = () => {
    if (graphRef.current) {
      graphRef.current.fitNodesInView();
    }
  };

  return (
    <div 
      ref={containerRef}
      className="w-full h-full relative bg-gray-50"
      style={{ minHeight: '400px' }} // 确保最小高度，防止塌缩
    >
      <GraphCanvas
        ref={graphRef}
        nodes={MOCK_NODES}
        edges={MOCK_EDGES}
        layoutType="forceDirected2d"
        labelType="all"
        sizingType="centrality"
        cameraMode="rotate"
        // 显式设置背景透明，以便看到底色
        theme={{
          canvas: { background: 'transparent' },
          node: { 
            fill: '#4F46E5',
            activeFill: '#4338ca',
            opacity: 1,
            selectedOpacity: 1,
            inactiveOpacity: 0.2,
            label: { color: '#1f2937', stroke: '#ffffff', activeColor: '#1f2937' }
          },
          edge: { 
            fill: '#94a3b8',
            activeFill: '#64748b',
            opacity: 1,
            selectedOpacity: 1,
            inactiveOpacity: 0.2,
            label: { color: '#64748b', stroke: '#ffffff', activeColor: '#64748b' }
          },
          arrow: { fill: '#94a3b8', activeFill: '#64748b' },
          ring: { fill: '#818cf8', activeFill: '#4f46e5' },
          lasso: { 
            border: '1px solid #5c5c5c', 
            background: 'rgba(75, 160, 255, 0.1)' 
          }
        }}
      />
      
      {/* 简单的悬浮统计 */}
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur px-3 py-1.5 rounded-full shadow-sm border border-gray-200 text-xs font-medium text-gray-600">
        {MOCK_NODES.length} Nodes · {MOCK_EDGES.length} Edges
      </div>

      {/* 控制按钮组 */}
      <div className="absolute top-4 right-4 flex gap-2">
        <button
          onClick={handleFit}
          className="p-2 bg-white/90 backdrop-blur rounded-lg shadow-sm border border-gray-200 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
          title="适应视图"
        >
          <Focus className="w-4 h-4" />
        </button>
        <button
          onClick={handleReset}
          className="p-2 bg-white/90 backdrop-blur rounded-lg shadow-sm border border-gray-200 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
          title="重置视角"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
