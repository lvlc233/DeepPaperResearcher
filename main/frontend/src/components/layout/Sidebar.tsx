'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  Search, 
  FolderOpen, 
  Settings, 
  ChevronRight, 
  ChevronLeft, 
  BookOpen,
  Plus,
  MoreVertical,
  Trash2,
  Edit2,
  X,
  Check
} from 'lucide-react';
import * as Popover from '@radix-ui/react-popover';

import { collectionService } from '@/services/collection.service';
import { toast } from 'sonner';
import { logger } from '@/lib/logger';

interface SidebarProps {
  className?: string;
  onSettingsClick?: () => void;
  onSelectCollection?: (collection: Collection | null) => void;
  collections?: Collection[];
  activeCollectionId?: string | null;
  onRefresh?: () => void;
}

export interface Collection {
  id: string;
  label: string;
  count: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  className, 
  onSettingsClick, 
  onSelectCollection,
  collections: propCollections,
  activeCollectionId,
  onRefresh
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();
  // Local state is only a fallback or for optimistic UI, but mainly we rely on props now
  const [collections, setCollections] = useState<Collection[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  // Sync with props
  React.useEffect(() => {
    if (propCollections) {
      setCollections(propCollections);
    }
  }, [propCollections]);

  React.useEffect(() => {
    if (activeCollectionId !== undefined) {
      setActiveId(activeCollectionId);
    }
  }, [activeCollectionId]);
  const [isCreating, setIsCreating] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameLabel, setRenameLabel] = useState('');

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleResetSearch = () => {
    setActiveId(null);
    if (onSelectCollection) onSelectCollection(null);
  };

  const handleCreate = async () => {
    if (!newLabel.trim()) {
      setIsCreating(false);
      return;
    }
    
    try {
        await collectionService.create(newLabel);
        toast.success("创建收藏夹成功");
        setNewLabel('');
        setIsCreating(false);
        if (onRefresh) onRefresh();
    } catch (error: any) {
        logger.error("Failed to create collection", error, "Sidebar");
        toast.error(error.message || "创建失败");
    }
  };

  const startRename = (collection: Collection) => {
    setRenamingId(collection.collection_id);
    setRenameLabel(collection.label);
  };

  const handleRename = async () => {
    if (!renameLabel.trim() || !renamingId) {
      setRenamingId(null);
      return;
    }

    try {
      await collectionService.update(renamingId, renameLabel);
      toast.success("重命名成功");
      setRenamingId(null);
      setRenameLabel('');
      if (onRefresh) onRefresh();
    } catch (error: any) {
      logger.error("Failed to update collection", error, "Sidebar");
      toast.error(error.message || "重命名失败");
    }
  };

  const handleDelete = async (collectionId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (confirm('确定要删除这个收藏夹吗？')) {
      try {
        await collectionService.delete(collectionId);
        toast.success("删除成功");
        
        if (activeId === collectionId) {
            setActiveId(null);
            if (onSelectCollection) onSelectCollection(null);
        }
        
        if (onRefresh) onRefresh();
      } catch (error: any) {
        logger.error("Failed to delete collection", error, "Sidebar");
        toast.error(error.message || "删除失败");
      }
    }
  };

