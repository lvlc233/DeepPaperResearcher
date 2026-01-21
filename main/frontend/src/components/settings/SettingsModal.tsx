'use client';

import React, { useState } from 'react';
import { X, User, Settings, Shield, Bell, Database } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type SettingsTab = 'general' | 'account' | 'privacy' | 'data';

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general');

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 animate-in fade-in duration-200" />
        <Dialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-3xl translate-x-[-50%] translate-y-[-50%] outline-none animate-in zoom-in-95 slide-in-from-bottom-4 duration-300">
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-100 flex h-[600px]">
            
            {/* Left Sidebar */}
            <div className="w-64 bg-gray-50/50 border-r border-gray-100 p-6 flex flex-col">
              <h2 className="text-lg font-bold text-gray-900 mb-6 px-2">设置</h2>
              
              <nav className="space-y-1 flex-1">
                <TabButton 
                  active={activeTab === 'general'} 
                  onClick={() => setActiveTab('general')}
                  icon={<Settings className="w-4 h-4" />}
                  label="通用设置"
                />
                <TabButton 
                  active={activeTab === 'account'} 
                  onClick={() => setActiveTab('account')}
                  icon={<User className="w-4 h-4" />}
                  label="账号与偏好"
                />
                <TabButton 
                  active={activeTab === 'privacy'} 
                  onClick={() => setActiveTab('privacy')}
                  icon={<Shield className="w-4 h-4" />}
                  label="隐私安全"
                />
                <TabButton 
                  active={activeTab === 'data'} 
                  onClick={() => setActiveTab('data')}
                  icon={<Database className="w-4 h-4" />}
                  label="数据管理"
                />
              </nav>

              <div className="text-xs text-gray-400 px-2">
                Version 1.0.0
              </div>
            </div>

            {/* Right Content Area */}
            <div className="flex-1 flex flex-col min-w-0 bg-white">
              {/* Header */}
              <div className="h-16 border-b border-gray-100 flex items-center justify-between px-8">
                <h3 className="text-base font-semibold text-gray-900">
                  {activeTab === 'general' && "通用配置"}
                  {activeTab === 'account' && "账号设置"}
                  {activeTab === 'privacy' && "隐私与安全"}
                  {activeTab === 'data' && "数据管理"}
                </h3>
                <button 
                  onClick={onClose}
                  className="p-2 -mr-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content Scrollable */}
              <div className="flex-1 overflow-y-auto p-8">
                {activeTab === 'general' && <GeneralSettings />}
                {activeTab === 'account' && <div className="text-gray-400 text-sm">暂无账号设置项</div>}
                {activeTab === 'privacy' && <div className="text-gray-400 text-sm">暂无隐私设置项</div>}
                {activeTab === 'data' && <div className="text-gray-400 text-sm">暂无数据管理项</div>}
              </div>

              {/* Footer Actions */}
              <div className="p-6 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
                <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition-colors">
                  取消
                </button>
                <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm shadow-indigo-200 transition-colors">
                  保存更改
                </button>
              </div>
            </div>

          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

const TabButton = ({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) => (
  <button
    onClick={onClick}
    className={cn(
      "w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200",
      active 
        ? "bg-white text-indigo-600 shadow-sm border border-gray-100" 
        : "text-gray-600 hover:bg-white/50 hover:text-gray-900"
    )}
  >
    <span className={cn(active ? "text-indigo-600" : "text-gray-400")}>{icon}</span>
    {label}
  </button>
);

const GeneralSettings = () => (
  <div className="space-y-8">
    {/* Section 1 */}
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-gray-900 border-b border-gray-100 pb-2">界面显示</h4>
      
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="text-sm font-medium text-gray-700">深色模式</div>
          <div className="text-xs text-gray-500">切换应用的主题颜色为深色</div>
        </div>
        <Switch checked={false} onCheckedChange={() => {}} />
      </div>

      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="text-sm font-medium text-gray-700">紧凑模式</div>
          <div className="text-xs text-gray-500">减小界面间距，显示更多内容</div>
        </div>
        <Switch checked={false} onCheckedChange={() => {}} />
      </div>
    </div>

    {/* Section 2 */}
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-gray-900 border-b border-gray-100 pb-2">语言与地区</h4>
      
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="text-sm font-medium text-gray-700">系统语言</div>
          <div className="text-xs text-gray-500">选择应用的显示语言</div>
        </div>
        <select className="text-sm border-gray-200 rounded-lg focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 p-1.5">
            <option>简体中文</option>
            <option>English</option>
        </select>
      </div>
    </div>
  </div>
);
