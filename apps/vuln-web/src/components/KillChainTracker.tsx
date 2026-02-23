import React, { useState, useEffect, useRef } from 'react';
import { Trophy, CheckCircle2, Circle, Target, ChevronDown, ChevronUp } from 'lucide-react';
import { KILL_CHAIN_OBJECTIVES, Objective, AttackLog } from '../lib/objectives';
import { useAttackLog } from '../hooks/useAttackLog';

const STORAGE_KEY = 'chimera-kill-chain';
const TOAST_DURATION_MS = 5000;

export const KillChainTracker: React.FC = () => {
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
  }, [completedIds]);

  // Cleanup toast on unmount
  useEffect(() => {
    return () => {
      if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    };
  }, []);

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

  return (
    <div className="fixed top-20 left-6 z-[90] w-64 max-w-[calc(100vw-3rem)] md:max-w-xs pointer-events-none">
      {/* Toast for completion */}
      {lastCompleted && (
        <div 
          role="status" 
          aria-live="polite"
          className="mb-4 p-4 bg-emerald-600 text-white rounded-xl shadow-2xl flex items-center gap-3 animate-in slide-in-from-left-10 duration-500 pointer-events-auto"
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
        <button 
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
          aria-controls="kill-chain-panel"
          className="w-full p-4 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
        >
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-red-500" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">Kill Chain Status</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-slate-400">{completedIds.length} / {KILL_CHAIN_OBJECTIVES.length}</span>
            {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </div>
        </button>

        {isOpen && (
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
        )}
      </div>
    </div>
  );
};
