import React, { useState, useEffect } from 'react';
import { 
  Scan, 
  X, 
  ChevronRight, 
  ChevronDown, 
  Play, 
  Copy, 
  Check, 
  AlertCircle,
  ArrowRight,
  Database,
  Globe,
  Settings
} from 'lucide-react';
import { useRequestInspector, interceptedExchange } from './RequestInspectorProvider';

export const XRayInspector: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { exchanges, clearExchanges } = useRequestInspector();
  const [selectedExchange, setSelectedExchange] = useState<interceptedExchange | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'request' | 'response' | 'headers'>('request');

  // Auto-open on first request if closed? Maybe not.
  // Toggle with Ctrl + X
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'x') {
        setIsOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 left-6 p-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full shadow-lg transition-all hover:scale-110 z-50 group border-2 border-white/20"
        title="Open X-Ray Inspector (Ctrl+X)"
      >
        <Scan className="w-6 h-6" />
        <span className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          X-Ray Inspector
        </span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-0 left-0 w-full h-[60vh] bg-slate-900 text-slate-300 z-[100] shadow-2xl flex flex-col border-t border-emerald-500/30 animate-in slide-in-from-bottom duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-950 border-b border-slate-800">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Scan className="w-5 h-5 text-emerald-400 animate-pulse" />
            <span className="font-bold tracking-widest text-emerald-400 uppercase text-xs">X-Ray Inspector // API Traffic</span>
          </div>
          <div className="h-4 w-px bg-slate-800" />
          <div className="flex gap-4 text-[10px] font-mono">
            <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Interceptor: Active</span>
            <span className="text-slate-500">Total: {exchanges.length}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={clearExchanges}
            className="text-[10px] font-bold uppercase text-slate-500 hover:text-white transition-colors px-2 py-1 bg-slate-900 rounded border border-slate-800"
          >
            Clear Logs
          </button>
          <button onClick={() => setIsOpen(false)} className="hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar: List of Exchanges */}
        <div className="w-1/3 border-r border-slate-800 flex flex-col overflow-hidden">
          <div className="p-2 bg-slate-900/50 border-b border-slate-800 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            Recent Transactions
          </div>
          <div className="flex-1 overflow-y-auto">
            {exchanges.map(ex => (
              <button 
                key={ex.id}
                onClick={() => setSelectedExchange(ex)}
                className={`w-full p-3 text-left border-b border-slate-800/50 hover:bg-slate-800 transition-all flex items-center justify-between group ${selectedExchange?.id === ex.id ? 'bg-emerald-900/20 border-l-2 border-l-emerald-500' : ''}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      ex.method === 'GET' ? 'bg-blue-900/30 text-blue-400' :
                      ex.method === 'POST' ? 'bg-emerald-900/30 text-emerald-400' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {ex.method}
                    </span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      ex.status >= 400 ? 'bg-red-900/30 text-red-400' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {ex.status}
                    </span>
                    <span className="text-[10px] text-slate-500">{ex.timestamp}</span>
                  </div>
                  <div className="text-xs font-mono text-slate-300 truncate">{ex.url.replace(window.location.origin, '')}</div>
                </div>
                <ChevronRight className={`w-4 h-4 text-slate-600 transition-transform ${selectedExchange?.id === ex.id ? 'translate-x-1 text-emerald-500' : ''}`} />
              </button>
            ))}
            {exchanges.length === 0 && (
              <div className="p-12 text-center text-slate-600">
                <Globe className="w-8 h-8 mx-auto mb-3 opacity-20" />
                <p className="text-xs">No API traffic detected yet.</p>
              </div>
            )}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="flex-1 flex flex-col bg-slate-900/50 overflow-hidden">
          {selectedExchange ? (
            <>
              {/* Tab Navigation */}
              <div className="flex border-b border-slate-800 px-4 pt-4 gap-6">
                {[
                  { id: 'request', label: 'Request Body' },
                  { id: 'response', label: 'Response JSON' },
                  { id: 'headers', label: 'Headers' }
                ].map(tab => (
                  <button 
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`pb-3 text-xs font-bold uppercase tracking-widest transition-all relative ${activeTab === tab.id ? 'text-emerald-400' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    {tab.label}
                    {activeTab === tab.id && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-emerald-500 shadow-[0_-4px_8px_rgba(16,185,129,0.5)]" />}
                  </button>
                ))}
              </div>

              {/* Toolbar */}
              <div className="px-4 py-2 bg-slate-950/50 border-b border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-4 text-[10px] text-slate-500">
                  <span className="flex items-center gap-1 font-mono"><ArrowRight className="w-3 h-3" /> {selectedExchange.duration}ms</span>
                  <span className="flex items-center gap-1 font-mono"><Database className="w-3 h-3" /> {JSON.stringify(selectedExchange.responseBody).length} bytes</span>
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => handleCopy(JSON.stringify(activeTab === 'request' ? selectedExchange.requestBody : selectedExchange.responseBody, null, 2))}
                    className="flex items-center gap-1.5 px-2 py-1 hover:bg-slate-800 rounded text-[10px] font-bold transition-colors"
                  >
                    {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                  <button className="flex items-center gap-1.5 px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold transition-colors">
                    <Play className="w-3 h-3" />
                    Replay
                  </button>
                </div>
              </div>

              {/* Content Area */}
              <div className="flex-1 overflow-auto p-6 font-mono text-sm">
                {activeTab === 'request' && (
                  <div className="space-y-4">
                    <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-emerald-500 font-bold uppercase mb-2">Request Endpoint</div>
                      <div className="text-emerald-400 font-bold">{selectedExchange.method} <span className="text-slate-300">{selectedExchange.url.replace(window.location.origin, '')}</span></div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500 font-bold uppercase mb-2">Payload</div>
                      {selectedExchange.requestBody ? (
                        <pre className="text-slate-300">
                          <code>{JSON.stringify(selectedExchange.requestBody, null, 2)}</code>
                        </pre>
                      ) : (
                        <div className="text-slate-600 italic">No request body (GET/DELETE usually)</div>
                      )}
                    </div>
                  </div>
                )}

                {activeTab === 'response' && (
                  <div className="space-y-4">
                    <div className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-emerald-500 font-bold uppercase mb-2">Status Code</div>
                      <div className={`text-lg font-bold ${selectedExchange.status >= 400 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {selectedExchange.status} {selectedExchange.status === 200 ? 'OK' : selectedExchange.status === 401 ? 'Unauthorized' : ''}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500 font-bold uppercase mb-2">Response Data</div>
                      <pre className="text-slate-300">
                        <code>{JSON.stringify(selectedExchange.responseBody, null, 2)}</code>
                      </pre>
                    </div>
                  </div>
                )}

                {activeTab === 'headers' && (
                  <div className="space-y-6">
                    <div>
                      <div className="text-[10px] text-emerald-500 font-bold uppercase mb-2">Request Headers</div>
                      <div className="grid grid-cols-3 gap-y-2 text-xs">
                        {Object.entries(selectedExchange.requestHeaders).map(([k, v]) => (
                          <React.Fragment key={k}>
                            <div className="text-slate-500">{k}</div>
                            <div className="col-span-2 text-slate-300 break-all">{v}</div>
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                    <div className="h-px bg-slate-800" />
                    <div>
                      <div className="text-[10px] text-blue-500 font-bold uppercase mb-2">Response Headers</div>
                      <div className="grid grid-cols-3 gap-y-2 text-xs">
                        {Object.entries(selectedExchange.responseHeaders).map(([k, v]) => (
                          <React.Fragment key={k}>
                            <div className="text-slate-500">{k}</div>
                            <div className="col-span-2 text-slate-300 break-all">{v}</div>
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-600 p-8 text-center">
              <div className="p-6 bg-slate-950 rounded-full mb-6 border-2 border-slate-900">
                <Settings className="w-12 h-12 opacity-10" />
              </div>
              <h3 className="text-lg font-bold text-slate-400 mb-2">Inspection Ready</h3>
              <p className="max-w-xs text-sm">Select an API transaction from the list to view its internal payload and response data.</p>
              <div className="mt-8 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl text-[10px] font-bold text-emerald-500/60 uppercase tracking-widest flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Education: Pay attention to excessive data in responses
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-1.5 bg-slate-950 border-t border-slate-800 flex justify-between text-[10px] text-slate-500 font-mono">
        <div>CHIMERA X-RAY AGENT v1.0.4 // LOCAL_PROXY</div>
        <div className="flex gap-4">
          <span>LATENCY: <span className="text-emerald-500">OPTIMAL</span></span>
          <span>FILTER: <span className="text-emerald-500">OFF</span></span>
        </div>
      </div>
    </div>
  );
};
