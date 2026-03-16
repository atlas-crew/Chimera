import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Users, 
  Activity, 
  Search, 
  Terminal,
  Lock,
  Eye,
  Trash2,
  FileText,
  Info
} from 'lucide-react';
import { type SecurityConfig, useSettings } from '../components/SettingsProvider';
import { useApi } from '../hooks/useApi';
import { VulnerabilityModal } from '../components/VulnerabilityModal';
import { HintChip } from '../components/HintChip';
import { useVulnerabilityInfo } from '../hooks/useVulnerabilityInfo';
import { ApparatusPanel } from '../components/ApparatusPanel';
import { API_BASE_URL } from '../lib/config';
import { dispatchAttackLog } from '../lib/security';

type DefenseToggleKey = keyof Pick<
  SecurityConfig,
  'sqli_protection' | 'xss_protection' | 'bola_protection' | 'ssrf_protection' | 'csrf_protection'
>;

interface AuditLogEntry {
  event: string;
  timestamp: string;
}

const DEFENSE_TOGGLES: Array<{ id: DefenseToggleKey; label: string; desc: string }> = [
  { id: 'sqli_protection', label: 'SQLi Filter', desc: 'Parameterized query enforcement' },
  { id: 'xss_protection', label: 'XSS Sanitizer', desc: 'HTML output encoding' },
  { id: 'bola_protection', label: 'BOLA Guardian', desc: 'Object-level ownership validation' },
  { id: 'ssrf_protection', label: 'SSRF Shield', desc: 'Egress IP/Domain allow-listing' },
  { id: 'csrf_protection', label: 'CSRF Token', desc: 'Synchronizer token pattern' },
];

