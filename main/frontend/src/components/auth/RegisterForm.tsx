'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Mail, Lock, User as UserIcon, ArrowRight, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthModal } from './AuthModalContext';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/use-auth-store';
import { toast } from 'sonner';

interface RegisterFormProps {
  className?: string;
  isModal?: boolean;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ className, isModal = false }) => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: ''
  });
  
  const { setAuthView, closeAuthModal } = useAuthModal();
  const login = useAuthStore((state) => state.login);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      // 1. Register
      const user = await authService.register(formData.email, formData.password, formData.full_name);
      
      // 2. Auto Login (if API doesn't return token on register, we might need to login manually)
      // Assuming register returns User. We need token.
      // So we call login immediately.
      const loginResponse = await authService.login(formData.email, formData.password);
      
      login(loginResponse.user, loginResponse.access_token);
      toast.success('注册成功');
      
      if (isModal) {
        closeAuthModal();
      }
      
      router.push('/dashboard');
    } catch (error: any) {
      const errorMessage = error.message || '注册失败';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
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
          <h2 className="text-3xl font-bold text-white mb-4">加入 DeepPaper</h2>
          <p className="text-indigo-100 text-lg leading-relaxed">
            创建您的账户，开始探索海量学术资源。
          </p>
        </div>

        <div className="relative z-10 flex gap-2">
            <div className="w-4 h-1 bg-white/20 rounded-full" />
            <div className="w-12 h-1 bg-white/20 rounded-full" />
            <div className="w-4 h-1 bg-white/20 rounded-full" />
        </div>
      </div>

      {/* Right: Form Area */}
      <div className="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center bg-white">
        <div className="mb-8 text-center md:text-left">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">创建新账户</h1>
          <p className="text-gray-500 text-sm">填写以下信息完成注册</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 ml-1">用户名</label>
            <div className="relative">
              <UserIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input 
                type="text" 
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="your_username"
                className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 placeholder:text-gray-400 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all duration-200 outline-none"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 ml-1">邮箱地址</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input 
                type="email" 
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="name@example.com"
                className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 placeholder:text-gray-400 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all duration-200 outline-none"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 ml-1">密码</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input 
                type="password" 
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 placeholder:text-gray-400 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all duration-200 outline-none"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full h-12 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-indigo-200 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <span>注册账户</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            已有账户？{' '}
            {isModal ? (
              <button 
                onClick={handleLoginClick}
                className="text-indigo-600 font-medium hover:text-indigo-700 transition-colors"
              >
                立即登录
              </button>
            ) : (
              <a href="/login" className="text-indigo-600 font-medium hover:text-indigo-700 transition-colors">
                立即登录
              </a>
            )}
          </p>
        </div>
      </div>
    </div>
  );
};
