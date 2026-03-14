import React, { useState, useRef, useEffect } from 'react';
import { RefreshCw, Activity, Settings2, Clock } from 'lucide-react';
import { useConnectivity } from './ConnectivityProvider';

export const ConnectivityStatus: React.FC = () => {
  const { 
    isOnline, 
    lastChecked, 
    latency, 
    isPinging, 
    checkConnectivity,
    autoPing,
    setAutoPing,
    pingInterval,
    setPingInterval 
  } = useConnectivity();

  const [showSettings, setShowSettings] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setShowSettings(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowSettings(false);
      }
    };

    if (showSettings) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showSettings]);

  const getStatusBg = () => {
    if (isOnline === null) return 'bg-slate-400';
    return isOnline ? 'bg-emerald-400' : 'bg-red-400';
  };

  return (
    <div className="relative" ref={settingsRef}>
      <button
        onClick={() => setShowSettings(!showSettings)}
        aria-expanded={showSettings}
        className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-full text-xs font-bold transition-all border border-slate-700"
        title="Backend Connectivity Status"
        aria-label="Backend Connectivity Status"
      >
        <div className="relative">
          <div className={`w-2 h-2 rounded-full ${getStatusBg()} ${isOnline ? 'animate-pulse' : ''}`} />
          {isPinging && (
            <div className="absolute inset-0 w-2 h-2 rounded-full bg-blue-400 animate-ping opacity-75" />
          )}
        </div>
        <span className="hidden lg:inline">
          {isOnline === null ? 'Checking API...' : isOnline ? 'API Online' : 'API Offline'}
        </span>
        <span className="lg:hidden">
           {isOnline === null ? '...' : isOnline ? 'Online' : 'Offline'}
        </span>
        {latency !== null && (
          <span className="hidden xl:inline text-[10px] text-slate-500 font-mono ml-1 border-l border-slate-700 pl-2">
            {latency}ms
          </span>
        )}
      </button>

      {showSettings && (
        <div 
          role="dialog"
          aria-label="API Connection Settings"
          className="absolute right-0 mt-2 w-72 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-[60] overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        >
          <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-blue-400" />
              <h3 className="font-bold text-sm text-white uppercase tracking-wider">API Connection</h3>
            </div>
            <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${isOnline ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
              {isOnline ? 'Connected' : 'Disconnected'}
            </div>
          </div>

          <div className="p-4 space-y-4 text-slate-300">
            {/* Status Section */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-800/50 p-2 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1 flex items-center gap-1">
                   <Activity className="w-3 h-3" /> Latency
                </div>
                <div className="text-sm font-mono text-white">
                  {latency !== null ? `${latency}ms` : '--'}
                </div>
              </div>
              <div className="bg-slate-800/50 p-2 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-bold mb-1 flex items-center gap-1">
                   <Clock className="w-3 h-3" /> Last Check
                </div>
                <div className="text-[10px] text-white">
                  {lastChecked ? lastChecked.toLocaleTimeString() : 'Never'}
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label htmlFor="auto-ping" className="text-xs font-medium cursor-pointer">Auto-refresh Status</label>
                <button
                  id="auto-ping"
                  role="switch"
                  aria-checked={autoPing}
                  aria-label="Auto-refresh Status"
                  onClick={() => setAutoPing(!autoPing)}
                  className={`w-10 h-5 rounded-full relative transition-colors ${autoPing ? 'bg-blue-600' : 'bg-slate-700'}`}
                >
                  <div className={`absolute top-1 w-3 h-3 rounded-full bg-white transition-all ${autoPing ? 'left-6' : 'left-1'}`} />
                </button>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium">Check Interval</label>
                <div className="grid grid-cols-4 gap-1">
                  {[10000, 30000, 60000, 300000].map((interval) => (
                    <button
                      key={interval}
                      aria-pressed={pingInterval === interval}
                      onClick={() => setPingInterval(interval)}
                      className={`py-1 text-[10px] font-bold rounded ${pingInterval === interval ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
                    >
                      {interval >= 60000 ? `${interval / 60000}m` : `${interval / 1000}s`}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={() => checkConnectivity()}
              disabled={isPinging}
              className="w-full py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors border border-slate-700"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isPinging ? 'animate-spin' : ''}`} />
              {isPinging ? 'Pinging Backend...' : 'Check Connectivity Now'}
            </button>
          </div>

          <div className="p-3 bg-slate-950/50 border-t border-slate-800 text-[10px] text-slate-500 italic flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
            Backend: http://localhost:8880/api/v1
          </div>
        </div>
      )}
    </div>
  );
};
