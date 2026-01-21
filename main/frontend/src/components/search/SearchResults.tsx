'use client';

import React from 'react';
import { FileText, User, Calendar, ExternalLink, Download, MoreHorizontal, Bookmark, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Paper } from '@/types/models';

interface SearchResultsProps {
  results: Paper[];
  className?: string;
  onToggleBookmark?: (id: string) => void;
  aiEnabled?: boolean;
}

export const SearchResults: React.FC<SearchResultsProps> = ({ results, className, onToggleBookmark, aiEnabled }) => {
  const router = useRouter();

  const handleOpenPaper = React.useCallback(
    (paperId: string) => {
      router.push(`/reader/${paperId}`);
    },
    [router]
  );

  if (!results || results.length === 0) return null;

  return (
    <div className={cn("w-full max-w-5xl animate-in fade-in slide-in-from-bottom-8 duration-700", className)}>
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 p-4 bg-gray-50/50 border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          <div className="col-span-6 pl-2">论文标题 / 摘要</div>
          <div className="col-span-3">作者</div>
          <div className="col-span-1 text-center">年份 / 评分</div>
          <div className="col-span-2 text-right pr-2">来源</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-gray-50">
          {results.map((paper) => (
            <div 
              key={paper.paper_id} 
              className="grid grid-cols-12 gap-4 p-4 hover:bg-gray-50/50 transition-colors group cursor-pointer"
              onClick={() => handleOpenPaper(paper.paper_id)}
            >
              {/* Title & Abstract Column */}
              <div className="col-span-6 pl-2">
                <div className="flex items-start gap-3">
                  <div className="mt-1 p-2 bg-indigo-50 text-indigo-600 rounded-lg flex-shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-gray-900 leading-tight group-hover:text-indigo-600 transition-colors">
                        {paper.title}
                      </h3>
                      {aiEnabled && paper.aiScore && (
                        <span className={cn(
                          "px-1.5 py-0.5 rounded text-[10px] font-bold border",
                          paper.aiScore >= 90 ? "bg-green-50 text-green-700 border-green-200" :
                          paper.aiScore >= 80 ? "bg-blue-50 text-blue-700 border-blue-200" :
                          "bg-yellow-50 text-yellow-700 border-yellow-200"
                        )}>
                          AI {paper.aiScore}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
                      {paper.abstract || "暂无摘要..."}
                    </p>
                    
                    {/* AI Reason Box */}
                    {aiEnabled && paper.aiReason && (
                      <div className="mt-2 p-2 bg-indigo-50/50 border border-indigo-100 rounded-md">
                         <div className="flex items-start gap-1.5">
                            <Sparkles className="w-3 h-3 text-indigo-500 mt-0.5 flex-shrink-0" />
                            <p className="text-xs text-indigo-700 leading-relaxed font-medium">
                              推荐理由: <span className="font-normal text-indigo-600">{paper.aiReason}</span>
                            </p>
                         </div>
                      </div>
                    )}

                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-[10px] px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">
                        引用: {paper.citations || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Authors Column */}
              <div className="col-span-3">
                <div className="flex flex-col gap-1">
                  {paper.authors.slice(0, 2).map((author, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-xs text-gray-600">
                      <User className="w-3 h-3 text-gray-400" />
                      <span className="truncate">{author}</span>
                    </div>
                  ))}
                  {paper.authors.length > 2 && (
                    <span className="text-xs text-gray-400 pl-4.5">+{paper.authors.length - 2} 位作者</span>
                  )}
                </div>
              </div>

              {/* Year Column */}
              <div className="col-span-1 flex items-start justify-center">
                <span className="text-xs font-medium text-gray-500 bg-gray-50 px-2 py-1 rounded-md border border-gray-100">
                  {paper.year}
                </span>
              </div>

              {/* Source & Actions Column */}
              <div className="col-span-2 flex flex-col items-end gap-2 pr-2">
                <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                  {paper.source}
                </span>
                
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleBookmark?.(paper.id);
                    }}
                    className={cn(
                      "p-1.5 rounded-md transition-colors",
                      paper.is_bookmarked 
                        ? "text-indigo-600 bg-indigo-50 hover:bg-indigo-100" 
                        : "text-gray-400 hover:text-gray-900 hover:bg-gray-100"
                    )}
                    title={paper.is_bookmarked ? "取消收藏" : "收藏"}
                  >
                    <Bookmark className={cn("w-3.5 h-3.5", paper.is_bookmarked && "fill-current")} />
                  </button>
                   <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenPaper(paper.id);
                    }}
                    className="p-1.5 text-gray-400 hover:text-gray-900 hover:bg-gray-100 rounded-md"
                    title="查看详情"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                  <button className="p-1.5 text-gray-400 hover:text-gray-900 hover:bg-gray-100 rounded-md" title="下载 PDF">
                    <Download className="w-3.5 h-3.5" />
                  </button>
                  <button className="p-1.5 text-gray-400 hover:text-gray-900 hover:bg-gray-100 rounded-md">
                    <MoreHorizontal className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Footer / Pagination Placeholder */}
        <div className="p-3 border-t border-gray-100 bg-gray-50/30 text-center text-xs text-gray-400">
          显示 {results.length} 条结果
        </div>
      </div>
    </div>
  );
};
