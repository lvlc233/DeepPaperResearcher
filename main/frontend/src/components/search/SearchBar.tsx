'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Search, Settings, Sparkles, SlidersHorizontal } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';
import { SearchSettings } from './SearchSettings';

interface SearchBarProps {
  className?: string;
  onSearch?: (query: string, useAI: boolean) => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({ className, onSearch }) => {
  const [query, setQuery] = useState('');
  const [useAI, setUseAI] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setIsSettingsOpen(false);
      }
    };

    if (isSettingsOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isSettingsOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    if (onSearch) {
      onSearch(query, useAI);
    }
  };

  return (
    <div className={cn("w-full max-w-4xl mx-auto relative", className)} ref={settingsRef}>
      <form onSubmit={handleSubmit} className="relative group">
        <div className={cn(
          "flex items-center w-full h-14 pl-6 pr-2 bg-white rounded-2xl border transition-all duration-300 shadow-sm",
          "hover:shadow-md hover:border-indigo-200",
          "focus-within:ring-4 focus-within:ring-indigo-500/10 focus-within:border-indigo-500 focus-within:shadow-xl",
          useAI ? "border-indigo-200 bg-indigo-50/30" : "border-gray-200"
        )}>
          <Search className={cn(
            "w-5 h-5 mr-3 transition-colors duration-300",
            useAI ? "text-indigo-600" : "text-gray-400 group-hover:text-gray-600"
          )} />
          
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={useAI ? "AI 深度搜索中..." : "搜索论文标题、作者、关键词..."}
            className="flex-1 h-full bg-transparent border-none outline-none text-gray-900 placeholder:text-gray-400 text-base"
          />

          {/* Right Actions Group */}
          <div className="flex items-center gap-3 pl-3 border-l border-gray-100">
            {/* AI Toggle */}
            <div className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-300 cursor-pointer select-none",
              useAI ? "bg-indigo-100 text-indigo-700" : "bg-gray-50 text-gray-500 hover:bg-gray-100"
            )} onClick={() => setUseAI(!useAI)}>
              <div className={cn(
                "w-6 h-6 flex items-center justify-center rounded-md transition-all",
                useAI ? "bg-white shadow-sm" : "bg-transparent"
              )}>
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <span className="text-sm font-medium">AI</span>
            </div>

            {/* Settings Button */}
            <button 
              type="button"
              onClick={() => setIsSettingsOpen(!isSettingsOpen)}
              className={cn(
                "p-2 rounded-lg transition-all",
                isSettingsOpen ? "bg-indigo-100 text-indigo-700" : "text-gray-400 hover:text-gray-700 hover:bg-gray-100"
              )}
            >
              <Settings className="w-5 h-5" />
            </button>
            
            {/* Search Button (Optional, mostly enter key) */}
            <button 
              type="submit"
              className="hidden sm:flex h-9 px-4 items-center justify-center bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium rounded-lg transition-all shadow-sm active:scale-95"
            >
              搜索
            </button>
          </div>
        </div>
      </form>

      {/* Search Level Settings Popover */}
      <SearchSettings 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </div>
  );
};
