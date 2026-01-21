'use client';

import { useEffect } from 'react';
import { logger } from '@/lib/logger';
import { Button } from '@/components/ui/button';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    logger.error('Global Error', error, 'GlobalBoundary');
  }, [error]);

  return (
    <html>
      <body>
        <div className="flex flex-col items-center justify-center min-h-screen p-8 text-center bg-gray-50">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">系统严重错误</h2>
          <p className="text-gray-500 mb-8">
            发生了一个无法恢复的错误。
          </p>
          <Button onClick={() => reset()}>重启应用</Button>
        </div>
      </body>
    </html>
  );
}
