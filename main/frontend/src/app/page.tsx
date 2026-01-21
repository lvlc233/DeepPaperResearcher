'use client';

import React from 'react';
import { Navbar } from "@/components/layout/Navbar";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col bg-background">
      <Navbar />
      
      <div className="flex-1 flex flex-col items-center justify-center relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 z-0 opacity-30">
             <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl animate-blob"></div>
             <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000"></div>
             <div className="absolute -bottom-8 left-1/3 w-96 h-96 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-4000"></div>
        </div>

        <div className="z-10 text-center space-y-8 max-w-4xl px-4">
            <h1 className="text-6xl font-bold tracking-tight text-foreground">
              Deep<span className="text-primary">Paper</span> Researcher
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              您的智能学术科研助手。深度解析论文，构建知识图谱，加速科研创新。
            </p>
        </div>
      </div>
    </main>
  );
}
