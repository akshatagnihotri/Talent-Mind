'use client';
import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface UploadedFile {
  file: File;
  id: string;
  preview?: string;
}

interface UploadZoneProps {
  onFilesChange?: (files: File[]) => void;
  multiple?: boolean;
  accept?: string;
  maxSizeMB?: number;
}

export default function UploadZone({
  onFilesChange,
  multiple = true,
  accept = '.pdf,.doc,.docx',
  maxSizeMB = 10,
}: UploadZoneProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processFiles = useCallback(
    (rawFiles: FileList | null) => {
      if (!rawFiles) return;
      setError(null);
      const validExtensions = ['pdf', 'doc', 'docx'];
      const newFiles: UploadedFile[] = [];

      Array.from(rawFiles).forEach((file) => {
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        if (!validExtensions.includes(ext)) {
          setError(`"${file.name}" is not a supported format. Use PDF or DOCX.`);
          return;
        }
        if (file.size > maxSizeMB * 1024 * 1024) {
          setError(`"${file.name}" exceeds ${maxSizeMB}MB limit.`);
          return;
        }
        newFiles.push({ file, id: `${file.name}-${Date.now()}` });
      });

      const updated = multiple ? [...files, ...newFiles] : newFiles.slice(0, 1);
      setFiles(updated);
      onFilesChange?.(updated.map((f) => f.file));
    },
    [files, multiple, maxSizeMB, onFilesChange],
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const removeFile = (id: string) => {
    const updated = files.filter((f) => f.id !== id);
    setFiles(updated);
    onFilesChange?.(updated.map((f) => f.file));
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <motion.div
        animate={{
          borderColor: isDragging ? '#6366F1' : 'rgba(99,102,241,0.35)',
          background: isDragging ? 'rgba(99,102,241,0.08)' : 'rgba(99,102,241,0.03)',
          boxShadow: isDragging ? '0 0 30px rgba(99,102,241,0.2)' : 'none',
        }}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className="upload-zone cursor-pointer relative overflow-hidden"
        style={{ padding: '48px 32px' }}
      >
        {/* Animated bg */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            background: isDragging
              ? 'radial-gradient(circle at 50% 50%, rgba(99,102,241,0.3), transparent 70%)'
              : 'none',
          }}
        />

        <label className="cursor-pointer block">
          <input
            type="file"
            className="hidden"
            multiple={multiple}
            accept={accept}
            onChange={(e) => processFiles(e.target.files)}
          />
          <div className="flex flex-col items-center gap-4 relative z-10">
            <motion.div
              animate={{ y: isDragging ? -8 : 0 }}
              transition={{ duration: 0.3 }}
              className="animate-float"
            >
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center text-4xl"
                style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)' }}
              >
                ☁️
              </div>
            </motion.div>
            <div className="text-center">
              <p className="text-lg font-semibold text-white mb-1">
                {isDragging ? 'Drop files here!' : 'Drag & drop resumes here'}
              </p>
              <p className="text-sm text-slate-400 mb-4">
                or{' '}
                <span className="font-semibold" style={{ color: '#6366F1' }}>
                  click to browse
                </span>
              </p>
              <div className="flex items-center justify-center gap-3">
                {['PDF', 'DOCX', 'DOC'].map((type) => (
                  <span
                    key={type}
                    className="px-3 py-1 rounded-lg text-xs font-semibold"
                    style={{
                      background: 'rgba(99,102,241,0.1)',
                      color: '#818CF8',
                      border: '1px solid rgba(99,102,241,0.2)',
                    }}
                  >
                    {type}
                  </span>
                ))}
                <span className="text-xs text-slate-500">up to {maxSizeMB}MB</span>
              </div>
            </div>
          </div>
        </label>
      </motion.div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm"
            style={{ background: 'rgba(244,63,94,0.1)', color: '#F43F5E', border: '1px solid rgba(244,63,94,0.2)' }}
          >
            <span>⚠️</span> {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* File list */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-2"
          >
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              {files.length} file{files.length > 1 ? 's' : ''} selected
            </p>
            {files.map((f) => (
              <motion.div
                key={f.id}
                initial={{ opacity: 0, x: -20, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: -20, scale: 0.95 }}
                className="flex items-center gap-3 px-4 py-3 rounded-xl"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
              >
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
                  style={{
                    background: f.file.name.endsWith('.pdf')
                      ? 'rgba(244,63,94,0.1)'
                      : 'rgba(99,102,241,0.1)',
                  }}
                >
                  {f.file.name.endsWith('.pdf') ? '📄' : '📝'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{f.file.name}</p>
                  <p className="text-xs text-slate-400">{formatSize(f.file.size)}</p>
                </div>
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center"
                  style={{ background: 'rgba(16,185,129,0.15)' }}
                >
                  <span className="text-emerald-400 text-xs">✓</span>
                </div>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => removeFile(f.id)}
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-rose-400 transition-colors"
                  style={{ background: 'rgba(255,255,255,0.05)' }}
                >
                  ✕
                </motion.button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
