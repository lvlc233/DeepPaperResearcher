'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { UploadCloud, Check } from 'lucide-react';

interface SearchFiltersProps {
  className?: string;
  onUploadClick?: () => void;
}

const FILTERS = [
  { id: 'all', label: '全部' },
  { id: 'title', label: '标题' },
  { id: 'author', label: '作者' },
  { id: 'abstract', label: '摘要' },
  { id: 'year', label: '年份' },
  { id: 'journal', label: '期刊' },
];

export const SearchFilters: React.FC<SearchFiltersProps> = ({ className, onUploadClick }) => {
  const [selectedFilters, setSelectedFilters] = useState<string[]>(['all']);

  const toggleFilter = (id: string) => {
    if (id === 'all') {
      setSelectedFilters(['all']);
      return;
    }
    
    let newFilters = selectedFilters.filter(f => f !== 'all');
    if (selectedFilters.includes(id)) {
      newFilters = newFilters.filter(f => f !== id);
    } else {
      newFilters = [...newFilters, id];
    }
    
    if (newFilters.length === 0) newFilters = ['all'];
    setSelectedFilters(newFilters);
  };

  return (
    <div className={cn("w-full max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 mt-6", className)}>
      {/* Filters List */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {FILTERS.map((filter) => {
          const isSelected = selectedFilters.includes(filter.id);
          return (
            <button
              key={filter.id}
              onClick={() => toggleFilter(filter.id)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 border",
                isSelected 
                  ? "bg-gray-900 text-white border-gray-900 shadow-md" 
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
              )}
            >
              {isSelected && <Check className="w-3 h-3" />}
              {filter.label}
            </button>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button 
          onClick={onUploadClick}
          className="flex items-center gap-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-4 py-2 rounded-lg transition-colors"
        >
          <UploadCloud className="w-4 h-4" />
          <span>上传论文</span>
        </button>
      </div>
    </div>
  );
};
