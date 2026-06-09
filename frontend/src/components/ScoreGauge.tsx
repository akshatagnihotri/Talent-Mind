'use client';
import { useEffect, useState } from 'react';

interface ScoreGaugeProps {
  score: number;
  size?: number;
  label?: string;
  color?: string;
}

export default function ScoreGauge({ score, size = 200, label = 'ATS Score', color }: ScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      let current = 0;
      const increment = score / 60;
      const interval = setInterval(() => {
        current += increment;
        if (current >= score) {
          setAnimatedScore(score);
          clearInterval(interval);
        } else {
          setAnimatedScore(Math.floor(current));
        }
      }, 16);
      return () => clearInterval(interval);
    }, 300);
    return () => clearTimeout(timer);
  }, [score]);

  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference * 0.75;
  const strokeDasharray = `${circumference * 0.75} ${circumference * 0.25}`;

  const getColor = () => {
    if (color) return color;
    if (score >= 80) return '#10B981';
    if (score >= 60) return '#6366F1';
    if (score >= 40) return '#F59E0B';
    return '#F43F5E';
  };

  const scoreColor = getColor();

  const getLabel = () => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Average';
    return 'Needs Work';
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div style={{ width: size, height: size }} className="relative">
        {/* Glow effect */}
        <div
          className="absolute inset-0 rounded-full blur-2xl opacity-20"
          style={{ background: scoreColor }}
        />
        <svg width={size} height={size} className="-rotate-[135deg] relative z-10">
          {/* Background track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="10"
            strokeDasharray={strokeDasharray}
            strokeLinecap="round"
          />
          {/* Score arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={scoreColor}
            strokeWidth="10"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1.5s ease, stroke 0.5s ease', filter: `drop-shadow(0 0 6px ${scoreColor})` }}
          />
        </svg>
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-bold leading-none" style={{ fontSize: size * 0.2, color: scoreColor }}>
            {animatedScore}
          </span>
          <span className="text-slate-400 mt-1" style={{ fontSize: size * 0.07 }}>/100</span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-sm font-semibold text-slate-300">{label}</p>
        <p className="text-xs text-slate-500">{getLabel()}</p>
      </div>
    </div>
  );
}