export const AdminDashboard: React.FC = () => {
  const { securityConfig, setSecurityConfig } = useSettings();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [showInfo, setShowInfo] = useState(false);
  
  const { request } = useApi<{ logs?: AuditLogEntry[] }>();
  const { info: adminInfo } = useVulnerabilityInfo('admin');

  useEffect(() => {
    const fetchLogs = async () => {
      const data = await request('/api/v1/saas/audit/logs?limit=10');
      if (data) {
        setLogs(Array.isArray(data.logs) ? data.logs : []);
      }
    };
    fetchLogs();
  }, [request]);

  const toggleSetting = (key: DefenseToggleKey) => {
    const newConfig = { ...securityConfig, [key]: !securityConfig[key] };
    setSecurityConfig(newConfig);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {adminInfo && <VulnerabilityModal isOpen={showInfo} onClose={() => setShowInfo(false)} info={adminInfo} />}
      
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3 underline decoration-red-500/20">
              <ShieldAlert className="w-8 h-8 text-red-600" />
              Security Control Center
            </h1>
            <button 
              onClick={() => setShowInfo(true)}
              className="p-1.5 text-red-600 bg-red-50 rounded-full hover:bg-blue-100 transition-colors"
              aria-label="View Vulnerability Info"
            >
              <Info className="w-5 h-5" />
            </button>
          </div>
          <p className="text-slate-500 font-mono text-sm tracking-tight mt-1">Administrative Terminal • Root Access Level</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded shadow-sm text-sm font-bold hover:bg-slate-800 transition-all">
            <Terminal className="w-4 h-4" />
            System Console
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded shadow-sm text-sm font-bold hover:bg-red-700 transition-all">
            <Activity className="w-4 h-4" />
            Global Killswitch
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Security Toggles */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2 text-sm uppercase tracking-widest">
              <Lock className="w-4 h-4 text-slate-400" />
              Defense Pipeline
            </h2>
            <div className="space-y-4">
              {DEFENSE_TOGGLES.map((defense) => (
                <div key={defense.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <div>
                    <p className="text-xs font-bold text-slate-800">{defense.label}</p>
                    <p className="text-[10px] text-slate-500">{defense.desc}</p>
                  </div>
                  <button 
                    onClick={() => toggleSetting(defense.id)}
                    type="button"
                    role="switch"
                    aria-checked={securityConfig[defense.id]}
                    aria-label={defense.label}
                    className={`w-10 h-5 rounded-full transition-colors relative focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${securityConfig[defense.id] ? 'bg-emerald-500' : 'bg-slate-300'}`}
                  >
                    <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${securityConfig[defense.id] ? 'left-6' : 'left-1'}`} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 p-6 rounded-xl text-white shadow-xl relative overflow-hidden">
            <Activity className="absolute -right-4 -bottom-4 w-24 h-24 text-white/5" />
            <h2 className="font-bold mb-4 flex items-center gap-2 text-xs uppercase tracking-widest text-red-400">
              <Activity className="w-4 h-4" />
              Real-time Metrics
            </h2>
            <div className="space-y-4 relative z-10">
              <div className="flex justify-between items-end">
                <span className="text-[10px] text-slate-400 uppercase font-bold">Threat Level</span>
                <span className="text-xl font-bold text-red-500">CRITICAL</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-red-500 h-full w-3/4" />
              </div>
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold">Blocked Attacks</p>
                  <p className="text-lg font-bold">1,242</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold">Active Sessions</p>
                  <p className="text-lg font-bold">84</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Middle Column: User Management / Monitoring */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl overflow-hidden shadow-sm border border-slate-200">
            <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
              <h2 className="font-bold text-slate-700 flex items-center gap-2 text-xs uppercase tracking-widest">
                <Users className="w-4 h-4 text-blue-500" />
                Active Sessions
              </h2>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                <input type="text" placeholder="Search accounts..." className="pl-8 pr-4 py-1.5 bg-white border border-slate-200 rounded text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 w-48" />
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-bold">
                  <tr>
                    <th className="p-4">Account ID</th>
                    <th className="p-4">User Identity</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Last Activity</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {[
                    { id: 'ACC-001', user: 'admin@chimera.lab', status: 'active', last: 'Now' },
                    { id: 'ACC-002', user: 'j.doe@example.com', status: 'idle', last: '12m ago' },
                    { id: 'ACC-003', user: 'attacker@evil.corp', status: 'flagged', last: '2m ago' },
                    { id: 'ACC-004', user: 's.smith@bank.com', status: 'active', last: '1h ago' },
                  ].map((row) => (
                    <tr key={row.id} className="hover:bg-slate-50 transition-colors">
                      <td className="p-4 font-mono text-xs font-bold text-slate-900">{row.id}</td>
                      <td className="p-4 text-slate-600">{row.user}</td>
                      <td className="p-4">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          row.status === 'active' ? 'bg-emerald-100 text-emerald-700' :
                          row.status === 'idle' ? 'bg-slate-100 text-slate-600' :
                          'bg-red-100 text-red-700'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            row.status === 'active' ? 'bg-emerald-500' :
                            row.status === 'idle' ? 'bg-slate-400' :
                            'bg-red-500'
                          }`} />
                          {row.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-4 text-slate-500 text-xs">{row.last}</td>
                      <td className="p-4 text-right space-x-2">
                        <button className="p-1 hover:text-blue-600 transition-colors" title="View Details"><Eye className="w-3.5 h-3.5" /></button>
                        <button className="p-1 hover:text-red-400 transition-colors" title="Purge Record"><Trash2 className="w-3.5 h-3.5" /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <ApparatusPanel />
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2 text-xs uppercase tracking-widest">
                <FileText className="w-4 h-4 text-slate-400" />
                Audit Logs
              </h2>
              <div className="space-y-3">
                {logs.map((log) => (
                  <div key={`${log.timestamp}-${log.event}`} className="flex gap-3 items-start border-b border-slate-50 pb-2 last:border-0 last:pb-0">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-slate-800">{log.event}</p>
                      <p className="text-[10px] text-slate-400 font-mono">{log.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 py-2 text-[10px] font-bold text-blue-600 uppercase tracking-widest hover:bg-blue-50 transition-all rounded">View All Logs</button>
            </div>

            <div className="bg-slate-800 p-6 rounded-xl shadow-inner border border-slate-700">
              <div className="p-4 border-b border-slate-800 bg-slate-800/50 flex items-center justify-between">
                <h2 className="font-bold text-slate-200 flex items-center gap-2 uppercase text-xs tracking-widest font-mono">
                  <Terminal className="w-4 h-4 text-red-400" />
                  Network Diagnostics
                </h2>
              </div>
              <div className="space-y-6">
                {/* Ping Tool (RCE) */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label htmlFor="ping-host" className="text-[10px] font-bold text-slate-400 uppercase block">Network Connectivity Check</label>
                    <HintChip label="RCE" onClick={() => setShowInfo(true)} />
                  </div>
                  <div className="flex gap-2">
                    <input 
                      id="ping-host"
                      type="text" 
                      placeholder="IP or Hostname" 
                      defaultValue="8.8.8.8"
                      className="flex-1 p-2 bg-slate-900 border border-slate-600 rounded font-mono text-xs text-green-400 focus:outline-none focus:border-green-500" 
                    />
                    <button 
                      onClick={() => {
                        const host = (document.getElementById('ping-host') as HTMLInputElement).value;
                        const output = document.getElementById('diag-output');
                        if(output) output.innerText = '> Pinging ' + host + '...';
                        fetch(`${API_BASE_URL}/api/v1/diagnostics/ping`, {
                          method: 'POST',
                          headers: {'Content-Type': 'application/json'},
                          body: JSON.stringify({ host })
                        })
                        .then(res => res.json())
                        .then(data => { 
                          if(output) output.innerText = data.output || data.error || 'Error';
                          if (data.vulnerability) {
                            dispatchAttackLog('RCE', `${API_BASE_URL}/api/v1/diagnostics/ping`, `host=${host} [VULN TRIGGERED]`, 'allowed');
                          }
                        })
                      }}
                      className="bg-slate-700 hover:bg-slate-600 text-white px-3 rounded text-xs font-bold transition-colors"
                    >
                      Ping
                    </button>
                  </div>
                </div>

                {/* Webhook Tool (SSRF) */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label htmlFor="webhook-url" className="text-[10px] font-bold text-slate-400 uppercase block">Webhook Integration Tester</label>
                    <HintChip label="SSRF" onClick={() => setShowInfo(true)} />
                  </div>
                  <div className="flex gap-2">
                    <input 
                      id="webhook-url"
                      type="text" 
                      placeholder="Webhook URL" 
                      defaultValue="http://api.external.service/webhook"
                      className="flex-1 p-2 bg-slate-900 border border-slate-600 rounded font-mono text-xs text-blue-400 focus:outline-none focus:border-blue-500" 
                    />
                    <button 
                      onClick={() => {
                        const url = (document.getElementById('webhook-url') as HTMLInputElement).value;
                        const output = document.getElementById('diag-output');
                        if(output) output.innerText = '> Triggering Webhook...';
                        fetch(`${API_BASE_URL}/api/v1/diagnostics/webhook`, {
                          method: 'POST',
                          headers: {'Content-Type': 'application/json'},
                          body: JSON.stringify({ url })
                        })
                        .then(res => res.json())
                        .then(data => { 
                          if(output) output.innerText = JSON.stringify(data, null, 2);
                          if (data.vulnerability) {
                            dispatchAttackLog('SSRF', `${API_BASE_URL}/api/v1/diagnostics/webhook`, `url=${url} [VULN TRIGGERED]`, 'allowed');
                          }
                        })
                      }}
                      className="bg-blue-600 hover:bg-blue-500 text-white px-3 rounded text-xs font-bold transition-colors"
                    >
                      Test
                    </button>
                  </div>
                </div>

                {/* Legacy Config Import (XXE) */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label htmlFor="xxe-input" className="text-[10px] font-bold text-slate-400 uppercase block">Legacy XML Config Importer</label>
                    <HintChip label="XXE" onClick={() => setShowInfo(true)} />
                  </div>
                  <div className="flex flex-col gap-2">
                    <textarea 
                      id="xxe-input"
                      placeholder="XML Configuration Data" 
                      defaultValue={'<?xml version="1.0"?>\n<config>\n  <debug>true</debug>\n</config>'} 
                      className="w-full p-2 bg-slate-900 border border-slate-600 rounded font-mono text-xs text-yellow-400 focus:outline-none focus:border-yellow-500 h-16"
                    />
                    <button 
                      onClick={() => {
                        const xml = (document.getElementById('xxe-input') as HTMLTextAreaElement).value;
                        const output = document.getElementById('diag-output');
                        if(output) output.innerText = '> Importing Config...';
                        fetch(`${API_BASE_URL}/api/v1/admin/attack/xxe`, {
                          method: 'POST',
                          headers: {'Content-Type': 'application/json'},
                          body: JSON.stringify({ xml })
                        })
                        .then(res => res.json())
                        .then(data => { 
                          if(output) output.innerText = JSON.stringify(data, null, 2); 
                          if (data.vulnerability) {
                            dispatchAttackLog('XXE', `${API_BASE_URL}/api/v1/admin/attack/xxe`, `xml_payload [VULN TRIGGERED]`, 'allowed');
                          }
                        })
                      }}
                      className="bg-yellow-600 hover:bg-yellow-500 text-white px-3 rounded text-xs font-bold transition-colors self-start h-full"
                    >
                      Import
                    </button>
                  </div>
                </div>

                <div className="p-3 bg-black rounded border border-slate-700 min-h-[100px]">
                  <p className="text-[10px] text-slate-500 font-bold mb-1 uppercase">Terminal Output</p>
                  <pre id="diag-output" className="text-[10px] font-mono text-slate-300 whitespace-pre-wrap">Ready.</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
