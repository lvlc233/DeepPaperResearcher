'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

type AuthView = 'login' | 'register' | 'forgot-password';

interface AuthModalContextType {
  isOpen: boolean;
  view: AuthView;
  openAuthModal: (view?: AuthView) => void;
  closeAuthModal: () => void;
  setAuthView: (view: AuthView) => void;
}

const AuthModalContext = createContext<AuthModalContextType | undefined>(undefined);

export const AuthModalProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [view, setView] = useState<AuthView>('login');

  const openAuthModal = (initialView: AuthView = 'login') => {
    setView(initialView);
    setIsOpen(true);
  };

  const closeAuthModal = () => {
    setIsOpen(false);
  };

  // Listen for unauthorized events to automatically open login modal
  React.useEffect(() => {
    const handleUnauthorized = () => {
      openAuthModal('login');
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, []);

  return (
    <AuthModalContext.Provider value={{ isOpen, view, openAuthModal, closeAuthModal, setAuthView: setView }}>
      {children}
    </AuthModalContext.Provider>
  );
};

export const useAuthModal = () => {
  const context = useContext(AuthModalContext);
  if (context === undefined) {
    throw new Error('useAuthModal must be used within a AuthModalProvider');
  }
  return context;
};