  return (
    <aside 
      className={cn(
        "h-full bg-white border-r border-gray-100 flex flex-col transition-all duration-300 relative z-20", 
        isCollapsed ? "w-20" : "w-72",
        className
      )}
    >
      {/* Toggle Button */}
      <button 
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-sm text-gray-500 hover:text-indigo-600 z-50"
      >
        {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>

      {/* Top Section: Search Navigation */}
      <div className="p-4 border-b border-gray-50">
        <button 
          onClick={handleResetSearch}
          className={cn(
            "flex items-center gap-3 p-3 rounded-xl transition-all duration-200 w-full text-left",
            activeId === null
              ? "bg-indigo-50 text-indigo-600" 
              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
            isCollapsed && "justify-center"
          )}
        >
          <Search className="w-5 h-5 flex-shrink-0" />
          {!isCollapsed && <span className="font-medium">搜索论文</span>}
        </button>
      </div>

      {/* Middle Section: Collections */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className={cn("flex items-center justify-between mb-4", isCollapsed && "justify-center")}>
          {!isCollapsed && <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">我的收藏夹</h3>}
          <button 
            onClick={() => {
              if (isCollapsed) setIsCollapsed(false);
              setIsCreating(true);
            }}
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-indigo-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-1">
          {isCreating && (
             <div className="flex items-center gap-2 p-2.5 rounded-xl bg-white border-2 border-indigo-100 shadow-sm animate-in fade-in slide-in-from-left-2">
                <div className="flex-shrink-0 text-indigo-500">
                   <FolderOpen className="w-4 h-4" />
                </div>
                <input
                  autoFocus
                  type="text"
                  value={newLabel}
                  onChange={(e) => setNewLabel(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                  onBlur={() => { if (!newLabel) setIsCreating(false); }}
                  placeholder="输入名称..."
                  className="flex-1 min-w-0 bg-transparent text-sm border-none focus:ring-0 p-0 text-gray-900 placeholder:text-gray-400 outline-none"
                />
                <button onClick={handleCreate} className="text-indigo-600 hover:bg-indigo-50 p-1 rounded-md">
                  <Check className="w-3.5 h-3.5" />
                </button>
              </div>
          )}

            {collections.map((collection) => (
              <div 
                key={collection.collection_id}
                className={cn(
                  "group flex items-center justify-between px-3 py-2 text-sm rounded-lg transition-colors cursor-pointer",
                  activeId === collection.collection_id 
                    ? "bg-indigo-50 text-indigo-600 font-medium" 
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                )}
                onClick={() => {
                  setActiveId(collection.collection_id);
                  if (onSelectCollection) onSelectCollection(collection);
                }}
              >
                {renamingId === collection.collection_id ? (
                  <div className="flex items-center gap-2 flex-1" onClick={e => e.stopPropagation()}>
                    <input
                      type="text"
                      value={renameLabel}
                      onChange={(e) => setRenameLabel(e.target.value)}
                      className="flex-1 min-w-0 bg-white border border-indigo-200 rounded px-1 py-0.5 text-xs focus:outline-none focus:border-indigo-400"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRename();
                        if (e.key === 'Escape') setRenamingId(null);
                      }}
                    />
                    <button onClick={handleRename} className="text-green-600 hover:bg-green-50 p-0.5 rounded">
                      <Check className="w-3 h-3" />
                    </button>
                    <button onClick={() => setRenamingId(null)} className="text-gray-400 hover:bg-gray-100 p-0.5 rounded">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-3 min-w-0">
                      <FolderOpen className={cn("w-4 h-4 flex-shrink-0", activeId === collection.collection_id ? "text-indigo-500" : "text-gray-400")} />
                      {!isCollapsed && <span className="truncate">{collection.label}</span>}
                    </div>
                    {!isCollapsed && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">{collection.count}</span>
                        <Popover.Root>
                          <Popover.Trigger asChild>
                            <button 
                              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white rounded text-gray-400 hover:text-gray-600 transition-all"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreVertical className="w-3 h-3" />
                            </button>
                          </Popover.Trigger>
                          <Popover.Portal>
                            <Popover.Content className="w-32 bg-white rounded-lg shadow-lg border border-gray-100 p-1 z-50 animate-in zoom-in-95 duration-200" side="right" align="start">
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  startRename(collection);
                                  // Close popover handled by UI state or click outside
                                }}
                                className="flex items-center gap-2 w-full px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-50 rounded text-left"
                              >
                                <Edit2 className="w-3 h-3" />
                                重命名
                              </button>
                              <button 
                                onClick={(e) => handleDelete(collection.collection_id, e)}
                                className="flex items-center gap-2 w-full px-2 py-1.5 text-xs text-red-600 hover:bg-red-50 rounded text-left"
                              >
                                <Trash2 className="w-3 h-3" />
                                删除
                              </button>
                            </Popover.Content>
                          </Popover.Portal>
                        </Popover.Root>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
        </div>
      </div>

      {/* Bottom Section: Settings */}
      <div className="p-4 border-t border-gray-50 mt-auto">
        <button 
          onClick={onSettingsClick}
          className={cn(
            "flex items-center gap-3 p-3 rounded-xl transition-all duration-200 w-full text-gray-600 hover:bg-gray-50 hover:text-gray-900",
            isCollapsed && "justify-center"
          )}
        >
          <Settings className="w-5 h-5 flex-shrink-0" />
          {!isCollapsed && <span className="font-medium">设置</span>}
        </button>
      </div>
    </aside>
  );
};

const CollectionItem = ({ 
  icon, 
  label, 
  count, 
  isCollapsed, 
  isActive = false,
  onClick,
  onDelete,
  onRename
}: { 
  icon: React.ReactNode; 
  label: string; 
  count: number; 
  isCollapsed: boolean; 
  isActive?: boolean;
  onClick: () => void;
  onDelete: () => void;
  onRename: () => void;
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div 
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 p-2.5 rounded-xl cursor-pointer group transition-all duration-200 relative",
        isActive 
          ? "bg-indigo-50 text-indigo-900 shadow-sm ring-1 ring-indigo-100" 
          : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
        isCollapsed && "justify-center px-0"
      )}
    >
      <div className={cn("flex-shrink-0", isActive ? "text-indigo-600" : "text-gray-400 group-hover:text-gray-600")}>
        {icon}
      </div>
      
      {!isCollapsed && (
        <>
          <span className="flex-1 truncate text-sm font-medium">{label}</span>
          {count > 0 && (
             <span className={cn(
               "text-xs px-1.5 py-0.5 rounded-md border",
               isActive ? "bg-indigo-100 text-indigo-600 border-indigo-200" : "text-gray-400 bg-gray-50 border-gray-100"
             )}>{count}</span>
          )}
          
          <div className={cn(
            "absolute right-2 opacity-0 group-hover:opacity-100 transition-opacity",
            isOpen && "opacity-100"
          )}>
            <Popover.Root open={isOpen} onOpenChange={setIsOpen}>
              <Popover.Trigger asChild>
                <button 
                  onClick={(e) => e.stopPropagation()}
                  className={cn(
                    "p-1 rounded-md shadow-sm transition-colors",
                    isActive ? "bg-indigo-100 text-indigo-600 hover:bg-indigo-200" : "bg-white text-gray-400 hover:text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <MoreVertical className="w-3 h-3" />
                </button>
              </Popover.Trigger>
              <Popover.Portal>
                <Popover.Content 
                  className="min-w-[140px] bg-white rounded-lg shadow-xl border border-gray-100 p-1.5 z-50 animate-in fade-in zoom-in-95 duration-200" 
                  sideOffset={5}
                  align="start"
                >
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      onRename();
                      setIsOpen(false);
                    }}
                    className="flex items-center w-full px-2 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
                  >
                    <Edit2 className="w-3.5 h-3.5 mr-2.5 text-gray-400" />
                    重命名
                  </button>
                  <div className="h-px bg-gray-50 my-1" />
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete();
                      setIsOpen(false);
                    }}
                    className="flex items-center w-full px-2 py-2 text-xs font-medium text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5 mr-2.5" />
                    删除
                  </button>
                </Popover.Content>
              </Popover.Portal>
            </Popover.Root>
          </div>
        </>
      )}
    </div>
  );
};
