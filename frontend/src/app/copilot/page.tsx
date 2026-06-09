'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import apiClient from '@/lib/api';
import Navbar from '@/components/Navbar';

interface Candidate {
  id: string;
  name: string;
  email: string;
  resume_id: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function CopilotPage() {
  const router = useRouter();
  const [authenticated, setAuthenticated] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I am your AI Recruiter Copilot. Select a candidate on the left, and ask me anything about their qualifications, skills, gaps, or work history.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Check auth and fetch candidates
  useEffect(() => {
    const token = apiClient.getToken();
    if (!token) {
      router.push('/auth');
      return;
    }
    setAuthenticated(true);

    const fetchCandidates = async () => {
      try {
        const resumes = await apiClient.getResumes() as any[];
        const list = resumes
          .filter((r) => r.candidate)
          .map((r) => ({
            id: r.candidate.id,
            name: r.candidate.name,
            email: r.candidate.email,
            resume_id: r.id,
          }));
        setCandidates(list);
        if (list.length > 0) {
          setSelectedCandidate(list[0]);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchCandidates();
  }, [router]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userText }]);
    setLoading(true);

    try {
      // Setup system context prompt
      const context = selectedCandidate
        ? `We are discussing candidate "${selectedCandidate.name}" with email "${selectedCandidate.email}".`
        : `No candidate is currently selected.`;
      
      const prompt = `${context}\n\nRecruiter asks: ${userText}`;
      
      let responseText = '';
      if (selectedCandidate) {
        const chatResponse = await apiClient.chatWithCopilot(selectedCandidate.resume_id, userText) as any;
        responseText = chatResponse.response || 'No response received from the AI.';
      } else {
        responseText = 'Please select a candidate from the sidebar first to chat about their resume.';
      }

      // Add a slight typing delay to make it feel natural
      await new Promise((r) => setTimeout(r, 600));
      setMessages((prev) => [...prev, { role: 'assistant', content: responseText }]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an issue retrieving that candidate details. Make sure they have been fully analyzed.' }]);
    } finally {
      setLoading(false);
    }
  };

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
    <div className="animated-bg min-h-screen text-slate-100 flex flex-col">
      <Navbar />

      <div className="flex-1 max-w-7xl mx-auto w-full px-6 pt-24 pb-8 flex gap-8 h-[calc(100vh-6rem)] overflow-hidden">
        {/* Candidates list Sidebar */}
        <div className="w-80 glass-card p-6 bg-slate-900/40 border-white/5 flex flex-col h-full overflow-hidden flex-shrink-0">
          <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
            <span>👥</span> Candidates Pool
          </h2>
          
          <div className="flex-1 overflow-y-auto space-y-2 pr-2">
            {candidates.map((cand) => (
              <div
                key={cand.id}
                onClick={() => setSelectedCandidate(cand)}
                className="p-3.5 rounded-xl cursor-pointer border transition-all text-left"
                style={{
                  background: selectedCandidate?.id === cand.id ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.03)',
                  borderColor: selectedCandidate?.id === cand.id ? '#6366F1' : 'rgba(255,255,255,0.06)',
                }}
              >
                <p className="text-sm font-semibold text-white truncate">{cand.name}</p>
                <p className="text-xs text-slate-500 truncate mt-0.5">{cand.email}</p>
              </div>
            ))}
            {candidates.length === 0 && (
              <div className="text-center py-10 text-slate-500 text-sm">
                No candidates available. Go upload a resume.
              </div>
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 glass-card bg-slate-900/40 border-white/5 flex flex-col h-full overflow-hidden relative">
          {/* Active candidate header */}
          <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-slate-900/30">
            <div>
              <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Active Conversation</span>
              <h3 className="text-base font-bold text-white mt-0.5">
                {selectedCandidate ? `Chatting about: ${selectedCandidate.name}` : 'AI Recruiter Copilot'}
              </h3>
            </div>
            {selectedCandidate && (
              <Link href={`/dashboard/ats?id=${selectedCandidate.resume_id}`}>
                <span className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold cursor-pointer">
                  View full profile →
                </span>
              </Link>
            )}
          </div>

          {/* Messages list */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 flex flex-col">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}
              >
                <p className="text-sm leading-relaxed text-white whitespace-pre-wrap">{msg.content}</p>
              </div>
            ))}

            {loading && (
              <div className="chat-bubble-ai flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0s' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0.15s' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0.3s' }} />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input form */}
          <form onSubmit={handleSend} className="p-4 border-t border-white/5 bg-slate-900/30 flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={selectedCandidate ? `Ask something about ${selectedCandidate.name}...` : 'Select a candidate to start chatting'}
              disabled={!selectedCandidate || loading}
              className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!selectedCandidate || !input.trim() || loading}
              className="btn-primary py-3 px-6 rounded-xl text-sm font-semibold flex items-center gap-2 disabled:opacity-50 shadow-none hover:shadow-none hover:translate-y-0"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
