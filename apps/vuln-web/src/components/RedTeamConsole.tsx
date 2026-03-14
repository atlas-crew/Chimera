import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Terminal, X, Shield, Activity } from 'lucide-react';
import { useCustomEvent } from '../hooks/useCustomEvent';
import { CHIMERA_EVENTS } from '../lib/config';

interface AttackLog {
  id: string;
  timestamp: string;
  method: string;
  path: string;
  payload?: string;
  type: 'SQLi' | 'XSS' | 'RCE' | 'SSRF' | 'XXE' | 'Auth' | 'Info' | 'GenAI' | 'FileUpload';
  status: 'blocked' | 'allowed';
  source_ip: string;
}

export const RedTeamConsole: React.FC<{ showLauncher?: boolean }> = ({ showLauncher = true }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [logs, setLogs] = useState<AttackLog[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Toggle with Ctrl + ~ (tilde)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === '`') {
        setIsOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Use the new generic hook for safer event handling
  useCustomEvent(CHIMERA_EVENTS.TOGGLE_RED_TEAM_CONSOLE, () => {
    setIsOpen(prev => !prev);
  });

  // Listen for real attack logs from other components using the generic hook
  useCustomEvent<AttackLog>(CHIMERA_EVENTS.ATTACK_LOG, (log) => {
    setLogs(prev => [...prev.slice(-49), log]); // Keep last 50 logs
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  });

  // Simulate receiving background attack traffic
  useEffect(() => {
    if (!isOpen) return;

    const interval = setInterval(() => {
      if (Math.random() > 0.8) { // Reduced frequency
        const attackTypes: AttackLog['type'][] = ['SQLi', 'XSS', 'RCE', 'SSRF', 'XXE', 'GenAI'];
        const paths = [
          '/api/v1/healthcare/records/search',
          '/api/v1/diagnostics/ping',
          '/api/v1/genai/chat',
          '/api/v1/admin/attack/xxe'
        ];
        const payloads = [
          "' OR 1=1 --", 
          "<script>alert(1)</script>", 
          "; cat /etc/passwd", 
          "<!ENTITY xxe SYSTEM...>"
        ];

        const newLog: AttackLog = {
          id: Math.random().toString(36).substring(2, 11),
          timestamp: new Date().toLocaleTimeString(),
          method: 'POST',
          path: paths[Math.floor(Math.random() * paths.length)],
          payload: payloads[Math.floor(Math.random() * payloads.length)],
          type: attackTypes[Math.floor(Math.random() * attackTypes.length)],
          status: Math.random() > 0.4 ? 'blocked' : 'allowed',
          source_ip: `192.168.1.${Math.floor(Math.random() * 255)}`
        };

        setLogs(prev => [...prev.slice(-49), newLog]);
        
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isOpen]);

  const stats = useMemo(() => ({
    sqli: logs.filter(l => l.type === 'SQLi').length,
    xss: logs.filter(l => l.type === 'XSS').length,
    genai: logs.filter(l => l.type === 'GenAI').length,
  }), [logs]);

  if (!isOpen && showLauncher) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        aria-label="Open Red Team Console"
        className="fixed bottom-6 left-[8.5rem] p-3 bg-red-600 hover:bg-red-700 text-white rounded-full shadow-lg transition-all hover:scale-110 z-[90] group"
      >
        <Terminal className="w-6 h-6" />
        <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          Red Team Console
        </span>
      </button>
    );
  }

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 w-full h-64 bg-slate-950 text-green-400 font-mono text-xs z-[100] shadow-2xl border-b border-green-900/50 animate-in slide-in-from-top-10 duration-300 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Terminal className="w-4 h-4 text-red-500 animate-pulse" />
          <span className="font-bold tracking-widest text-slate-200">RED TEAM CONSOLE // LIVE FEED</span>
          <span className="bg-red-900/30 text-red-400 px-2 py-0.5 rounded text-[10px] border border-red-900/50">
            CONNECTION ESTABLISHED
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex gap-2 text-slate-500">
            <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> WAF: ACTIVE</span>
            <span className="flex items-center gap-1"><Activity className="w-3 h-3" /> RT: <span className="text-green-400">12ms</span></span>
          </div>
          <button onClick={() => setIsOpen(false)} className="hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Logs Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-1">
        {logs.map(log => (
          <div key={log.id} className="grid grid-cols-12 gap-2 hover:bg-white/5 p-1 rounded transition-colors group">
            <div className="col-span-1 text-slate-500">[{log.timestamp}]</div>
            <div className="col-span-1 text-blue-400 font-bold">{log.type}</div>
            <div className="col-span-1 text-yellow-500">{log.method}</div>
            <div className="col-span-3 text-slate-300 truncate" title={log.path}>{log.path}</div>
            <div className="col-span-4 text-slate-400 font-mono truncate group-hover:text-white transition-colors">
              {log.payload}
            </div>
            <div className="col-span-1 text-slate-500 text-right">{log.source_ip}</div>
            <div className="col-span-1 text-right">
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                log.status === 'blocked' 
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                  : 'bg-red-500/20 text-red-400 border border-red-500/30'
              }`}>
                {log.status.toUpperCase()}
              </span>
            </div>
          </div>
        ))}
        {logs.length === 0 && (
          <div className="text-slate-600 italic mt-4 text-center">Waiting for attack traffic...</div>
        )}
      </div>

      {/* Footer / Stats */}
      <div className="px-4 py-1 bg-slate-900 border-t border-slate-800 flex justify-between text-[10px] text-slate-500">
        <div>Listening on port 8880...</div>
        <div className="flex gap-4">
          <span>SQLi: <span className="text-slate-300">{stats.sqli}</span></span>
          <span>XSS: <span className="text-slate-300">{stats.xss}</span></span>
          <span>GenAI: <span className="text-slate-300">{stats.genai}</span></span>
        </div>
      </div>
    </div>
  );
};
