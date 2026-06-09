'use client';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/upload', label: 'Upload' },
  { href: '/dashboard/ranking', label: 'Ranking' },
  { href: '/dashboard/analytics', label: 'Analytics' },
  { href: '/copilot', label: 'Copilot' },
];

export default function Navbar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userDropdown, setUserDropdown] = useState(false);

  return (
    <motion.nav
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: 'rgba(10, 15, 30, 0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-xl"
              style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)' }}
            >
              🧠
            </motion.div>
            <span className="text-lg font-bold text-white">
              TalentMind <span style={{ color: '#6366F1' }}>AI</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link key={link.href} href={link.href}>
                <motion.span
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer block"
                  style={{
                    color: pathname === link.href ? '#6366F1' : '#94A3B8',
                    background: pathname === link.href ? 'rgba(99,102,241,0.12)' : 'transparent',
                  }}
                >
                  {link.label}
                </motion.span>
              </Link>
            ))}
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-3">
            {/* Mode toggle */}
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => alert('Theme toggle coming soon!')}
              className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-400 hover:text-white transition-colors"
              style={{ background: 'rgba(255,255,255,0.05)' }}
              title="Toggle theme"
            >
              🌙
            </motion.button>

            {/* User dropdown */}
            <div className="relative">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setUserDropdown(!userDropdown)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl transition-all"
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
              >
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold"
                  style={{ background: 'linear-gradient(135deg,#6366F1,#8B5CF6)' }}
                >
                  A
                </div>
                <span className="text-sm text-white hidden sm:block">Admin</span>
                <span className="text-slate-400 text-xs">▾</span>
              </motion.button>

              <AnimatePresence>
                {userDropdown && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -5 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -5 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-52 rounded-xl overflow-hidden z-50"
                    style={{
                      background: 'rgba(15,23,42,0.97)',
                      border: '1px solid rgba(255,255,255,0.08)',
                      backdropFilter: 'blur(20px)',
                    }}
                  >
                    <div className="px-4 py-3 border-b border-white/5">
                      <p className="text-sm font-semibold text-white">Admin User</p>
                      <p className="text-xs text-slate-400">admin@talentmind.ai</p>
                    </div>
                    {[
                      { icon: '⚙️', label: 'Settings', action: () => alert('Settings coming soon!') },
                      { icon: '📊', label: 'Analytics', href: '/dashboard/analytics' },
                      { icon: '🔑', label: 'API Keys', action: () => alert('API Keys coming soon!') },
                    ].map((item) => (
                      item.href ? (
                        <Link key={item.label} href={item.href}>
                          <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-colors text-left">
                            <span>{item.icon}</span>
                            {item.label}
                          </button>
                        </Link>
                      ) : (
                        <button
                          key={item.label}
                          onClick={item.action}
                          className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-colors text-left"
                        >
                          <span>{item.icon}</span>
                          {item.label}
                        </button>
                      )
                    ))}
                    <div className="border-t border-white/5">
                      <Link href="/auth">
                        <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-rose-400 hover:bg-rose-500/10 transition-colors text-left">
                          <span>🚪</span> Sign Out
                        </button>
                      </Link>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Mobile hamburger */}
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden w-9 h-9 rounded-lg flex flex-col items-center justify-center gap-1.5"
              style={{ background: 'rgba(255,255,255,0.05)' }}
            >
              <span
                className="block w-5 h-0.5 bg-white transition-all"
                style={{ transform: menuOpen ? 'rotate(45deg) translateY(7px)' : 'none' }}
              />
              <span
                className="block w-5 h-0.5 bg-white transition-all"
                style={{ opacity: menuOpen ? 0 : 1 }}
              />
              <span
                className="block w-5 h-0.5 bg-white transition-all"
                style={{ transform: menuOpen ? 'rotate(-45deg) translateY(-7px)' : 'none' }}
              />
            </motion.button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden overflow-hidden"
            style={{ background: 'rgba(10,15,30,0.97)', borderTop: '1px solid rgba(255,255,255,0.05)' }}
          >
            <div className="px-4 py-3 flex flex-col gap-1">
              {navLinks.map((link) => (
                <Link key={link.href} href={link.href} onClick={() => setMenuOpen(false)}>
                  <span
                    className="block px-4 py-3 rounded-lg text-sm font-medium transition-colors"
                    style={{
                      color: pathname === link.href ? '#6366F1' : '#94A3B8',
                      background: pathname === link.href ? 'rgba(99,102,241,0.1)' : 'transparent',
                    }}
                  >
                    {link.label}
                  </span>
                </Link>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
