'use client';

import React, { useState, useRef, useCallback } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, UploadCloud, FileText, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { paperService } from '@/services/paper.service';
import { logger } from '@/lib/logger';

import { useUploadStore } from '@/store/upload.store';

interface UploadModalProps {
  // Compatibility props, optional now
  isOpen?: boolean;
  onClose?: () => void;
  onUploadSuccess?: () => void;
}

interface FileItem {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
}

export const UploadModal: React.FC<UploadModalProps> = (props) => {
  const uploadStore = useUploadStore();
  
  // Use store state if props are not provided, otherwise use props (for backward compatibility if needed)
  const isControlled = props.isOpen !== undefined;
  const show = isControlled ? props.isOpen : uploadStore.isOpen;
  
  const handleClose = useCallback(() => {
    if (isControlled && props.onClose) {
        props.onClose();
    } else {
        uploadStore.close();
    }
  }, [isControlled, props, uploadStore]);

  const handleSuccess = () => {
      // Trigger global success mechanism
      uploadStore.triggerSuccess();
      
      // If props provided, also call it (legacy support)
      if (isControlled && props.onUploadSuccess) {
          props.onUploadSuccess();
      }
  };

  const [files, setFiles] = useState<FileItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFiles = (newFiles: File[]) => {
    const validFiles = newFiles.filter(file => file.type === 'application/pdf');
    
    const newFileItems: FileItem[] = validFiles.map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      status: 'pending',
      progress: 0
    }));

    setFiles(prev => [...prev, ...newFileItems]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
    // Reset input so the same file can be selected again if needed
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const uploadFiles = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    
    if (pendingFiles.length === 0) return;

    // Mark as uploading
    setFiles(prev => prev.map(f => 
      f.status === 'pending' ? { ...f, status: 'uploading' } : f
    ));

    // Upload each file
    for (const fileItem of pendingFiles) {
        try {
            await paperService.upload(fileItem.file, uploadStore.collectionId);
            setFiles(prev => prev.map(f => 
                f.id === fileItem.id ? { ...f, status: 'success', progress: 100 } : f
            ));
            toast.success(`文件 ${fileItem.file.name} 上传成功`);
            
            // Trigger success callback
            handleSuccess();
            
        } catch (error: any) {
            logger.error('Upload failed:', error, 'UploadModal');
            setFiles(prev => prev.map(f => 
                f.id === fileItem.id ? { ...f, status: 'error', progress: 0 } : f
            ));
            toast.error(`文件 ${fileItem.file.name} 上传失败: ${error.message || '未知错误'}`);
        }
    }
  };

  return (
    <Dialog.Root open={show} onOpenChange={(open) => !open && handleClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in" />
        <Dialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] bg-white rounded-xl shadow-2xl outline-none animate-in fade-in zoom-in-95 duration-200">
          
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-100">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              上传论文
            </Dialog.Title>
            <Dialog.Close asChild>
              <button onClick={handleClose} className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              "mt-2 flex flex-col items-center justify-center w-full h-48 rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer",
              isDragging 
                ? "border-indigo-500 bg-indigo-50/50" 
                : "border-gray-200 bg-gray-50/50 hover:bg-gray-50 hover:border-gray-300"
            )}
          >
            <input 
              ref={fileInputRef}
              type="file" 
              accept=".pdf"
              multiple 
              className="hidden" 
              onChange={handleFileSelect}
            />
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <div className={cn(
                "w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors",
                isDragging ? "bg-indigo-100 text-indigo-600" : "bg-gray-100 text-gray-400"
              )}>
                <UploadCloud className="w-6 h-6" />
              </div>
              <p className="mb-1 text-sm font-medium text-gray-700">
                <span className="text-indigo-600 hover:underline">点击上传</span> 或拖拽文件到这里
              </p>
              <p className="text-xs text-gray-500">支持 PDF 格式 (最大 20MB)</p>
            </div>
          </div>

          {files.length > 0 && (
            <div className="mt-4 space-y-3 max-h-[240px] overflow-y-auto pr-2">
              {files.map((file) => (
                <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100 group">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
                      file.status === 'success' ? "bg-green-100 text-green-600" :
                      file.status === 'error' ? "bg-red-100 text-red-600" :
                      "bg-white border border-gray-200 text-gray-500"
                    )}>
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span className="text-sm font-medium text-gray-700 truncate max-w-[200px] block">
                        {file.file.name}
                      </span>
                      <span className="text-xs text-gray-500">
                        {(file.file.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {file.status === 'pending' && (
                      <button 
                        onClick={(e) => { e.stopPropagation(); removeFile(file.id); }}
                        className="text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                    {file.status === 'uploading' && (
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-indigo-600 transition-all duration-300 rounded-full"
                            style={{ width: `${file.progress}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-indigo-600">{file.progress}%</span>
                      </div>
                    )}
                    {file.status === 'success' && (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    )}
                    {file.status === 'error' && (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-6 flex justify-end gap-3">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              取消
            </button>
            <button
              onClick={uploadFiles}
              disabled={files.length === 0 || files.every(f => f.status === 'success')}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-sm shadow-indigo-200 transition-all"
            >
              {files.some(f => f.status === 'uploading') ? '上传中...' : '开始上传'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
