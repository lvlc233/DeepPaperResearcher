import React, { useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  FileText, Download, Copy, ArrowLeft, Loader2, CheckCircle, AlertCircle, Clock, 
  Trash2, PauseCircle, PlayCircle, RotateCcw 
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cn } from '@/lib/utils';

// Mock Data Types
interface ReportItem {
  id: string;
  title: string;
  createTime: string;
  status: 'completed' | 'generating' | 'failed' | 'cancelled';
  content: string;
  summary?: string;
}

// Mock Data
const INITIAL_REPORTS: ReportItem[] = [
  {
    id: '1',
    title: 'DeepPaperResearcher 深度分析报告',
    createTime: '2026-01-11 15:00',
    status: 'completed',
    content: `
# DeepPaperResearcher 论文深度分析报告

## 1. 研究背景
随着学术论文数量的爆炸式增长，科研人员面临着巨大的信息过载压力。传统的文献检索和阅读方式效率低下，难以满足快速获取核心知识的需求。

## 2. 核心方法
本文提出的 **DeepPaperResearcher** 系统，创新性地结合了：

- **多 Agent 协同架构**：将文献调研分解为检索、阅读、总结等子任务。
- **动态知识图谱**：用于捕捉和推理跨文档的潜在关联。
- **自适应评分机制**：根据用户偏好自动筛选高质量论文。

## 3. 实验结果
在包含 10,000 篇计算机科学领域论文的数据集上进行测试，结果显示：

> 相比于单 Agent 系统，本方法的查准率提升了 15%，生成报告的完整性评分提高了 22%。

## 4. 结论与展望
该工作验证了 Agentic Workflow 在学术科研辅助领域的巨大潜力。未来工作将集中在多模态理解（图表分析）和更大规模的知识库构建上。
    `,
    summary: '本文提出了一种基于多 Agent 协同的深度文献调研系统...'
  },
  {
    id: '2',
    title: '相关工作综述 (Related Work)',
    createTime: '2026-01-11 14:30',
    status: 'completed',
    content: `
# 相关工作综述

## 1. 传统文献检索
基于关键词匹配的方法（如 TF-IDF, BM25）在处理语义复杂性时存在局限...

## 2. 神经检索与 RAG
近年来，基于 Embedding 的稠密检索（Dense Retrieval）和检索增强生成（RAG）技术取得了显著进展...

## 3. Agentic Systems
AutoGPT 和 BabyAGI 等自主 Agent 系统的出现，为复杂任务自动化提供了新思路...
    `,
    summary: '对比了传统检索、神经检索与 Agentic Systems 的优劣...'
  },
  {
    id: '3',
    title: '方法论详细拆解',
    createTime: '2026-01-11 15:15',
    status: 'generating',
    content: '',
    summary: '正在分析论文方法论部分的细节实现...'
  }
];

// Status Badge Component
const StatusBadge = ({ status }: { status: ReportItem['status'] }) => {
  switch (status) {
    case 'completed':
      return (
        <span className="flex items-center gap-1 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
          <CheckCircle className="w-3 h-3" />
          完成
        </span>
      );
    case 'generating':
      return (
        <span className="flex items-center gap-1 text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
          <Loader2 className="w-3 h-3 animate-spin" />
          生成中
        </span>
      );
    case 'failed':
      return (
        <span className="flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
          <AlertCircle className="w-3 h-3" />
          失败
        </span>
      );
    case 'cancelled':
      return (
        <span className="flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
          <PauseCircle className="w-3 h-3" />
          已取消
        </span>
      );
  }
};

