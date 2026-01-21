'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { BookOpen, Search, Upload, Bookmark, LogIn, LogOut, User as UserIcon } from 'lucide-react';
import { useAuthModal } from '@/components/auth/AuthModalContext';
import { useAuthStore } from '@/store/use-auth-store';
import { useUploadStore } from '@/store/upload.store';
import { toast } from 'sonner';

interface NavbarProps {
  className?: string;
  onCollectionsClick?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ className, onCollectionsClick }) => {
  const { openAuthModal } = useAuthModal();
  const { user, isAuthenticated, logout } = useAuthStore();
  const uploadStore = useUploadStore();

  const handleUploadClick = () => {
    uploadStore.open();
  };

  const handleLogout = () => {
    logout();
    toast.success('已退出登录');
  };

  return (
    <header className={cn(
      "w-full h-16 border-b border-gray-100 flex items-center justify-between px-6 lg:px-12 bg-white/80 backdrop-blur-md sticky top-0 z-50 transition-all duration-300 relative", 
      className
    )}>
      {/* Logo Area */}
      <Link href="/" className="flex items-center gap-3 group z-10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-indigo-200 group-hover:shadow-indigo-300 transition-all duration-300 group-hover:scale-105">
          <BookOpen className="w-5 h-5" />
        </div>
        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
          DeepPaper
        </span>
      </Link>

      {/* Navigation Links - Centered Group */}
      <nav className="hidden md:flex items-center gap-2 p-1 bg-gray-100/50 rounded-full border border-gray-200/50 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <NavItem href="/dashboard" icon={<Search className="w-4 h-4" />}>搜索论文</NavItem>
        <NavItem 
          onClick={handleUploadClick}
          icon={<Upload className="w-4 h-4" />}
        >
          上传论文
        </NavItem>
        <NavItem 
          href={onCollectionsClick ? undefined : "/dashboard"} 
          onClick={onCollectionsClick}
          icon={<Bookmark className="w-4 h-4" />}
        >
          收藏夹
        </NavItem>
      </nav>

      {/* Auth Action */}
      <div className="flex-shrink-0 z-10">
        {isAuthenticated && user ? (
          <div className="flex items-center gap-4">
             <div className="flex items-center gap-2 text-sm text-gray-700">
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
                  {user.full_name?.[0]?.toUpperCase() || user.email[0].toUpperCase()}
                </div>
                <span className="hidden sm:inline">{user.full_name || user.email}</span>
             </div>
             <button 
               onClick={handleLogout}
               className="flex items-center gap-2 px-3 py-2 rounded-full text-gray-500 hover:text-red-600 hover:bg-red-50 transition-all duration-200"
               title="退出登录"
             >
               <LogOut className="w-4 h-4" />
             </button>
          </div>
        ) : (
          <button 
            onClick={() => openAuthModal('login')}
            className="flex items-center gap-2 h-10 px-6 rounded-full bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-all duration-300 shadow-md hover:shadow-lg active:scale-95"
          >
            <LogIn className="w-4 h-4" />
            <span>登录</span>
          </button>
        )}
      </div>
    </header>
  );
};

const NavItem = ({ href, children, icon, onClick }: { href?: string; children: React.ReactNode; icon?: React.ReactNode; onClick?: () => void }) => {
  if (onClick) {
    return (
      <button 
        onClick={onClick}
        className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-white hover:shadow-sm transition-all duration-200"
      >
        {icon}
        <span>{children}</span>
      </button>
    );
  }

  return (
    <Link 
      href={href || '#'}
      className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-white hover:shadow-sm transition-all duration-200"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
