'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Mail, ArrowRight, Loader2, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthModal } from './AuthModalContext';

interface ForgotPasswordFormProps {
  className?: string;
  isModal?: boolean;
}

export const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({ className, isModal = false }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);
  const { setAuthView, closeAuthModal } = useAuthModal();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsLoading(false);
    setIsSent(true);
  };

  const handleLoginClick = (e: React.MouseEvent) => {
    if (isModal) {
      e.preventDefault();
      setAuthView('login');
    }
  };

  return (
    <div className={cn("flex flex-col md:flex-row w-full max-w-4xl bg-white rounded-2xl shadow-2xl overflow-hidden", className)}>
      {/* Left: Image Area */}
      <div className="hidden md:flex md:w-1/2 bg-gray-900 relative p-12 flex-col justify-between">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 to-violet-900 opacity-90" />
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop')] bg-cover bg-center mix-blend-overlay opacity-50" />
        
        <div className="relative z-10">
          <h2 className="text-3xl font-bold text-white mb-4">找回密码</h2>
          <p className="text-indigo-100 text-lg leading-relaxed">
            不用担心，我们帮您重置密码。
          </p>
        </div>

        <div className="relative z-10 flex gap-2">
            <div className="w-4 h-1 bg-white/20 rounded-full" />
            <div className="w-4 h-1 bg-white/20 rounded-full" />
            <div className="w-12 h-1 bg-white/20 rounded-full" />
        </div>
      </div>

      {/* Right: Form Area */}
      <div className="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center bg-white">
        <div className="mb-8 text-center md:text-left">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">重置密码</h1>
          <p className="text-gray-500 text-sm">请输入您的注册邮箱，我们将发送重置链接</p>
        </div>

        {isSent ? (
          <div className="space-y-6 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto text-green-600">
              <Mail className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">邮件已发送</h3>
              <p className="text-gray-500 mt-2 text-sm">
                请检查您的邮箱收件箱（以及垃圾邮件文件夹），按照邮件中的指示重置密码。
              </p>
            </div>
            <button 
              onClick={() => setIsSent(false)}
              className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
            >
              重新发送
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 ml-1">邮箱地址</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input 
                  type="email" 
                  placeholder="name@example.com"
                  className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 placeholder:text-gray-400 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all duration-200 outline-none"
                  required
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              className="w-full h-12 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-medium shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:hover:translate-y-0"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <span>发送重置链接</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

        <div className="mt-8 pt-8 border-t border-gray-100 text-center">
          <Link 
            href="/login" 
            onClick={handleLoginClick}
            className="flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>返回登录</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
