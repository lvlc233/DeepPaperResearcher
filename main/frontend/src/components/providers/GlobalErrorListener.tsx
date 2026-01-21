'use client';

import { useEffect } from 'react';
import { logger } from '@/lib/logger';

export function GlobalErrorListener() {
  useEffect(() => {
    // Catch unhandled promise rejections (e.g. async errors not awaited or caught)
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      logger.error('Unhandled Promise Rejection', event.reason, 'Window');
      // We don't prevent default here to let browser console still show it if needed,
      // but in some cases you might want event.preventDefault();
    };

    // Catch global synchronous errors
    const handleError = (event: ErrorEvent) => {
      logger.error('Uncaught Exception', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
      }, 'Window');
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    window.addEventListener('error', handleError);

    logger.info('Global Error Listener Initialized', null, 'System');

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('error', handleError);
    };
  }, []);

  return null;
}
