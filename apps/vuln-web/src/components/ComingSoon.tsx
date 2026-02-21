import React from 'react';
import { Link } from 'react-router-dom';
import { HardHat } from 'lucide-react';

export const ComingSoon: React.FC<{ title: string; vertical: string }> = ({ title, vertical }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full py-24 text-center bg-slate-50 dark:bg-slate-900">
      <div className="p-6 bg-yellow-100 dark:bg-yellow-900/30 rounded-full mb-6">
        <HardHat className="w-12 h-12 text-yellow-600 dark:text-yellow-500" />
      </div>
      <h1 className="text-3xl font-bold text-slate-800 dark:text-white">{title} Portal</h1>
      <p className="mt-2 text-slate-600 dark:text-slate-400">
        The <span className="font-semibold">{vertical}</span> vertical is under construction.
      </p>
      <Link 
        to="/" 
        className="mt-8 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
      >
        ← Back to Directory
      </Link>
    </div>
  );
};
