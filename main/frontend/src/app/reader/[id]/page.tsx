'use client';

import React, { useState, useEffect } from 'react';
import { ReaderNavbar } from '@/components/reader/ReaderNavbar';
import { ReaderSidebar } from '@/components/reader/ReaderSidebar';
import { ReaderRightPanel } from '@/components/reader/ReaderRightPanel';
import { PDFViewer } from '@/components/reader/PDFViewer';
import { Layer, Annotation } from '@/types/reader';
import { paperService } from '@/services/paper.service';
import { readerService } from '@/services/reader.service';
import { Paper, PaperStatusResponse } from '@/types/api';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';
import { logger } from '@/lib/logger';

interface ReaderPageProps {
  params: {
    id: string;
  };
}

export default function ReaderPage({ params }: ReaderPageProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [paper, setPaper] = useState<Paper | null>(null);
  const [status, setStatus] = useState<PaperStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Layers State
  const [layers, setLayers] = useState<Layer[]>([]);
  const [activeViewId, setActiveViewId] = useState<string>('');

  useEffect(() => {
    const init = async () => {
        try {
            // 1. Get Paper Details
            const paperData = await paperService.getById(params.id);
            setPaper(paperData);

            // 2. Get Status
            const statusData = await paperService.getStatus(params.id);
            setStatus(statusData);

            if (statusData.status === 'completed') {
                 // 3. Get Layers (Views + Annotations) if completed
                 try {
                    const views = await readerService.getViews(params.id);
                    
                    if (views.length > 0) {
                        const layersData = await Promise.all(views.map(async (view) => {
                            try {
                                const annos = await readerService.getAnnotations(params.id, view.view_id);
                                return {
                                    view_id: view.view_id,
                                    name: view.name,
                                    type: (view.name.includes('Base') || view.name.includes('原文')) ? 'system' : 'user',
                                    visible: view.enable,
                                    annotations: annos.items || [],
                                    color: undefined
                                } as Layer;
                            } catch (e) {
                                logger.warn(`Failed to fetch annotations for view ${view.view_id}`, e);
                                return {
                                    view_id: view.view_id,
                                    name: view.name,
                                    type: 'user',
                                    visible: view.enable,
                                    annotations: [],
                                } as Layer;
                            }
                        }));
                        setLayers(layersData);
                        setActiveViewId(layersData[0].view_id);
                    } else {
                         // Create default system layer if none
                         const defaultView = await readerService.createView(params.id, '原文 (Base)');
                         const defaultLayer: Layer = {
                             view_id: defaultView.view_id,
                             name: defaultView.name,
                             type: 'system',
                             visible: defaultView.enable,
                             annotations: []
                         };
                         setLayers([defaultLayer]);
                         setActiveViewId(defaultLayer.view_id);
                    }
                 } catch (e) {
                     logger.error("Failed to fetch layers", e, 'ReaderPage');
                 }
            }

        } catch (error: any) {
            logger.error("Failed to init reader:", error, 'ReaderPage');
            toast.error(error.message || "无法加载论文信息");
        } finally {
            setIsLoading(false);
        }
    };

    init();
  }, [params.id]);

  // Polling for status if processing
  useEffect(() => {
      if (status && (status.status === 'pending' || status.status === 'processing')) {
          const interval = setInterval(async () => {
              try {
                  const newStatus = await paperService.getStatus(params.id);
                  setStatus(newStatus);
                  if (newStatus.status === 'completed') {
                      clearInterval(interval);
                      try {
                        const layersData = await readerService.getLayers(params.id);
                        const fetchedLayers = (layersData as any).layers || layersData;
                        setLayers(fetchedLayers);
                        if (fetchedLayers.length > 0) {
                          setActiveViewId(fetchedLayers[0].view_id);
                        } else {
                          const defaultView = await readerService.createView(params.id, '原文 (Base)');
                          const defaultLayer: Layer = {
                              view_id: defaultView.view_id,
                              name: defaultView.name,
                              type: 'system',
                              visible: defaultView.enable,
                              annotations: []
                          };
                          setLayers([defaultLayer]);
                          setActiveViewId(defaultLayer.view_id);
                        }
                      } catch (e) {
                        logger.error('Failed to fetch layers after processing completed', e, 'ReaderPage');
                      }
                  } else if (newStatus.status === 'failed') {
                      clearInterval(interval);
                      toast.error("论文处理失败");
                  }
              } catch (e) {
                  logger.error("Polling failed", e, 'ReaderPage');
              }
          }, 3000);
          return () => clearInterval(interval);
      }
  }, [status, params.id]);


  // Layer Handlers
  const handleAddLayer = async () => {
    try {
        const name = `新视图 ${layers.length + 1}`;
        const newView = await readerService.createView(params.id, name);
        const newLayer: Layer = {
            view_id: newView.view_id,
            name: newView.name,
            type: 'user',
            visible: newView.enable,
            annotations: []
        };
        setLayers([...layers, newLayer]);
        setActiveViewId(newLayer.view_id);
        toast.success("图层创建成功");
    } catch (e) {
        toast.error("创建图层失败");
    }
  };

  const handleDeleteLayer = async (viewId: string) => {
    try {
        await readerService.deleteView(params.id, viewId);
        setLayers(layers.filter(l => l.view_id !== viewId));
        if (activeViewId === viewId) {
            setActiveViewId(layers[0]?.view_id || '');
        }
        toast.success("图层删除成功");
    } catch (e) {
        toast.error("删除图层失败");
    }
  };

  const handleToggleLayerVisibility = async (viewId: string) => {
    const layer = layers.find(l => l.view_id === viewId);
    if (!layer) return;

    // Optimistic update
    const newVisibility = !layer.visible;
    setLayers(layers.map(l => l.view_id === viewId ? { ...l, visible: newVisibility } : l));
    
    try {
        await readerService.updateView(params.id, viewId, newVisibility);
    } catch (e) {
        // Revert
        setLayers(layers.map(l => l.view_id === viewId ? { ...l, visible: !newVisibility } : l));
        toast.error("更新图层状态失败");
    }
  };

  const handleSetActiveLayer = (viewId: string) => {
    setActiveViewId(viewId);
  };

  const handleAddAnnotation = async (annotation: Annotation) => {
      try {
          const { annotation_id, ...data } = annotation;
          await readerService.addAnnotation(params.id, activeViewId, data);
          
          // Re-fetch to get the real ID if needed, or just use optimistic with generated ID?
          // The backend might assign a different ID. Ideally we should get the response.
          // But addAnnotation returns void in current service definition.
          // Let's assume for now we might need to refresh or just keep using the generated ID if backend accepts it?
          // Actually, service.addAnnotation takes Omit<Annotation, 'annotation_id'>.
          // This implies backend generates ID.
          // If backend generates ID, we should update our local state with that ID.
          // But `addAnnotation` returns void. This is a potential issue.
          // Let's check reader.service.ts again. It returns void.
          // Recommendation: Update reader.service.ts to return the created annotation or at least the ID.
          // For now, I will use the generated ID and hope for the best, or trigger a refresh?
          // Refreshing is safer.
          
          const annos = await readerService.getAnnotations(params.id, activeViewId);
          setLayers(layers.map(l => {
            if (l.view_id === activeViewId) {
                return { ...l, annotations: annos.items || [] };
            }
            return l;
          }));
      } catch (e) {
          toast.error("添加标注失败");
      }
  };

  const handleUpdateAnnotation = async (annotation: Annotation) => {
    // Optimistic
    setLayers(layers.map(l => {
      if (l.annotations.some(a => a.annotation_id === annotation.annotation_id)) {
        return {
          ...l,
          annotations: l.annotations.map(a => a.annotation_id === annotation.annotation_id ? annotation : a)
        };
      }
      return l;
    }));

    try {
        const { annotation_id, ...data } = annotation;
        // We need to find which view this annotation belongs to.
        // It should be the active view usually, or the view it belongs to.
        const layer = layers.find(l => l.annotations.some(a => a.annotation_id === annotation_id));
        if (layer) {
            await readerService.updateAnnotation(params.id, layer.view_id, annotation_id, data);
        }
    } catch (e) {
        toast.error("更新标注失败");
        // Revert? Complex to revert without deep clone or history.
    }
  };

  const handleDeleteAnnotation = async (annotationId: string) => {
    // Optimistic
    const layer = layers.find(l => l.annotations.some(a => a.annotation_id === annotationId));
    
    setLayers(layers.map(l => ({
      ...l,
      annotations: l.annotations.filter(a => a.annotation_id !== annotationId)
    })));

    if (layer) {
        try {
            await readerService.deleteAnnotation(params.id, layer.view_id, annotationId);
        } catch (e) {
             toast.error("删除标注失败");
             // Revert logic needed ideally
        }
    }
  };
  
  if (isLoading) {
      return (
          <div className="h-screen w-full flex items-center justify-center bg-gray-50">
              <div className="text-center">
                  <Loader2 className="w-10 h-10 animate-spin text-indigo-600 mx-auto mb-4" />
                  <p className="text-gray-600">正在加载论文...</p>
              </div>
          </div>
      );
  }

  if (!paper || !status) {
       return (
          <div className="h-screen w-full flex items-center justify-center bg-gray-50">
              <div className="text-center">
                  <p className="text-red-600">未找到论文信息</p>
              </div>
          </div>
      );
  }

  /*
   * 变更记录：FrontendAgent(react)｜2026-01-17 21:36:00
   * 使用位置：ReaderPage（src/app/reader/[id]/page.tsx），用于阅读页主渲染分支。
   * 实现说明：解析状态为 pending/processing 时，只要后端已提供 file_url（来自 status 或 paper），就直接渲染 PDF；
   *           同时以非阻塞的方式展示解析进度提示，避免“必须等 AI 解析完才能看论文”。
   */
  const pdfUrl = status.file_url || paper.file_url || '';
  const isProcessing = status.status === 'processing' || status.status === 'pending';
  const shouldBlockForProcessing = isProcessing && !pdfUrl;

  if (shouldBlockForProcessing) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md p-6 bg-white rounded-xl shadow-lg">
          <Loader2 className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-6" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">正在解析论文</h2>
          <p className="text-gray-500 mb-6">DeepPaper 正在使用 AI 深度解析您的论文，生成导读、脑图和结构化数据。这通常需要 1-2 分钟。</p>

          <div className="w-full bg-gray-100 rounded-full h-2 mb-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${status.progress || 0}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-400 text-right">{status.progress || 0}%</p>
        </div>
      </div>
    );
  }

  if (!pdfUrl) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md p-6 bg-white rounded-xl shadow-lg">
          <p className="text-gray-900 font-medium">未找到论文 PDF 资源</p>
          <p className="text-sm text-gray-500 mt-2">请稍后重试，或返回重新打开该论文。</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex flex-col bg-white overflow-hidden">
      {/* 1. Top Navbar */}
      <ReaderNavbar 
        title={`Paper: ${paper.title}`}
        isBookmarked={!!paper.is_bookmarked}
        onViewManage={() => logger.debug('View Manage Clicked', null, 'ReaderPage')}
        onSearch={setSearchQuery}
      />

      {/* 2. Main Workspace (Flex Row) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar (TOC / Layers) */}
        <ReaderSidebar 
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          toc={status.toc || []}
          layers={layers}
          activeViewId={activeViewId}
          onAddLayer={handleAddLayer}
          onDeleteLayer={handleDeleteLayer}
          onToggleLayerVisibility={handleToggleLayerVisibility}
          onSetActiveLayer={handleSetActiveLayer}
        />

        {/* Center PDF Viewer */}
        <div className="flex-1 h-full relative">
          {isProcessing && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 w-[min(520px,calc(100%-24px))] bg-white/95 backdrop-blur border border-gray-200 rounded-xl shadow-sm px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                  <span>AI 解析中（不影响阅读）</span>
                </div>
                <div className="text-xs text-gray-500">{status.progress || 0}%</div>
              </div>
              <div className="mt-2 w-full bg-gray-100 rounded-full h-2">
                <div
                  className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${status.progress || 0}%` }}
                ></div>
              </div>
            </div>
          )}

          <PDFViewer
            url={pdfUrl}
            className="h-full"
            initialPage={currentPage}
            onPageChange={setCurrentPage}
            searchQuery={searchQuery}
            layers={layers}
            activeViewId={activeViewId}
            onAddAnnotation={activeViewId ? handleAddAnnotation : undefined}
            onUpdateAnnotation={handleUpdateAnnotation}
            onDeleteAnnotation={handleDeleteAnnotation}
          />
        </div>

        {/* Right AI Panel */}
        <ReaderRightPanel paperId={params.id} />
      </div>
    </div>
  );
}
