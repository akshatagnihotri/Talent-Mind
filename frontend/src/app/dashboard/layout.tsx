'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import apiClient from '@/lib/api';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const token = apiClient.getToken();
    if (!token) {
      router.push('/auth');
    } else {
      setAuthenticated(true);
    }
  }, [router]);

  if (!authenticated) {
    return (
      <div className="min-h-screen animated-bg flex items-center justify-center text-slate-100">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Verifying session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen animated-bg flex text-slate-100">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content area */}
      <main className="flex-1 min-h-screen pl-24 md:pl-[280px] pr-6 py-8 transition-all duration-300">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