// Detail View Component
const ReportDetail = ({ report, onBack }: { report: ReportItem; onBack: () => void }) => {
  return (
    <div className="h-full flex flex-col bg-white animate-in slide-in-from-right-10 duration-300 fade-in-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-white sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <button 
            onClick={onBack}
            className="p-1.5 hover:bg-gray-100 rounded-full transition-colors text-gray-600"
            title="返回列表"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="flex flex-col">
            <h3 className="font-semibold text-gray-900 leading-tight">{report.title}</h3>
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" /> {report.createTime}
            </span>
          </div>
        </div>
        
        <div className="flex gap-2">
          {report.status === 'completed' && (
            <>
              <button className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 rounded-md hover:bg-indigo-100 transition-colors">
                <Copy className="w-3.5 h-3.5" />
                复制
              </button>
              <button className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors">
                <Download className="w-3.5 h-3.5" />
                PDF
              </button>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-6">
        {report.status === 'generating' ? (
          <div className="flex flex-col items-center justify-center h-64 gap-4 text-gray-500">
            <div className="relative">
              <div className="w-12 h-12 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-bold text-indigo-600">SSE</span>
              </div>
            </div>
            <p className="text-sm">正在深度研读并生成报告中...</p>
            <div className="w-full max-w-xs bg-gray-100 rounded-full h-1.5 overflow-hidden">
              <div className="h-full bg-indigo-600 rounded-full animate-progress-indeterminate" />
            </div>
          </div>
        ) : report.status === 'cancelled' ? (
          <div className="flex flex-col items-center justify-center h-64 gap-4 text-gray-400">
             <PauseCircle className="w-12 h-12" />
             <p className="text-sm">任务已取消</p>
          </div>
        ) : (
          <article className="prose prose-sm prose-indigo max-w-none">
             <ReactMarkdown>{report.content}</ReactMarkdown>
          </article>
        )}
      </ScrollArea>
    </div>
  );
};

// List View Component
const ReportList = ({ 
  reports, 
  onSelect,
  onDelete,
  onCancel,
  onResume 
}: { 
  reports: ReportItem[];
  onSelect: (report: ReportItem) => void;
  onDelete: (e: React.MouseEvent, id: string) => void;
  onCancel: (e: React.MouseEvent, id: string) => void;
  onResume: (e: React.MouseEvent, id: string) => void;
}) => {
  return (
    <div className="h-full flex flex-col bg-gray-50/50 animate-in slide-in-from-left-10 duration-300 fade-in-50">
      <div className="p-4 border-b border-gray-200 bg-white">
        <h3 className="font-semibold text-gray-900">分析报告</h3>
        <p className="text-xs text-gray-500 mt-1">查看论文的深度研究结果与进度</p>
      </div>

      <div className="flex-1 overflow-auto">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500">
          <div className="col-span-6 pl-2">标题</div>
          <div className="col-span-3">创建时间</div>
          <div className="col-span-2 text-center">状态</div>
          <div className="col-span-1 text-center">操作</div>
        </div>

        {/* List Items */}
        <div className="divide-y divide-gray-100">
          {reports.map((report) => (
            <div 
              key={report.id}
              onClick={() => onSelect(report)}
              className="grid grid-cols-12 gap-4 px-4 py-3 hover:bg-indigo-50/50 cursor-pointer transition-all group items-center bg-white"
            >
              <div className="col-span-6 flex flex-col pl-2">
                <span className="text-sm font-medium text-gray-900 group-hover:text-indigo-700 transition-colors truncate">
                  {report.title}
                </span>
                {report.summary && (
                  <span className="text-xs text-gray-400 truncate mt-0.5">
                    {report.summary}
                  </span>
                )}
              </div>
              <div className="col-span-3 text-xs text-gray-500 flex items-center">
                {report.createTime}
              </div>
              <div className="col-span-2 flex justify-center">
                <StatusBadge status={report.status} />
              </div>
              <div className="col-span-1 flex justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {/* Action Buttons */}
                {report.status === 'generating' && (
                  <button 
                    onClick={(e) => onCancel(e, report.id)}
                    className="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded-md transition-colors"
                    title="取消生成"
                  >
                    <PauseCircle className="w-3.5 h-3.5" />
                  </button>
                )}
                {(report.status === 'cancelled' || report.status === 'failed') && (
                  <button 
                    onClick={(e) => onResume(e, report.id)}
                    className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                    title="恢复生成"
                  >
                    {report.status === 'failed' ? <RotateCcw className="w-3.5 h-3.5" /> : <PlayCircle className="w-3.5 h-3.5" />}
                  </button>
                )}
                <button 
                  onClick={(e) => onDelete(e, report.id)}
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  title="删除报告"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
          {reports.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <FileText className="w-10 h-10 mb-2 opacity-20" />
              <p className="text-sm">暂无报告</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

interface ReportTabProps {
  paperId: string;
}

export const ReportTab: React.FC<ReportTabProps> = ({ paperId }) => {
  const [reports, setReports] = useState<ReportItem[]>(INITIAL_REPORTS);
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm('确定要删除这份报告吗？')) {
      setReports(prev => prev.filter(item => item.id !== id));
      if (selectedReport?.id === id) {
        setSelectedReport(null);
      }
    }
  };

  const handleCancel = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setReports(prev => prev.map(item => 
      item.id === id ? { ...item, status: 'cancelled' } : item
    ));
  };

  const handleResume = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setReports(prev => prev.map(item => 
      item.id === id ? { ...item, status: 'generating' } : item
    ));
  };

  // Update selected report if it changes in the list (e.g. status change)
  const currentSelectedReport = reports.find(r => r.id === selectedReport?.id);

  if (currentSelectedReport) {
    return (
      <ReportDetail 
        report={currentSelectedReport} 
        onBack={() => setSelectedReport(null)} 
      />
    );
  }

  return (
    <ReportList 
      reports={reports} 
      onSelect={setSelectedReport}
      onDelete={handleDelete}
      onCancel={handleCancel}
      onResume={handleResume}
    />
  );
};
