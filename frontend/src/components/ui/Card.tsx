import React, { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glass?: boolean;
  onClick?: () => void;
}

export function Card({ children, className = '', hover = false, glass = false, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={`
        rounded-2xl border border-slate-200 dark:border-slate-700
        ${glass ? 'glass' : 'bg-white dark:bg-slate-800'}
        ${hover ? 'hover-card cursor-pointer' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`px-6 py-4 border-b border-slate-100 dark:border-slate-700 ${className}`}>
      {children}
    </div>
  );
}

export function CardContent({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`px-6 py-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`px-6 py-4 border-t border-slate-100 dark:border-slate-700 ${className}`}>
      {children}
    </div>
  );
}

