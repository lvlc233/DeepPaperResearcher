'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Layers, List, FileText, Eye, EyeOff, Plus, Trash2, MoreHorizontal, Check } from 'lucide-react';
import { Layer } from '@/types/reader';

interface ReaderSidebarProps {
  className?: string;
  isCollapsed?: boolean;
  onNavigate?: (page: number) => void;
  onToggleCollapse?: () => void;
  toc?: any[];
  
  // Layer Management Props
  layers?: Layer[];
  activeViewId?: string;
  onAddLayer?: () => void;
  onDeleteLayer?: (viewId: string) => void;
  onToggleLayerVisibility?: (viewId: string) => void;
  onSetActiveLayer?: (viewId: string) => void;
}

type Tab = 'outline' | 'views';

export const ReaderSidebar: React.FC<ReaderSidebarProps> = ({ 
  className,
  isCollapsed = false,
  onNavigate,
  onToggleCollapse,
  toc = [],
  layers = [],
  activeViewId,
  onAddLayer,
  onDeleteLayer,
  onToggleLayerVisibility,
  onSetActiveLayer
}) => {
  const [activeTab, setActiveTab] = useState<Tab>('views'); // Default to views based on user focus

  if (isCollapsed) return null;

  return (
    <aside className={cn(
      "w-64 bg-white border-r border-gray-200 flex flex-col h-full",
      className
    )}>
      {/* Tabs */}
      <div className="flex p-2 gap-1 border-b border-gray-100">
        <button
          onClick={() => setActiveTab('views')}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 py-1.5 rounded-md text-xs font-medium transition-colors",
            activeTab === 'views' 
              ? "bg-indigo-50 text-indigo-600" 
              : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
          )}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>视图</span>
        </button>
        <button
          onClick={() => setActiveTab('outline')}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 py-1.5 rounded-md text-xs font-medium transition-colors",
            activeTab === 'outline' 
              ? "bg-indigo-50 text-indigo-600" 
              : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
          )}
        >
          <List className="w-3.5 h-3.5" />
          <span>目录</span>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3">
        {activeTab === 'outline' ? (
          <OutlineView onNavigate={onNavigate} />
        ) : (
          <LayersView 
            layers={layers}
            activeViewId={activeViewId}
            onAddLayer={onAddLayer}
            onDeleteLayer={onDeleteLayer}
            onToggleLayerVisibility={onToggleLayerVisibility}
            onSetActiveLayer={onSetActiveLayer}
          />
        )}
      </div>
    </aside>
  );
};

// Mock Outline Component
const OutlineView = ({ onNavigate }: { onNavigate?: (page: number) => void }) => {
  return (
    <div className="space-y-1">
      <div className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">目录 / 缩略图</div>
      {/* Mock Items */}
      {[
        { title: "Abstract", page: 1 },
        { title: "1. Introduction", page: 1 },
        { title: "2. Related Work", page: 2 },
        { title: "3. Methodology", page: 4 },
        { title: "3.1 Data Collection", page: 4 },
        { title: "3.2 Model Architecture", page: 5 },
        { title: "4. Experiments", page: 7 },
        { title: "5. Conclusion", page: 10 },
      ].map((item, idx) => (
        <button 
          key={idx}
          onClick={() => onNavigate?.(item.page)}
          className="w-full text-left px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50 rounded-md truncate transition-colors"
        >
          <span className="mr-2 text-gray-400">{item.page}</span>
          {item.title}
        </button>
      ))}
    </div>
  );
};

// Layers/Views Component
interface LayersViewProps {
  layers: Layer[];
  activeViewId?: string;
  onAddLayer?: () => void;
  onDeleteLayer?: (viewId: string) => void;
  onToggleLayerVisibility?: (viewId: string) => void;
  onSetActiveLayer?: (viewId: string) => void;
}

