import React, { useState, useEffect, useRef } from 'react';
import { Terminal, X, Shield, Activity } from 'lucide-react';

interface AttackLog {
  id: string;
  timestamp: string;
  method: string;
  path: string;
  payload?: string;
  type: 'SQLi' | 'XSS' | 'RCE' | 'SSRF' | 'XXE' | 'Auth' | 'Info' | 'GenAI';
  status: 'blocked' | 'allowed';
  source_ip: string;
}

export const RedTeamConsole: React.FC = () => {
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

  // Simulate receiving attack logs (mock for now, would hook into websocket)
  useEffect(() => {
    if (!isOpen) return;

    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
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
          id: Math.random().toString(36).substr(2, 9),
          timestamp: new Date().toLocaleTimeString(),
          method: 'POST',
          path: paths[Math.floor(Math.random() * paths.length)],
          payload: payloads[Math.floor(Math.random() * payloads.length)],
          type: attackTypes[Math.floor(Math.random() * attackTypes.length)],
          status: Math.random() > 0.4 ? 'blocked' : 'allowed',
          source_ip: `192.168.1.${Math.floor(Math.random() * 255)}`
        };

        setLogs(prev => [...prev.slice(-19), newLog]); // Keep last 20 logs
        
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

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
          <span>SQLi: <span className="text-slate-300">12</span></span>
          <span>XSS: <span className="text-slate-300">4</span></span>
          <span>RCE: <span className="text-slate-300">8</span></span>
        </div>
      </div>
    </div>
  );
};
