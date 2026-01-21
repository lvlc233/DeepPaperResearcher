'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';
import { Calendar, FileText, BarChart, Zap, Layers } from 'lucide-react';

interface SearchSettingsProps {
  className?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const SearchSettings: React.FC<SearchSettingsProps> = ({ className, isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className={cn(
      "absolute right-0 top-16 w-80 bg-white rounded-2xl shadow-xl border border-gray-100 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200 origin-top-right",
      className
    )}>
      <div className="p-4 space-y-6">
        
        {/* AI Configuration Section */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-2">
            <Zap className="w-3 h-3" />
            AI 搜索配置
          </h4>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium text-gray-700">深度推理模式</div>
                <div className="text-[10px] text-gray-400">进行多步推理以获取更精准结果</div>
              </div>
              <Switch checked={false} onCheckedChange={() => {}} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm font-medium text-gray-700">自动生成摘要</div>
                <div className="text-[10px] text-gray-400">对搜索结果进行智能总结</div>
              </div>
              <Switch checked={true} onCheckedChange={() => {}} />
            </div>
            
             <div className="space-y-1.5">
                <div className="text-sm font-medium text-gray-700">搜索深度</div>
                <select className="w-full text-sm border-gray-200 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 p-2">
                    <option>标准 (Standard)</option>
                    <option>深入 (Deep)</option>
                    <option>全面 (Comprehensive)</option>
                </select>
            </div>
          </div>
        </div>

        <div className="h-px bg-gray-50" />

        {/* Filter Configuration Section */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-3 h-3" />
            结果过滤
          </h4>

          <div className="space-y-3">
             <div className="space-y-1.5">
                <div className="text-sm font-medium text-gray-700">排序方式</div>
                <div className="grid grid-cols-2 gap-2">
                    <button className="text-xs py-1.5 px-2 bg-indigo-50 text-indigo-600 rounded-md font-medium border border-indigo-100">相关性</button>
                    <button className="text-xs py-1.5 px-2 bg-white text-gray-600 rounded-md border border-gray-200 hover:bg-gray-50">引用量</button>
                    <button className="text-xs py-1.5 px-2 bg-white text-gray-600 rounded-md border border-gray-200 hover:bg-gray-50">最新发表</button>
                    <button className="text-xs py-1.5 px-2 bg-white text-gray-600 rounded-md border border-gray-200 hover:bg-gray-50">影响力</button>
                </div>
            </div>

            <div className="space-y-1.5">
                <div className="text-sm font-medium text-gray-700">发表年份</div>
                <div className="flex items-center gap-2">
                    <input type="number" placeholder="2020" className="w-full text-sm bg-gray-50 border-gray-200 rounded-md p-1.5" />
                    <span className="text-gray-400">-</span>
                    <input type="number" placeholder="2024" className="w-full text-sm bg-gray-50 border-gray-200 rounded-md p-1.5" />
                </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 bg-gray-50 border-t border-gray-100 flex justify-between items-center">
        <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-900">重置</button>
        <button onClick={onClose} className="px-3 py-1.5 bg-gray-900 text-white text-xs font-medium rounded-lg hover:bg-gray-800">
            确认应用
        </button>
      </div>
    </div>
  );
};
