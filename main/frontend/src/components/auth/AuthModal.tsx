'use client';

import React from 'react';
import { useAuthModal } from './AuthModalContext';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';
import { ForgotPasswordForm } from './ForgotPasswordForm';

export const AuthModal: React.FC = () => {
  const { isOpen, closeAuthModal, view } = useAuthModal();

  return (
    <Dialog open={isOpen} onOpenChange={closeAuthModal}>
      <DialogContent className="max-w-4xl p-0 overflow-hidden bg-transparent border-none shadow-none sm:rounded-2xl">
        <div className="w-full">
          {view === 'login' && <LoginForm isModal />}
          {view === 'register' && <RegisterForm isModal />}
          {view === 'forgot-password' && <ForgotPasswordForm isModal />}
        </div>
      </DialogContent>
    </Dialog>
  );
};
