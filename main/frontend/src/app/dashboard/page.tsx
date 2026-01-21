'use client';

import React, { useState } from 'react';
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar, Collection } from "@/components/layout/Sidebar";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchFilters } from "@/components/search/SearchFilters";
import { Paper } from "@/types/models";
import { SearchResults } from "@/components/search/SearchResults";
import { SettingsModal } from "@/components/settings/SettingsModal";
import { UploadModal } from "@/components/upload/UploadModal";
import { BookOpen, Sparkles } from 'lucide-react';
import { useUploadStore } from "@/store/upload.store";

import { searchService } from '@/services/search.service';
import { paperService } from '@/services/paper.service';
import { collectionService } from '@/services/collection.service';
import { toast } from 'sonner';
import { useAuthStore } from '@/store/use-auth-store';
import { logger } from '@/lib/logger';

export default function DashboardPage() {
  const [hasSearched, setHasSearched] = useState(false);
  const [searchResults, setSearchResults] = useState<Paper[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  // Upload modal is now controlled globally
  const [isSearching, setIsSearching] = useState(false);
  const [activeCollection, setActiveCollection] = useState<Collection | null>(null);
  const [isAIEnabled, setIsAIEnabled] = useState(false);
  
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const openUpload = useUploadStore((s) => s.open);
  const setUploadCollectionId = useUploadStore((s) => s.setCollectionId);
  const lastUploadTime = useUploadStore((s) => s.lastUploadTime);

  const loadCollections = React.useCallback(async () => {
    if (!isAuthenticated) {
        setCollections([]);
        return;
    }
    try {
      const list = await collectionService.getAll();
      const mapped = list.map(c => ({
        collection_id: c.collection_id,
        label: c.name,
        count: c.count || 0
      }));
      setCollections(mapped);
    } catch (error: any) {
      logger.error("Failed to load collections", error, 'DashboardPage');
      // Silent fail or toast? If not logged in, api throws 401. 
      // But we checked isAuthenticated. 
      // toast.error("加载收藏夹失败");
    }
  }, [isAuthenticated]);

  const loadRecentPapers = React.useCallback(async () => {
    try {
      setIsSearching(true);
      const papers = await paperService.getList(1, 10);
      setSearchResults(papers);
    } catch (error: any) {
      logger.error("Failed to load papers", error, 'DashboardPage');
      toast.error(error.message || "加载失败");
    } finally {
      setIsSearching(false);
    }
  }, []);

  const loadCollectionPapers = React.useCallback(async (collectionId: string) => {
    try {
      setIsSearching(true);
      const detail = await collectionService.getById(collectionId);
      const papers = (detail as any)?.papers ?? [];
      setSearchResults(papers);
      setIsAIEnabled(false);
      setHasSearched(true);
    } catch (error: any) {
      logger.error("Failed to load collection papers", error, 'DashboardPage');
      toast.error(error.message || "加载收藏夹论文失败");
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleUploadSuccess = React.useCallback(() => {
    if (activeCollection?.collection_id) {
      loadCollectionPapers(activeCollection.collection_id);
      return;
    }
    loadRecentPapers();
  }, [activeCollection?.collection_id, loadCollectionPapers, loadRecentPapers]);

  React.useEffect(() => {
    setUploadCollectionId(activeCollection?.collection_id ?? null);
  }, [activeCollection?.collection_id, setUploadCollectionId]);

  React.useEffect(() => {
    return () => {
      setUploadCollectionId(null);
    };
  }, [setUploadCollectionId]);

  // Listen for upload success
  React.useEffect(() => {
    if (lastUploadTime > 0) {
        handleUploadSuccess();
    }
  }, [handleUploadSuccess, lastUploadTime]);

  // Initial load & Auth change
  React.useEffect(() => {
    // loadRecentPapers();
    loadCollections();
    
    // Register global upload success callback for this page
    // When upload succeeds, we want to refresh the list if we are on dashboard
    // But since store is global, we need to be careful not to overwrite other callbacks if any
    // For now, we can just hook into the store's open mechanism or listen to changes?
    // Actually, simpler: pass a callback to open() if we triggered it. 
    // But Navbar triggers it. 
    // So we can subscribe to store changes or just reload periodically?
    // Or better: The Navbar in DashboardPage is the same Navbar.
    // The Navbar uses uploadStore.open(). 
    // We can't easily pass a callback from Navbar if Navbar is generic.
    // However, we can use a useEffect to listen to uploadStore.onUploadSuccess call? 
    // No, onUploadSuccess in store is a callback function stored in state.
    
    // Alternative: Dashboard watches for "upload success event".
    // Or we just reload periodically when modal closes?
  }, [loadCollections, loadRecentPapers]);

  // Listen for upload success
  // We can modify the store to have an event emitter or just a simple version flag?
  // Let's keep it simple. The user just wants the modal to open globally.
  // Auto-refreshing the dashboard list is a "nice to have".
  // Let's add a "lastUploadTime" to the store so we can depend on it.
  
  // For now, let's remove the local UploadModal and Navbar prop passing.

  const handleSearch = async (query: string, useAI: boolean) => {
    if (!query || !query.trim()) {
        toast.error("请输入搜索内容");
        return;
    }
    setIsSearching(true);
    setIsAIEnabled(useAI);
    
    try {
        const response = await searchService.search({
            query,
            page: 1,
            limit: 20,
            filters: activeCollection ? { collection_id: activeCollection.id } : undefined
        });
        setHasSearched(true);
        setSearchResults(response.items || []);
    } catch (error: any) {
        logger.error("Search failed", error, 'DashboardPage');
        toast.error(error.message || "搜索失败");
    } finally {
        setIsSearching(false);
    }
  };

  const handleToggleBookmark = (id: string) => {
    setSearchResults(prev => prev.map(p => 
      p.id === id ? { ...p, is_bookmarked: !p.is_bookmarked } : p
    ));
  };

  const handleCollectionsClick = () => {
    if (collections.length > 0) {
        // Try to find "默认收藏夹" or use the first one
        const defaultCol = collections.find(c => c.label.includes('默认')) || collections[0];
        setActiveCollection(defaultCol);
        loadCollectionPapers(defaultCol.id);
    } else {
        toast.info("暂无收藏夹");
    }
  };

  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      <Navbar 
        onCollectionsClick={handleCollectionsClick}
      />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar 
          onSettingsClick={() => setIsSettingsOpen(true)} 
          onSelectCollection={(collection) => {
             setActiveCollection(collection);
             if (collection?.id) {
               loadCollectionPapers(collection.id);
               return;
             }
             setHasSearched(false);
             loadRecentPapers();
          }}
          collections={collections}
          activeCollectionId={activeCollection?.id}
          onRefresh={loadCollections}
        />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto relative p-6 md:p-12 flex flex-col items-center">
          
          {/* Header Status Bar */}
          <div className="w-full max-w-5xl flex justify-end mb-4 min-h-[32px]">
             {activeCollection && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 rounded-lg shadow-sm animate-in fade-in slide-in-from-top-2">
                   <span className="text-xs font-medium text-gray-400">当前查看</span>
                   <span className="text-sm font-semibold text-indigo-600">{activeCollection.label}</span>
                </div>
             )}
          </div>

          {/* Top Search Area */}
          <div className={`w-full max-w-5xl flex flex-col items-center transition-all duration-500 ${hasSearched ? 'pt-2 pb-6' : 'pt-16 pb-10'}`}>
            <SearchBar onSearch={handleSearch} />
            <SearchFilters 
              className="mt-4" 
              onUploadClick={() => openUpload({ collectionId: activeCollection?.collection_id ?? null })} 
            />
          </div>

          {/* Content Area */}
          <div className="flex-1 w-full max-w-5xl flex flex-col">
            {isSearching ? (
               <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-4"></div>
                  <p>
                    {activeCollection ? `正在 ${activeCollection.label} 中检索...` : "正在深度检索..."}
                  </p>
               </div>
            ) : hasSearched ? (
              <SearchResults results={searchResults} onToggleBookmark={handleToggleBookmark} aiEnabled={isAIEnabled} />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400 mt-10">
                <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-6">
                  {activeCollection ? (
                     <Sparkles className="w-10 h-10 text-indigo-300" />
                  ) : (
                     <BookOpen className="w-10 h-10 text-gray-300" />
                  )}
                </div>
                <h2 className="text-xl font-semibold text-gray-600 mb-2">
                   {activeCollection ? `在 ${activeCollection.label} 中探索` : "开始探索知识"}
                </h2>
                <p className="max-w-md text-sm text-gray-500 leading-relaxed">
                  {activeCollection 
                    ? "仅搜索当前收藏夹内的论文。切换到全局搜索可查看更多结果。" 
                    : "输入关键词开始搜索，或上传您的 PDF 论文。开启 AI 模式可以获得更深度的见解和关联推荐。"
                  }
                </p>
              </div>
            )}
          </div>
          
        </main>
      </div>

      {/* Settings Modal */}
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      
      {/* Upload Modal - Now global in Layout, removed from here */}
    </div>
  );
}
