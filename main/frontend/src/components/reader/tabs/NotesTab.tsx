import React, { useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Plus, 
  Trash2, 
  Edit2, 
  ChevronUp, 
  ChevronDown, 
  Eye, 
  EyeOff
} from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

interface Note {
  id: string;
  content: string;
  timestamp: string;
  pageRef?: number;
}

interface NotesTabProps {
  paperId: string;
}

export const NotesTab: React.FC<NotesTabProps> = ({ paperId }) => {
  const [notes, setNotes] = useState<Note[]>([
    { id: '1', content: '这一段关于 Agent 协作的描述很有启发，可以参考到我的毕设中。', timestamp: '2026-01-11 10:30', pageRef: 3 },
    { id: '2', content: '这里提到的性能对比数据，需要进一步查证引用来源 [12]。', timestamp: '2026-01-11 11:15', pageRef: 5 },
  ]);

  const [newNote, setNewNote] = useState('');
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const [isPreviewMode, setIsPreviewMode] = useState(false);

  const handleAddNote = () => {
    if (!newNote.trim()) return;
    const note: Note = {
      id: Date.now().toString(),
      content: newNote,
      timestamp: new Date().toLocaleString(),
      pageRef: 1 // TODO: Get current page from context
    };
    setNotes([note, ...notes]);
    setNewNote('');
    setIsPreviewMode(false);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50/30">
      {/* 1. Header & History Section */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 shadow-sm z-10">
        <button 
          onClick={() => setIsHistoryOpen(!isHistoryOpen)}
          className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900">我的笔记</h3>
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
              {notes.length} 条笔记
            </span>
          </div>
          {isHistoryOpen ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </button>

        <div className={cn(
          "grid transition-all duration-300 ease-in-out",
          isHistoryOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        )}>
          <div className="overflow-hidden">
             <ScrollArea className="h-[200px] border-t border-gray-100">
               <div className="p-4 space-y-3">
                 {notes.map(note => (
                   <div key={note.id} className="group relative bg-white border border-gray-200 p-3 rounded-lg hover:border-indigo-300 transition-all shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                          Page {note.pageRef}
                        </span>
                        <span className="text-[10px] text-gray-400">{note.timestamp}</span>
                      </div>
                      <div className="text-sm text-gray-700 leading-snug prose prose-sm max-w-none">
                        <ReactMarkdown>{note.content}</ReactMarkdown>
                      </div>
                      
                      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 bg-white/80 backdrop-blur rounded p-1">
                        <button className="p-1 text-gray-400 hover:text-indigo-600 rounded">
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button 
                          onClick={() => setNotes(notes.filter(n => n.id !== note.id))}
                          className="p-1 text-gray-400 hover:text-red-600 rounded"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                   </div>
                 ))}
               </div>
             </ScrollArea>
          </div>
        </div>
      </div>

      {/* 2. Editor Section */}
      <div className="flex-1 flex flex-col min-h-0 bg-white">
        <div className="p-2 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider pl-2">
            新建笔记
          </span>
          <button 
            onClick={() => setIsPreviewMode(!isPreviewMode)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors",
              isPreviewMode 
                ? "bg-indigo-100 text-indigo-700" 
                : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            )}
          >
            {isPreviewMode ? (
              <>
                <EyeOff className="w-3.5 h-3.5" />
                <span>退出预览</span>
              </>
            ) : (
              <>
                <Eye className="w-3.5 h-3.5" />
                <span>预览效果</span>
              </>
            )}
          </button>
        </div>

        <div className="flex-1 relative">
          {isPreviewMode ? (
            <div className="absolute inset-0 p-4 overflow-y-auto prose prose-sm max-w-none text-gray-700">
               {newNote ? (
                 <ReactMarkdown>{newNote}</ReactMarkdown>
               ) : (
                 <span className="text-gray-400 italic">暂无内容预览...</span>
               )}
            </div>
          ) : (
            <textarea 
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="记录想法... (支持 Markdown)"
              className="w-full h-full p-4 resize-none focus:outline-none text-sm text-gray-800 leading-relaxed"
            />
          )}
        </div>

        <div className="p-4 border-t border-gray-100 bg-gray-50/30">
          <button 
            onClick={handleAddNote}
            disabled={!newNote.trim()}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-2.5 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
          >
            <Plus className="w-4 h-4" />
            <span>添加笔记</span>
          </button>
        </div>
      </div>
    </div>
  );
};
