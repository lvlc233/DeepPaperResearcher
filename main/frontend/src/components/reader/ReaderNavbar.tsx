'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { 
  ArrowLeft, 
  Bookmark, 
  Search, 
  Layers, 
  Plus,
  ChevronDown 
} from 'lucide-react';

interface ReaderNavbarProps {
  className?: string;
  title?: string;
  isBookmarked?: boolean;
  onToggleBookmark?: () => void;
  onSearch?: (query: string) => void;
  onViewManage?: () => void;
}

export const ReaderNavbar: React.FC<ReaderNavbarProps> = ({
  className,
  title = "Untitled Paper",
  isBookmarked = false,
  onToggleBookmark,
  onSearch,
  onViewManage,
}) => {
  return (
    <header className={cn(
      "h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 z-50",
      className
    )}>
      {/* Left: Back & Title */}
      <div className="flex items-center gap-4 w-1/4">
        <Link 
          href="/dashboard" 
          className="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          title="返回主页"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-sm font-medium text-gray-900 truncate max-w-[200px]" title={title}>
          {title}
        </h1>
      </div>

      {/* Center: Toolbar */}
      <div className="flex-1 flex items-center justify-center max-w-2xl mx-auto">
        <div className="flex items-center bg-gray-100/50 p-1 rounded-lg border border-gray-200 shadow-sm">
          {/* Search Input */}
          <div className="relative group w-80">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 group-focus-within:text-indigo-500" />
            <input 
              type="text" 
              placeholder="文章内搜索..." 
              className="w-full h-8 pl-8 pr-3 bg-transparent text-xs text-gray-900 placeholder:text-gray-400 focus:outline-none focus:bg-white focus:rounded-md transition-all"
              onChange={(e) => onSearch?.(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center justify-end gap-2 w-1/4">
        <button
          onClick={onToggleBookmark}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all",
            isBookmarked 
              ? "bg-indigo-50 text-indigo-600 border border-indigo-200" 
              : "text-gray-600 hover:bg-gray-100 border border-transparent"
          )}
        >
          <Bookmark className={cn("w-3.5 h-3.5", isBookmarked && "fill-current")} />
          <span>{isBookmarked ? '已收藏' : '收藏'}</span>
        </button>
      </div>
    </header>
  );
};
