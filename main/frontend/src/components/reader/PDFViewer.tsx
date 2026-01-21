'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { cn } from '@/lib/utils';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

import { Layer, Annotation } from '@/types/reader';
import { PDFPageOverlay } from './PDFPageOverlay';
import { useAuthStore } from '@/store/use-auth-store';

// Set worker src
// Use a stable CDN or local file. Here we use unpkg with https protocol explicitly.
// In a real production build, you should copy the worker to /public and reference it locally.
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
  url: string;
  className?: string;
  initialPage?: number;
  layers?: Layer[];
  activeViewId?: string;
  onAddAnnotation?: (annotation: Annotation) => void;
  onPageChange?: (page: number) => void;
  searchQuery?: string;
  onUpdateAnnotation?: (annotation: Annotation) => void;
  onDeleteAnnotation?: (annotationId: string) => void;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({ 
  url, 
  className,
  initialPage = 1,
  onPageChange,
  searchQuery = '',
  layers = [],
  activeViewId = '',
  onAddAnnotation,
  onUpdateAnnotation,
  onDeleteAnnotation
}) => {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState<number>(initialPage);
  const [scale, setScale] = useState<number>(1.0);
  const [viewMode, setViewMode] = useState<'pagination' | 'scroll'>('pagination');
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState<number>(0);
  const { token } = useAuthStore();

  const options = useMemo(() => ({
    httpHeaders: {
      'Authorization': `Bearer ${token}`
    }
  }), [token]);

  // Sync internal state with props if needed, or just use internal
  useEffect(() => {
    if (initialPage !== pageNumber) {
      setPageNumber(initialPage);
    }
  }, [initialPage, pageNumber]);

  // Notify parent on change
  const handlePageChange = (newPage: number) => {
    setPageNumber(newPage);
    onPageChange?.(newPage);
  };

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  // Highlight renderer
  const textRenderer = React.useCallback(
    (textItem: any) => {
      if (!searchQuery) return textItem.str;

      const str = textItem.str;
      const parts = str.split(new RegExp(`(${searchQuery})`, 'gi'));
      
      return parts.map((part: string, index: number) => 
        part.toLowerCase() === searchQuery.toLowerCase() ? (
          `<mark key=${index} style="background-color: #ffeb3b; padding: 2px 0;">${part}</mark>`
        ) : (
          part
        )
      ).join('');
    },
    [searchQuery]
  );


  // Handle Resize
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // Auto-scale based on container width (with some padding)
  useEffect(() => {
    if (containerWidth > 0) {
      // Assuming A4 ratio roughly, or just fit width. 
      // Standard A4 at 72dpi is ~595px width.
      // Let's just set a reasonable scale calculation or leave it to user.
      // For now, let's keep scale at 1.0 or responsive if we want 'fit-width'
      // Ideally, we want 'fit-width' logic.
      const targetWidth = containerWidth - 48; // 24px padding each side
      const standardPageWidth = 600; // approximation
      const newScale = targetWidth / standardPageWidth;
      // Clamp scale
      setScale(Math.min(Math.max(newScale, 0.5), 2.0));
    }
  }, [containerWidth]);

  return (
    <div 
      ref={containerRef} 
      className={cn("flex-1 bg-gray-100 overflow-y-auto flex justify-center p-6 relative", className)}
    >
      {/* Top Controls for View Mode */}
      <div className="absolute top-4 right-6 z-10 bg-white/90 backdrop-blur shadow-sm rounded-lg border border-gray-200 p-1 flex gap-1">
        <button
          onClick={() => setViewMode('pagination')}
          className={cn(
            "px-3 py-1 text-xs font-medium rounded-md transition-colors",
            viewMode === 'pagination' ? "bg-indigo-100 text-indigo-700" : "text-gray-600 hover:bg-gray-100"
          )}
        >
          翻页
        </button>
        <button
          onClick={() => setViewMode('scroll')}
          className={cn(
            "px-3 py-1 text-xs font-medium rounded-md transition-colors",
            viewMode === 'scroll' ? "bg-indigo-100 text-indigo-700" : "text-gray-600 hover:bg-gray-100"
          )}
        >
          滚动
        </button>
      </div>

      <div className="shadow-lg">
        <Document
          file={url}
          options={options}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div className="flex items-center justify-center h-[calc(100vh-200px)]">
               <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          }
          error={
             <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)] text-gray-500">
                <p>无法加载 PDF 文件</p>
                <p className="text-sm mt-2">请检查文件是否存在或权限是否正确</p>
             </div>
          }
        >
          {viewMode === 'pagination' ? (
            <div className="relative">
              <Page 
                pageNumber={pageNumber} 
                scale={scale} 
                renderTextLayer={true}
                renderAnnotationLayer={true}
                customTextRenderer={textRenderer}
                className="bg-white"
              />
              <PDFPageOverlay 
                pageIndex={pageNumber - 1} // 0-based
                scale={scale}
                layers={layers}
                activeViewId={activeViewId}
                onAddAnnotation={onAddAnnotation}
                onUpdateAnnotation={onUpdateAnnotation}
                onDeleteAnnotation={onDeleteAnnotation}
              />
            </div>
          ) : (
            // Scroll Mode: Render all pages
            // Note: In production, use react-window or similar for virtualization
            Array.from(new Array(numPages || 0), (_, index) => (
              <div key={`page_${index + 1}`} className="mb-4 last:mb-0 relative">
                 <Page 
                  pageNumber={index + 1} 
                  scale={scale} 
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  customTextRenderer={textRenderer}
                  className="bg-white"
                />
                <PDFPageOverlay 
                  pageIndex={index} // 0-based
                  scale={scale}
                  layers={layers}
                  activeViewId={activeViewId}
                  onAddAnnotation={onAddAnnotation}
                  onUpdateAnnotation={onUpdateAnnotation}
                  onDeleteAnnotation={onDeleteAnnotation}
                />
              </div>
            ))
          )}
        </Document>
      </div>
      
      {/* Floating Controls (Pagination Only) */}
      {viewMode === 'pagination' && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900/80 backdrop-blur-md text-white px-4 py-2 rounded-full flex items-center gap-4 text-sm shadow-xl z-50">
           <button 
             disabled={pageNumber <= 1}
             onClick={() => handlePageChange(pageNumber - 1)}
             className="hover:text-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
           >
             Prev
           </button>
           <span className="font-mono">
             {pageNumber} / {numPages || '--'}
           </span>
           <button 
             disabled={numPages === null || pageNumber >= numPages}
             onClick={() => handlePageChange(pageNumber + 1)}
             className="hover:text-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
           >
             Next
           </button>
        </div>
      )}
    </div>
  );
};
