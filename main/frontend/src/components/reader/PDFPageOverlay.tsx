import React, { useState, useRef, useEffect } from 'react';
import { Layer, Annotation, Rect as AnnotationRect } from '@/types/reader';
import { Highlighter, MessageSquare, Languages, X, Check, Trash2, Palette, Edit2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PDFPageOverlayProps {
  pageIndex: number; // 0-based
  scale: number;
  layers: Layer[];
  activeViewId: string;
  onAddAnnotation?: (annotation: Annotation) => void;
  onUpdateAnnotation?: (annotation: Annotation) => void;
  onDeleteAnnotation?: (annotationId: string) => void;
}

const HIGHLIGHT_COLORS = [
  { name: 'Yellow', value: 'bg-yellow-300', hex: '#fde047' },
  { name: 'Green', value: 'bg-green-300', hex: '#86efac' },
  { name: 'Blue', value: 'bg-blue-300', hex: '#93c5fd' },
  { name: 'Red', value: 'bg-red-300', hex: '#fca5a5' },
  { name: 'Purple', value: 'bg-purple-300', hex: '#d8b4fe' },
];

// Mock Translation Service
const translateTextMock = async (text: string): Promise<string> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(`[译] ${text.substring(0, 100)}${text.length > 100 ? '...' : ''} (这里是模拟的翻译结果，实际应接入后端 API)`);
    }, 800);
  });
};

