'use client';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
  { href: '/dashboard', icon: '🏠', label: 'Dashboard' },
  { href: '/upload', icon: '📤', label: 'Upload Resume' },
  { href: '/dashboard/ats', icon: '🎯', label: 'ATS Analysis' },
  { href: '/dashboard/match', icon: '🔗', label: 'Job Match' },
  { href: '/dashboard/ranking', icon: '🏆', label: 'Candidate Ranking' },
  { href: '/dashboard/recruiter', icon: '📋', label: 'Recruiter Notes' },
  { href: '/dashboard/analytics', icon: '📊', label: 'Analytics' },
  { href: '/copilot', icon: '🤖', label: 'Copilot Chat' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      initial={{ x: -280 }}
      animate={{ x: 0, width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="fixed left-0 top-0 bottom-0 z-40 flex flex-col sidebar"
      style={{ width: collapsed ? 72 : 260 }}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-white/5">
        <Link href="/" className="flex items-center gap-3 min-w-0">
          <motion.div
            whileHover={{ scale: 1.05, rotate: 5 }}
            className="w-9 h-9 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)' }}
          >
            🧠
          </motion.div>
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="text-base font-bold text-white whitespace-nowrap overflow-hidden"
              >
                TalentMind <span style={{ color: '#6366F1' }}>AI</span>
              </motion.span>
            )}
          </AnimatePresence>
        </Link>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto flex flex-col gap-1">
        {navItems.map((item, i) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05, duration: 0.3 }}
                whileHover={{ x: 2, scale: 1.01 }}
                className="nav-item relative"
                style={{
                  background: isActive ? 'rgba(99,102,241,0.15)' : undefined,
                  color: isActive ? '#6366F1' : undefined,
                  fontWeight: isActive ? 600 : 500,
                  justifyContent: collapsed ? 'center' : undefined,
                  padding: collapsed ? '10px' : undefined,
                }}
                title={collapsed ? item.label : undefined}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="absolute left-0 top-1 bottom-1 w-1 rounded-full"
                    style={{ background: '#6366F1' }}
                  />
                )}
                <span className="text-lg flex-shrink-0">{item.icon}</span>
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="whitespace-nowrap text-sm"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-white/5 p-3">
        {/* User profile */}
        <motion.div
          whileHover={{ scale: 1.02 }}
          onClick={() => alert('Profile settings coming soon!')}
          className="flex items-center gap-3 px-2 py-2 rounded-xl cursor-pointer mb-2 transition-all"
          style={{ background: 'rgba(255,255,255,0.03)' }}
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
            style={{ background: 'linear-gradient(135deg,#6366F1,#8B5CF6)' }}
          >
            A
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="min-w-0 flex-1"
              >
                <p className="text-sm font-semibold text-white truncate">Admin User</p>
                <p className="text-xs text-slate-500 truncate">admin@talentmind.ai</p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Collapse toggle */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-white transition-colors text-sm"
          style={{ background: 'rgba(255,255,255,0.04)', justifyContent: collapsed ? 'center' : undefined }}
        >
          <span className="text-base" style={{ transform: collapsed ? 'rotate(180deg)' : 'none', display: 'inline-block', transition: 'transform 0.3s' }}>
            ◀
          </span>
          <AnimatePresence>
            {!collapsed && (
              <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                Collapse
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>
      </div>
    </motion.aside>
  );
}
