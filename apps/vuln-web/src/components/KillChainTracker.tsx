import React, { useState, useEffect, useRef } from 'react';
import { Trophy, CheckCircle2, Circle, Target, ChevronDown } from 'lucide-react';
import { KILL_CHAIN_OBJECTIVES } from '../lib/objectives';
import { useAttackLog } from '../hooks/useAttackLog';
import { useCustomEvent } from '../hooks/useCustomEvent';
import { CHIMERA_EVENTS } from '../lib/config';

const STORAGE_KEY = 'chimera-kill-chain';
const TOAST_DURATION_MS = 5000;

export const KillChainTracker: React.FC<{ showLauncher?: boolean }> = ({ showLauncher = true }) => {
  const [completedIds, setCompletedIds] = useState<string[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return [];
    try {
      const parsed = JSON.parse(saved);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  });
  const [isOpen, setIsOpen] = useState(false);
  const [lastCompleted, setLastCompleted] = useState<string | null>(null);
  const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  const completedIdsRef = useRef(completedIds);
  completedIdsRef.current = completedIds;

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(completedIds));
    window.dispatchEvent(
      new CustomEvent(CHIMERA_EVENTS.KILL_CHAIN_PROGRESS, {
        detail: {
          completed: completedIds.length,
          total: KILL_CHAIN_OBJECTIVES.length,
        },
      }),
    );
  }, [completedIds]);

  // Cleanup toast on unmount
  useEffect(() => {
    return () => {
      if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    };
  }, []);

  // Use the new generic hook for safer event handling
  useCustomEvent(CHIMERA_EVENTS.TOGGLE_KILL_CHAIN, () => {
    setIsOpen(prev => !prev);
  });

  useAttackLog((log) => {
    KILL_CHAIN_OBJECTIVES.forEach(obj => {
      if (completedIdsRef.current.includes(obj.id)) return;

      const typeMatch = obj.type === log.type;
      const payloadMatch = !obj.payloadMatch || 
        log.payload.toLowerCase().includes(obj.payloadMatch.toLowerCase());
      const statusMatch = !obj.statusPattern || obj.statusPattern === log.status;

      if (typeMatch && payloadMatch && statusMatch) {
        setCompletedIds(prev => {
          if (prev.includes(obj.id)) return prev;
          return [...prev, obj.id];
        });
        setLastCompleted(obj.id);
        
        if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
        toastTimeoutRef.current = setTimeout(() => setLastCompleted(null), TOAST_DURATION_MS);
      }
    });
  });

  const handleReset = () => {
    if (window.confirm('Permanently reset all kill chain progress?')) {
      setCompletedIds([]);
    }
  };

  if (!isOpen && showLauncher) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        aria-label="Open Kill Chain Tracker"
        className="fixed bottom-6 left-6 p-3 bg-red-600 hover:bg-red-700 text-white rounded-full shadow-lg transition-all hover:scale-110 z-[90] group"
        title="Open Kill Chain Tracker"
      >
        <Target className="w-6 h-6" />
        <span className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          Kill Chain
        </span>
      </button>
    );
  }

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed left-4 top-28 z-[90] w-64 max-w-[calc(100vw-2rem)] md:max-w-xs pointer-events-none">
      {/* Toast for completion */}
      {lastCompleted && (
        <div
          role="status"
          aria-live="polite"
          className="mb-4 p-4 bg-emerald-600 text-white rounded-xl shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-10 duration-500 pointer-events-auto"
        >
          <Trophy className="w-6 h-6 shrink-0" />
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest opacity-80">Objective Met</p>
            <p className="text-sm font-bold">{KILL_CHAIN_OBJECTIVES.find(o => o.id === lastCompleted)?.title}</p>
          </div>
        </div>
      )}

      {/* Main Panel */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 overflow-hidden pointer-events-auto transition-all">
        <div
          className="w-full p-4 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-700"
        >
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-red-500" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">Kill Chain Status</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-bold text-slate-400">{completedIds.length} / {KILL_CHAIN_OBJECTIVES.length}</span>
            <button
              onClick={() => setIsOpen(false)}
              aria-label="Close Kill Chain Tracker"
              className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div
          id="kill-chain-panel"
          role="region"
          aria-label="Objectives List"
          className="p-4 space-y-4 animate-in slide-in-from-top-2 duration-300"
        >
            <ul className="space-y-4">
              {KILL_CHAIN_OBJECTIVES.map((obj) => {
                const isDone = completedIds.includes(obj.id);
                return (
                  <li key={obj.id} className={`flex gap-3 transition-opacity ${isDone ? 'opacity-100' : 'opacity-60'}`}>
                    {isDone ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="w-5 h-5 text-slate-300 dark:text-slate-700 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <h4 className={`text-xs font-bold ${isDone ? 'text-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-400'}`}>{obj.title}</h4>
                      <p className="text-[10px] text-slate-400 leading-tight mt-0.5">{obj.description}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
            
            {completedIds.length === KILL_CHAIN_OBJECTIVES.length && (
              <div className="mt-4 p-3 bg-fuchsia-50 dark:bg-fuchsia-900/20 border border-fuchsia-100 dark:border-fuchsia-900/30 rounded-xl text-center">
                <p className="text-xs font-bold text-fuchsia-600 dark:text-fuchsia-400 uppercase tracking-widest">Master Operator</p>
                <p className="text-[10px] text-fuchsia-500">All objectives secured.</p>
              </div>
            )}

            <button 
              onClick={handleReset}
              className="w-full mt-2 py-1.5 text-[10px] font-bold text-slate-400 hover:text-red-500 transition-colors uppercase outline-none focus-visible:underline"
            >
              Reset Progress
            </button>
          </div>
        </div>
      </div>
  );
};