export const PDFPageOverlay: React.FC<PDFPageOverlayProps> = ({
  pageIndex,
  scale,
  layers,
  activeViewId,
  onAddAnnotation,
  onUpdateAnnotation,
  onDeleteAnnotation
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const editPopupRef = useRef<HTMLDivElement>(null);
  const [selectedRects, setSelectedRects] = useState<AnnotationRect[]>([]);
  const [showToolbar, setShowToolbar] = useState(false);
  const [toolbarPosition, setToolbarPosition] = useState<{ top: number; left: number } | null>(null);
  const [selectedText, setSelectedText] = useState('');

  const [translationModal, setTranslationModal] = useState<{
    isOpen: boolean;
    text: string;
    result: string;
    loading: boolean;
    position: { top: number; left: number } | null;
  }>({
    isOpen: false,
    text: '',
    result: '',
    loading: false,
    position: null
  });

  // State for editing existing annotation
  const [activeAnnotationId, setActiveAnnotationId] = useState<string | null>(null);
  const [editPosition, setEditPosition] = useState<{ top: number; left: number } | null>(null);
  const [noteContent, setNoteContent] = useState('');
  const [translationResult, setTranslationResult] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  
  // State for hover tooltip
  const [hoveredAnnotationId, setHoveredAnnotationId] = useState<string | null>(null);
  const [hoverPosition, setHoverPosition] = useState<{ top: number; left: number } | null>(null);

  // Filter visible layers and their annotations for this page
  const visibleAnnotations = layers
    .filter(l => l.visible)
    .flatMap(l => l.annotations.map(a => ({ ...a, layerColor: l.color })))
    .filter(a => a.rects.some(r => r.pageIndex === pageIndex));

  // Handle click outside to close popup
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (activeAnnotationId && editPopupRef.current && !editPopupRef.current.contains(event.target as Node)) {
        // Only close if we are not clicking an annotation (which would switch active)
        // But annotations stop propagation, so this event listener on document shouldn't fire if annotation is clicked?
        // Actually, handleAnnotationClick calls stopPropagation, so it's fine.
        setActiveAnnotationId(null);
      }
    };

    if (activeAnnotationId) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [activeAnnotationId]);

  // Handle Page-level interaction (Click and Hover) manually
  // This allows us to set pointer-events-none on annotations to enable text selection through them
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    // We need to attach listeners to the parent Page component to capture events
    // because container itself might be covered or transparent
    const pageElement = container.parentElement;
    if (!pageElement) return;

    const getRelativeCoords = (e: MouseEvent) => {
      const rect = pageElement.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      return { x, y };
    };

    const findAnnotationAt = (x: number, y: number) => {
      // Find the top-most annotation (last in list usually rendered on top, but we want any match)
      // Reverse to hit the one visually on top if overlapping
      return [...visibleAnnotations].reverse().find(a => 
        a.rects.some(r => 
          r.pageIndex === pageIndex &&
          x >= r.x && x <= r.x + r.width &&
          y >= r.y && y <= r.y + r.height
        )
      );
    };

    const handlePageClick = (e: MouseEvent) => {
      // If user is selecting text, ignore click (selection logic handles it)
      const selection = window.getSelection();
      if (selection && selection.toString().length > 0) return;
      
      // If we are clicking inside the edit popup or toolbar, ignore
      // (This is handled by bubbling usually, but since we listen on parent, we might catch it)
      if ((e.target as HTMLElement).closest('.pointer-events-auto')) return;

      const { x, y } = getRelativeCoords(e);
      const annotation = findAnnotationAt(x, y);

      if (annotation) {
        // We found an annotation, trigger click logic manually
        // We need to call the logic defined in handleAnnotationClick
        // But we can't call internal function easily from here if it depends on state closure?
        // Actually we can, because this useEffect depends on visibleAnnotations
        
        // Logic from handleAnnotationClick:
      setActiveAnnotationId(annotation.annotation_id);
      setNoteContent(annotation.content || '');
      setTranslationResult(annotation.type === 'translate' ? (annotation.content || '') : '');
        
        const firstRect = annotation.rects.find(r => r.pageIndex === pageIndex);
        if (firstRect) {
          setEditPosition({
            top: firstRect.y + firstRect.height,
            left: firstRect.x + firstRect.width / 2
          });
        }
      } else {
        // Clicked on empty space (and not selecting text) -> Close popup
        // Already handled by click-outside, but good to be explicit
        // setActiveAnnotationId(null); // Optional
      }
    };

    const handlePageMouseMove = (e: MouseEvent) => {
      // Optimization: if we are editing, maybe skip hover?
      if (activeAnnotationId) return;

      const { x, y } = getRelativeCoords(e);
      const annotation = findAnnotationAt(x, y);

      if (annotation && annotation.type === 'note') {
         setHoveredAnnotationId(annotation.annotation_id);
         // Position tooltip
         const rect = annotation.rects.find(r => r.pageIndex === pageIndex);
         if (rect) {
            setHoverPosition({
              top: rect.y,
              left: rect.x + rect.width / 2
            });
         }
      } else {
         setHoveredAnnotationId(null);
      }
    };

    pageElement.addEventListener('click', handlePageClick);
    pageElement.addEventListener('mousemove', handlePageMouseMove);
    pageElement.addEventListener('mouseleave', () => setHoveredAnnotationId(null));

    return () => {
      pageElement.removeEventListener('click', handlePageClick);
      pageElement.removeEventListener('mousemove', handlePageMouseMove);
      pageElement.removeEventListener('mouseleave', () => setHoveredAnnotationId(null));
    };
  }, [visibleAnnotations, activeAnnotationId, pageIndex]); // Re-bind when annotations change

  // Handle Text Selection
  useEffect(() => {
    const handleSelection = () => {
      // If we are editing an annotation, don't trigger new selection logic easily
      if (activeAnnotationId) return;

      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
        setShowToolbar(false);
        return;
      }

      const range = selection.getRangeAt(0);
      const container = containerRef.current;
      
      if (!container || !container.parentElement?.contains(range.commonAncestorContainer)) {
        return;
      }

      const text = selection.toString();
      setSelectedText(text);

      // We are inside this page
      const pageRect = container.getBoundingClientRect();
      const clientRects = range.getClientRects();
      
      const newRects: AnnotationRect[] = [];
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

      for (let i = 0; i < clientRects.length; i++) {
        const rect = clientRects[i];
        
        // Convert to percentage relative to page
        const x = ((rect.left - pageRect.left) / pageRect.width) * 100;
        const y = ((rect.top - pageRect.top) / pageRect.height) * 100;
        const width = (rect.width / pageRect.width) * 100;
        const height = (rect.height / pageRect.height) * 100;

        newRects.push({ x, y, width, height, pageIndex });

        // Update bounds for toolbar position
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x + width);
        maxY = Math.max(maxY, y + height);
      }

      if (newRects.length > 0) {
        setSelectedRects(newRects);
        setToolbarPosition({
          top: minY, 
          left: (minX + maxX) / 2
        });
        setShowToolbar(true);
      }
    };

    document.addEventListener('mouseup', handleSelection);
    return () => {
      document.removeEventListener('mouseup', handleSelection);
    };
  }, [pageIndex, activeAnnotationId]);

  const handleCreateAnnotation = async (type: 'highlight' | 'note' | 'translate', color?: string) => {
    if (selectedRects.length === 0) return;

    // Special handling for Translation: Transient Mode
    if (type === 'translate') {
      // Calculate position (reusing toolbar or similar logic)
      let pos = toolbarPosition;
      if (!pos) {
         // Fallback center
         pos = { top: 50, left: 50 };
      }

      setTranslationModal({
        isOpen: true,
        text: selectedText,
        result: '',
        loading: true,
        position: { top: pos.top + 5, left: pos.left }
      });
      
      // Clear selection UI
      setShowToolbar(false);
      window.getSelection()?.removeAllRanges();

      // Fetch translation
      try {
        const translated = await translateTextMock(selectedText);
        setTranslationModal(prev => ({ ...prev, result: translated, loading: false }));
      } catch (e) {
        setTranslationModal(prev => ({ ...prev, result: '翻译失败', loading: false }));
      }
      return;
    }

    if (!onAddAnnotation) return;

    let content = '';
    const newId = Date.now().toString();
    
    // Determine initial content
    if (type === 'note') {
      content = '';
      setNoteContent('');
    }

    const newAnnotation: Annotation = {
      annotation_id: newId,
      type,
      rects: selectedRects,
      createdAt: Date.now(),
      content,
      color: color || (type === 'highlight' ? 'bg-yellow-300' : undefined)
    };

    onAddAnnotation(newAnnotation);
    
    // Clear selection UI but keep internal state for popup positioning
    window.getSelection()?.removeAllRanges();
    setShowToolbar(false);

    // Calculate position for the popup immediately
    if (toolbarPosition) {
       // We can adjust slightly
       setEditPosition({
         top: toolbarPosition.top + 5, // Slightly lower than toolbar was
         left: toolbarPosition.left
       });
    }

    // Auto-open logic
    if (type === 'note') {
      setActiveAnnotationId(newId);
    }
  };

  const handleAnnotationClick = (e: React.MouseEvent, annotation: Annotation) => {
    e.stopPropagation();
    e.preventDefault();
    
    setActiveAnnotationId(annotation.annotation_id);
    setNoteContent(annotation.content || '');
    setTranslationResult(annotation.type === 'translate' ? (annotation.content || '') : '');
    
    // Position popup near the first rect of the annotation on this page
    const firstRect = annotation.rects.find(r => r.pageIndex === pageIndex);
    if (firstRect) {
      setEditPosition({
        top: firstRect.y + firstRect.height,
        left: firstRect.x + firstRect.width / 2
      });
    }
  };

  const handleUpdateColor = (color: string) => {
    if (!activeAnnotationId || !onUpdateAnnotation) return;
    const annotation = visibleAnnotations.find(a => a.annotation_id === activeAnnotationId);
    if (annotation) {
      onUpdateAnnotation({ ...annotation, color });
    }
  };

  const handleSaveNote = () => {
    if (!activeAnnotationId || !onUpdateAnnotation) return;
    const annotation = visibleAnnotations.find(a => a.annotation_id === activeAnnotationId);
    if (annotation) {
      onUpdateAnnotation({ ...annotation, content: noteContent });
      setActiveAnnotationId(null);
    }
  };

  const handleSaveTranslationAsNote = () => {
     if (!onAddAnnotation) return;
     
     // We need to reconstruct rects? No, we used selectedRects but we cleared them.
     // Wait, if we are in transient mode, we need the rects to save.
     // But selectedRects state might be gone?
     // Actually `selectedRects` state is preserved until next selection changes it.
     // But `window.getSelection().removeAllRanges()` was called.
     // State `selectedRects` is React state, so it persists.
     
     const newId = Date.now().toString();
     const newAnnotation: Annotation = {
        annotation_id: newId,
        type: 'note', // Save as Note
        rects: selectedRects, // Using the preserved selection rects
        createdAt: Date.now(),
        content: `[原文] ${translationModal.text}\n\n[译文] ${translationModal.result}`,
        color: 'bg-yellow-300' // Default highlight for note
      };
      
      onAddAnnotation(newAnnotation);
      setTranslationModal(prev => ({ ...prev, isOpen: false }));
  };

  const handleDelete = () => {
    if (!activeAnnotationId || !onDeleteAnnotation) return;
    onDeleteAnnotation(activeAnnotationId);
    setActiveAnnotationId(null);
  };

  const handleAnnotationMouseEnter = (e: React.MouseEvent, annotation: Annotation) => {
    if (activeAnnotationId) return; // Don't show tooltip if editing
    if (annotation.type !== 'note') return; // Only show for notes as per request

    setHoveredAnnotationId(annotation.annotation_id);
    
    // Position tooltip near the mouse or the rect
    // Using rect for stability
    const rect = annotation.rects.find(r => r.pageIndex === pageIndex);
    if (rect) {
       setHoverPosition({
         top: rect.y,
         left: rect.x + rect.width / 2
       });
    }
  };

  const handleAnnotationMouseLeave = () => {
    setHoveredAnnotationId(null);
  };

  const activeAnnotation = visibleAnnotations.find(a => a.annotation_id === activeAnnotationId);

  return (
    <div ref={containerRef} className="absolute inset-0 z-10 pointer-events-none">
      {/* Existing Annotations */}
      {visibleAnnotations.map(annotation => (
        <React.Fragment key={annotation.annotation_id}>
          {annotation.rects.filter(r => r.pageIndex === pageIndex).map((rect, idx) => (
            <div
              key={`${annotation.annotation_id}-${idx}`}
              className={cn(
                "absolute transition-opacity mix-blend-multiply pointer-events-none",
                annotation.color || annotation.layerColor || "bg-yellow-300",
                annotation.type === 'note' && "border-b-[3px] border-red-500 border-dashed !bg-transparent", // Thicker dashed underline for notes
                annotation.type === 'translate' && "border-b-2 border-green-500 border-dashed !bg-transparent"
              )}
              style={{
                left: `${rect.x}%`,
                top: `${rect.y}%`,
                width: `${rect.width}%`,
                height: `${rect.height}%`,
                opacity: 0.4
              }}
            />
          ))}
          {/* Note Icon removed per user request */}
        </React.Fragment>
      ))}

      {/* Hover Tooltip for Notes - Card Style */}
      {hoveredAnnotationId && hoverPosition && !activeAnnotationId && (
        <div 
          className="absolute z-50 pointer-events-none bg-white text-gray-800 p-4 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-gray-100 w-[280px] transform -translate-x-1/2 -translate-y-full"
          style={{
            left: `${hoverPosition.left}%`,
            top: `${hoverPosition.top}%`,
            marginTop: '-16px'
          }}
        >
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-100">
            <MessageSquare className="w-4 h-4 text-indigo-500" />
            <span className="text-xs font-semibold text-gray-500 uppercase">备注内容</span>
          </div>
          <div className="text-sm leading-relaxed break-words text-gray-700">
            {visibleAnnotations.find(a => a.annotation_id === hoveredAnnotationId)?.content || '无内容'}
          </div>
        </div>
      )}

      {/* Creation Toolbar */}
      {showToolbar && toolbarPosition && !activeAnnotationId && (
        <div 
          className="absolute z-50 pointer-events-auto flex items-center gap-2 bg-white text-gray-700 p-2 rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.15)] border border-gray-100 transform -translate-x-1/2 -translate-y-full"
          style={{
            left: `${toolbarPosition.left}%`,
            top: `${toolbarPosition.top}%`,
            marginTop: '-12px'
          }}
        >
          {/* Color Picker for immediate highlight */}
          <div className="flex gap-1.5 mr-1">
             {HIGHLIGHT_COLORS.map(c => (
               <button
                 key={c.name}
                 onClick={(e) => { e.stopPropagation(); handleCreateAnnotation('highlight', c.value); }}
                 className={cn("w-5 h-5 rounded-full border border-gray-200 hover:scale-110 hover:shadow-sm transition-all", c.value)}
                 title={`高亮 ${c.name}`}
               />
             ))}
          </div>
          <div className="w-[1px] h-5 bg-gray-200 mx-1" />
          
          <button 
            onClick={(e) => { e.stopPropagation(); handleCreateAnnotation('note'); }}
            className="flex items-center gap-1 px-2 py-1 hover:bg-indigo-50 text-gray-600 hover:text-indigo-600 rounded-md transition-colors text-xs font-medium"
            title="添加备注"
          >
            <MessageSquare className="w-4 h-4" />
          </button>
          
          <button 
            onClick={(e) => { e.stopPropagation(); handleCreateAnnotation('translate'); }}
            className="flex items-center gap-1 px-2 py-1 hover:bg-green-50 text-gray-600 hover:text-green-600 rounded-md transition-colors text-xs font-medium"
            title="翻译选中内容"
          >
            <Languages className="w-4 h-4" />
          </button>
          
          <div className="w-[1px] h-5 bg-gray-200 mx-1" />
          
          <button 
            onClick={() => { setShowToolbar(false); window.getSelection()?.removeAllRanges(); }}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Edit/View Popup */}
      {activeAnnotationId && activeAnnotation && editPosition && (
        <div 
          ref={editPopupRef}
          className="absolute z-50 pointer-events-auto bg-white text-gray-900 p-3 rounded-lg shadow-xl border border-gray-200 w-64 transform -translate-x-1/2"
          style={{
            left: `${editPosition.left}%`,
            top: `${editPosition.top}%`,
            marginTop: '8px'
          }}
        >
          {/* Header */}
          <div className="flex justify-between items-center mb-2 pb-2 border-b border-gray-100">
            <span className="text-xs font-semibold text-gray-500 uppercase">
              {activeAnnotation.type === 'highlight' ? '高亮样式' : 
               activeAnnotation.type === 'note' ? '备注内容' : '翻译结果'}
            </span>
            <div className="flex gap-1">
               <button 
                 onClick={handleDelete}
                 className="p-1 hover:bg-red-50 text-gray-400 hover:text-red-600 rounded transition-colors"
                 title="删除"
               >
                 <Trash2 className="w-3.5 h-3.5" />
               </button>
               <button 
                 onClick={() => setActiveAnnotationId(null)}
                 className="p-1 hover:bg-gray-100 text-gray-400 hover:text-gray-700 rounded transition-colors"
               >
                 <X className="w-3.5 h-3.5" />
               </button>
            </div>
          </div>

          {/* Content */}
          {activeAnnotation.type === 'highlight' && (
            <div className="flex justify-center gap-2 p-1">
              {HIGHLIGHT_COLORS.map(c => (
                <button
                  key={c.name}
                  onClick={() => handleUpdateColor(c.value)}
                  className={cn(
                    "w-6 h-6 rounded-full border-2 transition-transform hover:scale-110", 
                    c.value,
                    activeAnnotation.color === c.value ? "border-gray-900" : "border-transparent"
                  )}
                  title={c.name}
                />
              ))}
            </div>
          )}

          {activeAnnotation.type === 'note' && (
            <div className="space-y-2">
              <textarea
                autoFocus
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSaveNote();
                  }
                }}
                className="w-full text-sm p-2 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[80px]"
                placeholder="输入备注... (按 Enter 保存)"
              />
              <button
                onClick={handleSaveNote}
                className="w-full flex items-center justify-center gap-1 bg-indigo-600 text-white py-1.5 rounded-md text-xs font-medium hover:bg-indigo-700"
              >
                <Check className="w-3 h-3" />
                保存备注
              </button>
            </div>
          )}

          {activeAnnotation.type === 'translate' && (
            <div className="space-y-2">
              <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded-md min-h-[60px] max-h-[200px] overflow-y-auto leading-relaxed border border-gray-100">
                {isTranslating ? (
                  <div className="flex items-center gap-2 text-indigo-600 py-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="font-medium">正在翻译中...</span>
                  </div>
                ) : (
                  translationResult || '暂无翻译结果'
                )}
              </div>
            </div>
          )}
        </div>
      )}
      {/* Translation Modal (Transient) */}
      {translationModal.isOpen && translationModal.position && (
         <div 
           className="absolute z-50 pointer-events-auto bg-white text-gray-900 p-0 rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-gray-100 w-72 transform -translate-x-1/2"
           style={{
             left: `${translationModal.position.left}%`,
             top: `${translationModal.position.top}%`,
             marginTop: '12px'
           }}
           onClick={(e) => e.stopPropagation()}
         >
           {/* Header */}
           <div className="flex justify-between items-center px-4 py-3 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
             <div className="flex items-center gap-2">
               <Languages className="w-4 h-4 text-indigo-500" />
               <span className="text-sm font-semibold text-gray-700">翻译助手</span>
             </div>
             <button 
               onClick={() => setTranslationModal(prev => ({ ...prev, isOpen: false }))}
               className="text-gray-400 hover:text-gray-600 transition-colors"
             >
               <X className="w-4 h-4" />
             </button>
           </div>
           
           {/* Body */}
           <div className="p-4 space-y-4">
             {/* Source */}
             <div className="text-xs text-gray-500 line-clamp-2 italic border-l-2 border-gray-200 pl-2">
               {translationModal.text}
             </div>
             
             {/* Result */}
             <div className="min-h-[80px]">
               {translationModal.loading ? (
                  <div className="flex flex-col items-center justify-center h-full gap-2 text-indigo-500 py-4">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-xs font-medium">正在翻译...</span>
                  </div>
               ) : (
                  <div className="text-sm text-gray-800 leading-relaxed font-medium">
                    {translationModal.result}
                  </div>
               )}
             </div>
           </div>
           
           {/* Footer */}
           <div className="px-4 py-3 border-t border-gray-100 flex gap-2">
             <button
               onClick={handleSaveTranslationAsNote}
               disabled={translationModal.loading}
               className="flex-1 flex items-center justify-center gap-1.5 bg-indigo-600 text-white py-1.5 rounded-lg text-xs font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
             >
               <MessageSquare className="w-3.5 h-3.5" />
               保存为备注
             </button>
           </div>
         </div>
      )}
    </div>
  );
};
