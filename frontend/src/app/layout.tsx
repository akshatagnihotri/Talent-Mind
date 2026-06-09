import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
  weight: ['300', '400', '500', '600', '700', '800', '900'],
});

export const metadata: Metadata = {
  title: 'TalentMind AI — Intelligent Resume Screening',
  description:
    'TalentMind AI uses 9 specialized AI agents to analyze resumes, rank candidates, and generate recruiter insights — all running locally with Ollama.',
  keywords: ['AI', 'resume screening', 'ATS', 'recruitment', 'HR tech'],
  authors: [{ name: 'TalentMind AI' }],
  openGraph: {
    title: 'TalentMind AI',
    description: 'Screen Smarter. Hire Better.',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="min-h-screen antialiased" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
        {children}
      </body>
    </html>
  );
}
