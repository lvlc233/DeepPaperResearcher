'use client';

import { useEffect } from 'react';
import { logger } from '@/lib/logger';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to our unified logger
    logger.error('Uncaught Runtime Error', error, 'ReactBoundary');
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] p-8 text-center">
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-6">
        <AlertTriangle className="w-8 h-8 text-red-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">出错了</h2>
      <p className="text-gray-500 mb-8 max-w-md">
        抱歉，应用程序遇到了一些问题。我们已经记录了这个错误。
      </p>
      
      {process.env.NODE_ENV === 'development' && (
        <div className="mb-8 p-4 bg-gray-100 rounded-lg text-left w-full max-w-2xl overflow-auto text-xs font-mono">
            <p className="font-bold text-red-600 mb-2">{error.message}</p>
            <pre>{error.stack}</pre>
        </div>
      )}

      <Button
        onClick={() => reset()}
        className="gap-2"
      >
        <RefreshCw className="w-4 h-4" />
        尝试恢复
      </Button>
    </div>
  );
}
