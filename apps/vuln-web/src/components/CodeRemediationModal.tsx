import React, { useState, useEffect, useRef } from 'react';
import { X, ShieldCheck, ShieldAlert, Copy, Check } from 'lucide-react';
import { CodeExample } from '../lib/vuln-code';
import { useFocusTrap } from '../hooks/useFocusTrap';

interface CodeRemediationModalProps {
  onClose: () => void;
  vulnName: string;
  example: CodeExample;
}

const FEEDBACK_DURATION_MS = 2000;

export const CodeRemediationModal: React.FC<CodeRemediationModalProps> = ({ onClose, vulnName, example }) => {
  const [copied, setCopied] = useState<'vulnerable' | 'secure' | null>(null);
  const containerRef = useFocusTrap(true, onClose);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopy = async (text: string, type: 'vulnerable' | 'secure') => {
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(text);
        
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        
        setCopied(type);
        timeoutRef.current = setTimeout(() => setCopied(null), FEEDBACK_DURATION_MS);
      } else {
        // Fallback or error feedback
        alert('Clipboard API unavailable in this context.');
      }
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <div 
      className="fixed inset-0 bg-black/60 backdrop-blur-md z-[70] flex items-center justify-center p-4 animate-in fade-in duration-300"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          e.stopPropagation();
          onClose();
        }
      }}
      data-testid="modal-backdrop"
    >
      <div 
        ref={containerRef}
        tabIndex={-1}
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden border border-slate-200 dark:border-slate-800 animate-in zoom-in-95 duration-300 outline-none"
        role="dialog"
        aria-modal="true"
        aria-labelledby="remediation-modal-title"
      >
        {/* Screen reader feedback for copy actions */}
        <div className="sr-only" aria-live="polite">
          {copied ? `${copied === 'vulnerable' ? 'Vulnerable code' : 'Secure fix'} copied to clipboard` : ''}
        </div>
        
        {/* Header */}
        <div className="p-6 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 id="remediation-modal-title" className="text-xl font-bold text-slate-900 dark:text-white">Remediation Guide: {vulnName}</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Comparing Vulnerable vs. Secure Implementation</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 rounded-lg outline-none"
            aria-label="Close Remediation Guide"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto grid grid-cols-1 lg:grid-cols-2 gap-6 bg-slate-50 dark:bg-slate-950">
          
          {/* Vulnerable Code */}
          <div className="flex flex-col h-full" data-testid="vulnerable-panel">
            <div className="flex items-center justify-between mb-2 px-1">
              <span className="flex items-center gap-2 text-xs font-bold text-red-500 uppercase tracking-widest">
                <ShieldAlert className="w-3 h-3" />
                Vulnerable Code
              </span>
              <button 
                onClick={() => handleCopy(example.vulnerable, 'vulnerable')}
                className="text-slate-400 hover:text-slate-600 transition-colors"
                aria-label="Copy vulnerable code"
                data-copied={copied === 'vulnerable'}
              >
                {copied === 'vulnerable' ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
            <div className="flex-1 bg-slate-950 rounded-xl border border-red-500/20 overflow-hidden font-mono text-xs p-4 shadow-lg">
              <pre className="text-slate-300 whitespace-pre-wrap">
                <code>{example.vulnerable}</code>
              </pre>
            </div>
          </div>

          {/* Secure Code */}
          <div className="flex flex-col h-full" data-testid="secure-panel">
            <div className="flex items-center justify-between mb-2 px-1">
              <span className="flex items-center gap-2 text-xs font-bold text-emerald-500 uppercase tracking-widest">
                <ShieldCheck className="w-3 h-3" />
                Secure Fix
              </span>
              <button 
                onClick={() => handleCopy(example.secure, 'secure')}
                className="text-slate-400 hover:text-slate-600 transition-colors"
                aria-label="Copy secure fix code"
                data-copied={copied === 'secure'}
              >
                {copied === 'secure' ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>
            <div className="flex-1 bg-slate-950 rounded-xl border border-emerald-500/20 overflow-hidden font-mono text-xs p-4 shadow-lg shadow-emerald-500/5">
              <pre className="text-emerald-400 whitespace-pre-wrap">
                <code>{example.secure}</code>
              </pre>
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Note: These snippets are for educational purposes. Always adapt security fixes to your specific framework and version.
          </p>
        </div>
      </div>
    </div>
  );
};