const LayersView: React.FC<LayersViewProps> = ({
  layers,
  activeViewId,
  onAddLayer,
  onDeleteLayer,
  onToggleLayerVisibility,
  onSetActiveLayer
}) => {
  
  const systemLayers = layers.filter(l => l.type === 'system');
  const userLayers = layers.filter(l => l.type === 'user');

  return (
    <div className="space-y-4">
       {/* Actions */}
       <button 
         onClick={onAddLayer}
         className="w-full flex items-center justify-center gap-2 py-2 border border-dashed border-gray-300 rounded-lg text-xs text-gray-500 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50 transition-all"
       >
         <Plus className="w-3.5 h-3.5" />
         <span>新建长图视图</span>
       </button>

       <div className="space-y-3">
         <div className="text-xs font-medium text-gray-400 uppercase tracking-wider flex items-center justify-between">
            <span>系统视图</span>
         </div>
         
         {systemLayers.map(layer => (
           <div 
             key={layer.view_id} 
             onClick={() => onSetActiveLayer?.(layer.view_id)}
             className={cn(
               "group flex items-center justify-between p-2 rounded-lg border transition-all cursor-pointer",
               activeViewId === layer.view_id ? "bg-indigo-50 border-indigo-200 shadow-sm" : "bg-gray-50 border-gray-200 hover:border-gray-300"
             )}
           >
             <div className="flex items-center gap-2">
               <div className="relative">
                 <FileText className={cn("w-4 h-4", activeViewId === layer.view_id ? "text-indigo-600" : "text-gray-500")} />
                 {activeViewId === layer.view_id && (
                   <div className="absolute -bottom-1 -right-1 bg-indigo-600 rounded-full p-[1px]">
                     <Check className="w-2 h-2 text-white" />
                   </div>
                 )}
               </div>
               <span className={cn("text-xs font-medium", activeViewId === layer.view_id ? "text-indigo-700" : "text-gray-700")}>
                 {layer.name}
               </span>
             </div>
             <button 
                onClick={(e) => { e.stopPropagation(); onToggleLayerVisibility?.(layer.view_id); }}
                className={cn("hover:text-gray-900", layer.visible ? "text-gray-400" : "text-gray-300")}
                title="显隐控制"
             >
               {layer.visible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
             </button>
           </div>
         ))}
       </div>

       <div className="space-y-3">
         <div className="text-xs font-medium text-gray-400 uppercase tracking-wider flex items-center justify-between">
            <span>自定义视图</span>
            <span className="text-[10px] bg-gray-100 px-1.5 py-0.5 rounded-full">{userLayers.length}</span>
         </div>

         <div className="space-y-2">
           {userLayers.map((view) => (
             <div 
               key={view.view_id} 
               onClick={() => onSetActiveLayer?.(view.view_id)}
               className={cn(
                 "group flex items-center justify-between p-2 rounded-lg border transition-all cursor-pointer",
                 activeViewId === view.view_id ? "bg-indigo-50 border-indigo-200 shadow-sm" : "border-transparent hover:bg-gray-50 hover:border-gray-100"
               )}
             >
               <div className="flex items-center gap-2">
                 <div className="relative">
                    <div className={cn("w-2 h-2 rounded-full", view.color || 'bg-gray-400')} />
                    {activeViewId === view.view_id && (
                      <div className="absolute -bottom-1.5 -right-1.5 bg-indigo-600 rounded-full p-[1px] scale-75">
                        <Check className="w-2 h-2 text-white" />
                      </div>
                    )}
                 </div>
                 <span className={cn(
                   "text-xs transition-colors", 
                   !view.visible && "text-gray-400 line-through",
                   activeViewId === view.view_id ? "text-indigo-700 font-medium" : "text-gray-600"
                 )}>
                    {view.name}
                 </span>
               </div>
               <div className="flex items-center gap-1">
                  <button 
                    onClick={(e) => { e.stopPropagation(); onToggleLayerVisibility?.(view.view_id); }}
                    className="p-1 hover:bg-gray-200 rounded text-gray-400 hover:text-gray-600"
                  >
                    {view.visible ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); onDeleteLayer?.(view.view_id); }}
                    className="p-1 hover:bg-red-50 hover:text-red-500 rounded text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
               </div>
             </div>
           ))}
         </div>
       </div>
    </div>
  );
};
