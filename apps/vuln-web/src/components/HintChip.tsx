import React from 'react';
import { HelpCircle } from 'lucide-react';
import { useSettings } from './SettingsProvider';

interface HintChipProps {
  label: string;
  onClick?: () => void;
  className?: string;
}

export const HintChip: React.FC<HintChipProps> = ({ label, onClick, className }) => {
  const { showHints } = useSettings();

  if (!showHints) return null;

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-md text-[10px] font-bold uppercase tracking-wider border border-yellow-200 dark:border-yellow-900/50 hover:bg-yellow-200 dark:hover:bg-yellow-900/50 transition-all animate-in zoom-in-90 duration-300 shadow-sm ${className}`}
      title={`Vulnerability Hint: ${label}`}
    >
      <HelpCircle className="w-3 h-3" />
      Hint: {label}
    </button>
  );
};
