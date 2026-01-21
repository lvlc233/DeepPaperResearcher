import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthModalProvider } from "@/components/auth/AuthModalContext";
import { AuthModal } from "@/components/auth/AuthModal";
import { UploadModal } from "@/components/upload/UploadModal";
import { GlobalErrorListener } from "@/components/providers/GlobalErrorListener";
import { Toaster } from 'sonner';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DeepPaper - AI 驱动的论文阅读助手",
  description: "基于大模型的深度论文解析与知识管理平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <GlobalErrorListener />
        <AuthModalProvider>
          {children}
          <AuthModal />
          <UploadModal />
        </AuthModalProvider>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
