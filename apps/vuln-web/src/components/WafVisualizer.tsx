import React, { useState, useEffect, useRef } from 'react';
import { Shield, ShieldCheck, ShieldAlert, Cpu, Lock, Loader2, X } from 'lucide-react';
import { useAttackLog } from '../hooks/useAttackLog';
import { useCustomEvent } from '../hooks/useCustomEvent';
import { CHIMERA_EVENTS } from '../lib/config';

interface RequestStep {
  id: string;
  name: string;
  status: 'pending' | 'passed' | 'failed' | 'neutralized';
  description: string;
  isBlockingStep?: boolean;
}

interface ActiveRequest {
  id: string;
  type: string;
  payload: string;
  steps: RequestStep[];
  finalStatus: 'blocked' | 'allowed';
}

const STEP_INITIAL_DELAY_MS = 400;
const STEP_INTERVAL_MS = 600;

export const WafVisualizer: React.FC<{ showLauncher?: boolean }> = ({ showLauncher = true }) => {
  const [activeRequest, setActiveRequest] = useState<ActiveRequest | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [userClosed, setUserClosed] = useState(false);
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const isOpenRef = useRef(isOpen);
  isOpenRef.current = isOpen;

  const clearTimeouts = () => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
  };

  // Toggle with Ctrl + Shift + B (Blue Team)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'b') {
        setIsOpen(prev => {
          const next = !prev;
          if (!next) setUserClosed(true);
          else setUserClosed(false);
          return next;
        });
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeouts();
    };
  }, []);

  // Use the new generic hook for safer event handling
  useCustomEvent(CHIMERA_EVENTS.TOGGLE_WAF_VISUALIZER, () => {
    setIsOpen(prev => {
      const next = !prev;
      if (!next) setUserClosed(true);
      else setUserClosed(false);
      return next;
    });
  });

  useAttackLog((log) => {
    clearTimeouts(); // Reset if a new request comes in

    const steps: RequestStep[] = [
      { id: 'ip_rep', name: 'IP Reputation', status: 'pending', description: 'Checking source IP against known threat feeds...' },
      { id: 'rate_limit', name: 'Rate Limiter', status: 'pending', description: 'Evaluating request frequency for burst patterns...' },
      { id: 'waf_sig', name: 'WAF Signature', status: 'pending', description: 'Analyzing payload for malicious patterns (SQLi, XSS, RCE)...', isBlockingStep: true },
    ];

    // Add App Layer if we have origin defense data
    if (log.origin_defense) {
      steps.push({ 
        id: 'origin_sec', 
        name: 'App Layer (Origin)', 
        status: 'pending', 
        description: `Backend defense active: ${log.origin_defense}`,
        isBlockingStep: true 
      });
    } else {
      steps.push({ 
        id: 'api_schema', 
        name: 'API Schema', 
        status: 'pending', 
        description: 'Validating input structure against OAS definition...' 
      });
    }

    const newRequest: ActiveRequest = {
      id: log.id,
      type: log.type,
      payload: log.payload,
      finalStatus: log.status,
      steps
    };

    setActiveRequest(newRequest);
    
    // Auto-open only if the user hasn't deliberately closed it
    if (!isOpenRef.current && !userClosed) {
      setIsOpen(true);
    }

    // Simulate step-by-step processing
    let currentStep = 0;
    const processNextStep = () => {
      if (currentStep >= newRequest.steps.length) return;

      setActiveRequest(prev => {
        if (!prev) return null;
        const nextSteps = [...prev.steps];
        const step = nextSteps[currentStep];
        
        let stepStatus: 'passed' | 'failed' | 'neutralized' = 'passed';
        
        // Block at WAF if status is blocked and no origin defense was mentioned
        if (step.id === 'waf_sig' && log.status === 'blocked' && !log.origin_defense) {
          stepStatus = 'failed';
        }
        
        // Handle App Layer (Origin)
        if (step.id === 'origin_sec') {
          if (log.status === 'blocked') {
            stepStatus = 'failed';
          } else if (log.origin_defense) {
            // It passed but was neutralized by the backend
            stepStatus = 'neutralized';
          }
        }

        nextSteps[currentStep] = { ...step, status: stepStatus };
        return { ...prev, steps: nextSteps };
      });

      // Stop if current step failed
      const stepObj = newRequest.steps[currentStep];
      const isFailedAtWaf = stepObj.id === 'waf_sig' && log.status === 'blocked' && !log.origin_defense;
      const isFailedAtOrigin = stepObj.id === 'origin_sec' && log.status === 'blocked';

      if (isFailedAtWaf || isFailedAtOrigin) return;

      currentStep++;
      const tid = setTimeout(processNextStep, STEP_INTERVAL_MS);
      timeoutsRef.current.push(tid);
    };

    const tid = setTimeout(processNextStep, STEP_INITIAL_DELAY_MS);
    timeoutsRef.current.push(tid);
  });

  if (!isOpen && showLauncher) {
    return (
      <button
        onClick={() => {
          setIsOpen(true);
          setUserClosed(false);
        }}
        aria-label="Open WAF Visualizer"
        className="fixed bottom-6 left-48 p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all hover:scale-110 z-[90] group"
        title="Open WAF Visualizer (Ctrl+Shift+B)"
      >
        <Shield className="w-5 h-5" />
        <span className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          WAF Visualizer
        </span>
      </button>
    );
  }

  if (!isOpen) {
    return null;
  }

  const firstPendingIdx = activeRequest?.steps.findIndex(s => s.status === 'pending') ?? -1;

  return (
    <div 
      className="fixed top-20 right-6 w-80 max-w-[calc(100vw-3rem)] md:max-w-sm bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 z-[100] flex flex-col overflow-hidden animate-in slide-in-from-right-10 duration-300"
      role="region"
      aria-label="WAF Visualizer"
    >
      {/* Header */}
      <div className="p-4 bg-blue-600 text-white flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          <h3 className="font-bold text-sm">Apparatus WAF Visualizer</h3>
        </div>
        <button 
          onClick={() => {
            setIsOpen(false);
            setUserClosed(true);
          }} 
          aria-label="Close WAF Visualizer"
          className="hover:bg-blue-500 rounded p-1 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-white/50"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Pipeline View */}
      <div className="p-4 bg-slate-50 dark:bg-slate-950 flex-1 min-h-[400px]">
        {activeRequest ? (
          <div className="space-y-6">
            {/* Request Info */}
            <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] font-bold text-blue-600 uppercase tracking-widest">Incoming Request</span>
                <span className="text-[10px] font-mono text-slate-400">{activeRequest.id}</span>
              </div>
              <p className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">{activeRequest.payload}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded font-bold uppercase">{activeRequest.type}</span>
              </div>
            </div>

            {/* Pipeline Steps */}
            <ol className="space-y-4 relative">
              {/* Connector Line */}
              <div className="absolute left-5 top-2 bottom-2 w-0.5 bg-slate-200 dark:bg-slate-800 -z-0" />

              {activeRequest.steps.map((step, idx) => (
                <li key={step.id} className="relative z-10 flex gap-4 animate-in fade-in slide-in-from-left-2 duration-300">
                  <div className={`mt-1 w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-4 border-slate-50 dark:border-slate-950 transition-all ${
                    step.status === 'passed' ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20' :
                    step.status === 'failed' ? 'bg-red-500 text-white shadow-lg shadow-red-500/20' :
                    step.status === 'neutralized' ? 'bg-yellow-500 text-slate-900 shadow-lg shadow-yellow-500/20' :
                    'bg-slate-200 dark:bg-slate-800 text-slate-400'
                  }`}>
                    {step.status === 'passed' ? <ShieldCheck className="w-5 h-5" /> :
                     step.status === 'failed' ? <ShieldAlert className="w-5 h-5" /> :
                     step.status === 'neutralized' ? <Lock className="w-5 h-5" /> :
                     idx === firstPendingIdx ? <Loader2 className="w-5 h-5 animate-spin" /> :
                     <Cpu className="w-5 h-5" />}
                  </div>
                  <div className="flex-1 pt-1">
                    <h4 className={`text-xs font-bold ${
                      step.status === 'passed' ? 'text-emerald-600 dark:text-emerald-400' :
                      step.status === 'failed' ? 'text-red-600 dark:text-red-400' :
                      step.status === 'neutralized' ? 'text-yellow-600 dark:text-yellow-400' :
                      'text-slate-500 dark:text-slate-400'
                    }`}>
                      {step.name} {step.status === 'neutralized' && '(Neutralized)'}
                    </h4>
                    <p className="text-[10px] text-slate-400 leading-tight mt-0.5">{step.description}</p>
                  </div>
                </li>
              ))}
            </ol>

            {/* Result Banner */}
            {activeRequest.steps.every(s => s.status !== 'pending') || activeRequest.steps.some(s => s.status === 'failed' || s.status === 'neutralized') ? (
              <div className={`p-4 rounded-xl text-center border animate-in zoom-in-95 duration-500 ${
                activeRequest.finalStatus === 'blocked' 
                  ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-400' 
                  : activeRequest.steps.some(s => s.status === 'neutralized')
                  ? 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                  : 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-200 dark:border-emerald-900/30 text-emerald-700 dark:text-emerald-400'
              }`}>
                <div className="flex items-center justify-center gap-2 mb-1">
                  {activeRequest.finalStatus === 'blocked' ? <Lock className="w-4 h-4" /> : 
                   activeRequest.steps.some(s => s.status === 'neutralized') ? <ShieldAlert className="w-4 h-4" /> :
                   <ShieldCheck className="w-4 h-4" />}
                  <span className="text-xs font-bold uppercase tracking-widest">
                    Verdict: {activeRequest.steps.some(s => s.status === 'neutralized') ? 'NEUTRALIZED' : activeRequest.finalStatus}
                  </span>
                </div>
                <p className="text-[10px] opacity-80">
                  {activeRequest.finalStatus === 'blocked' 
                    ? 'Threat detected. Request terminated at ingress.' 
                    : activeRequest.steps.some(s => s.status === 'neutralized')
                    ? 'Threat neutralized by origin defense. No data leaked.'
                    : 'No policy violations detected. Request passed to origin.'}
                </p>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <Shield className="w-12 h-12 text-slate-200 dark:text-slate-800 mb-4" />
            <h4 className="text-sm font-bold text-slate-400 mb-1">Protection Inactive</h4>
            <p className="text-xs text-slate-500">Perform an action or attack to visualize the security pipeline.</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 bg-slate-100 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800 flex justify-between text-[10px] font-mono text-slate-500">
        <div className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          BLUE TEAM MODE
        </div>
        <div>[Ctrl+Shift+B] APPARATUS_v2.1</div>
      </div>
    </div>
  );
};
