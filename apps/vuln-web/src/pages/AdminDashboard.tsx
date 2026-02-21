import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Users, 
  Settings, 
  Activity, 
  Search, 
  Terminal,
  Lock,
  Eye,
  Trash2,
  FileText
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/saas/audit/logs?limit=10')
      .then(res => res.json())
      .then(data => {
        setLogs(data.logs || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3 underline decoration-red-500/20">
            <ShieldAlert className="w-8 h-8 text-red-600" />
            Security Control Center
          </h1>
          <p className="text-slate-500 font-mono text-sm tracking-tight mt-1">Administrative Terminal • Root Access Level</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded shadow-sm text-sm font-bold hover:bg-slate-800 transition-all">
            <Terminal className="w-4 h-4" />
            System Console
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded shadow-sm text-sm font-bold hover:bg-red-700 transition-all">
            <Lock className="w-4 h-4" />
            Lockdown Domain
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main Log Viewer */}
        <div className="lg:col-span-8 space-y-8">
          <div className="bg-slate-900 rounded-xl overflow-hidden shadow-2xl border border-slate-800">
            <div className="p-4 border-b border-slate-800 bg-slate-800/50 flex items-center justify-between font-mono">
              <h2 className="font-bold text-slate-200 flex items-center gap-2 uppercase text-xs tracking-widest">
                <FileText className="w-4 h-4 text-red-400" />
                Global Audit Logs
              </h2>
              <div className="flex items-center gap-4">
                <span className="text-[10px] text-slate-500">Source: all_blueprints</span>
                <button className="text-[10px] text-red-400 font-bold hover:underline">Clear Logs</button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-slate-300 font-mono text-[11px]">
                <thead className="bg-slate-800/30 text-slate-500 uppercase">
                  <tr>
                    <th className="p-4">Timestamp</th>
                    <th className="p-4">Actor</th>
                    <th className="p-4">Action</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Options</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {loading ? (
                    <tr><td colSpan={5} className="p-12 text-center text-slate-500 italic">Querying audit trail...</td></tr>
                  ) : (
                    logs.map((log) => (
                      <tr key={log.log_id} className="hover:bg-red-500/5 transition-colors">
                        <td className="p-4 text-slate-500">{new Date(log.timestamp).toLocaleTimeString()}</td>
                        <td className="p-4 font-bold text-slate-200">{log.actor}</td>
                        <td className="p-4 capitalize">{log.action.replace('_', ' ')}</td>
                        <td className="p-4">
                          <span className={`px-1.5 py-0.5 rounded ${log.sensitive ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'}`}>
                            {log.sensitive ? 'CRITICAL' : 'INFO'}
                          </span>
                        </td>
                        <td className="p-4 text-right space-x-2">
                          <button className="p-1 hover:text-white transition-colors" title="Inspect Log"><Eye className="w-3.5 h-3.5" /></button>
                          <button className="p-1 hover:text-red-400 transition-colors" title="Purge Record"><Trash2 className="w-3.5 h-3.5" /></button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-500" />
                Identity Management
              </h3>
              <div className="space-y-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input type="text" placeholder="Filter users..." className="w-full pl-9 p-2 bg-slate-50 border border-slate-200 rounded text-sm" />
                </div>
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded group">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500">U{i}</div>
                      <div>
                        <p className="text-sm font-bold text-slate-800 leading-none">user_demo_0{i}</p>
                        <p className="text-[10px] text-slate-500">role: provisioned_member</p>
                      </div>
                    </div>
                    <button className="text-[10px] font-bold text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">Edit Role</button>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-500" />
                Service Topology
              </h3>
              <div className="space-y-4">
                {[
                  { name: 'API Backend', status: 'Healthy', load: '12%' },
                  { name: 'Redis Cache', status: 'Healthy', load: '4%' },
                  { name: 'SQLite Core', status: 'Warning', load: '82%' },
                ].map((svc, i) => (
                  <div key={i} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-slate-700">{svc.name}</span>
                      <span className={`font-bold ${svc.status === 'Healthy' ? 'text-emerald-600' : 'text-orange-500'}`}>{svc.status}</span>
                    </div>
                    <div className="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                      <div className={`h-full ${svc.status === 'Healthy' ? 'bg-emerald-500' : 'bg-orange-500'}`} style={{ width: svc.load }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-4 space-y-8">
          <div className="bg-red-50 border border-red-100 p-6 rounded-xl relative overflow-hidden">
            <ShieldAlert className="w-12 h-12 text-red-100 absolute -right-2 -bottom-2" />
            <h2 className="font-bold text-red-900 mb-4 flex items-center gap-2 font-mono text-xs uppercase tracking-widest border-b border-red-200 pb-2">
              Global Policy Override
            </h2>
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-red-800">Debug Mode</span>
                <div className="w-8 h-4 bg-red-600 rounded-full relative"><div className="absolute right-0.5 top-0.5 w-3 h-3 bg-white rounded-full" /></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-red-800">Relax Isolation</span>
                <div className="w-8 h-4 bg-slate-300 rounded-full relative"><div className="absolute left-0.5 top-0.5 w-3 h-3 bg-white rounded-full" /></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-red-800">Bypass Audit</span>
                <div className="w-8 h-4 bg-slate-300 rounded-full relative"><div className="absolute left-0.5 top-0.5 w-3 h-3 bg-white rounded-full" /></div>
              </div>
              <p className="text-[10px] text-red-700 italic leading-relaxed pt-2 border-t border-red-200">
                Warning: These settings apply globally across all blueprints. Exercise extreme caution.
              </p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2 font-mono text-xs uppercase tracking-widest border-b border-slate-100 pb-2">
              <Settings className="w-4 h-4 text-slate-500" />
              Runtime Config
            </h2>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase">WAF Sensor Endpoint</label>
                <input type="text" value="https://chimera-waf:8443" readOnly className="w-full p-2 bg-slate-50 border border-slate-200 rounded font-mono text-[10px] text-slate-600" />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase">Customer Identifier</label>
                <input type="text" value="chimera-demo-portal" readOnly className="w-full p-2 bg-slate-50 border border-slate-200 rounded font-mono text-[10px] text-slate-600" />
              </div>
              <button className="w-full py-2 border-2 border-slate-900 text-slate-900 rounded font-bold text-xs hover:bg-slate-900 hover:text-white transition-all">
                Export System Dump
              </button>
            </div>
          </div>

          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg text-white">
            <h2 className="font-bold text-slate-200 mb-4 flex items-center gap-2 font-mono text-xs uppercase tracking-widest border-b border-slate-700 pb-2">
              <Terminal className="w-4 h-4 text-green-400" />
              System Diagnostics
            </h2>
            <div className="space-y-6">
              
              {/* Ping Tool (RCE) */}
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">Network Connectivity Check</label>
                <div className="flex gap-2">
                  <input id="ping-host" type="text" placeholder="8.8.8.8" className="w-full p-2 bg-slate-900 border border-slate-600 rounded font-mono text-xs text-green-400 focus:outline-none focus:border-green-500" />
                  <button 
                    onClick={() => {
                      const host = (document.getElementById('ping-host') as HTMLInputElement).value;
                      const output = document.getElementById('diag-output');
                      if(output) output.innerText = '> Pinging...';
                      fetch('/api/v1/diagnostics/ping', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ host })
                      })
                      .then(res => res.json())
                      .then(data => { if(output) output.innerText = data.output || data.error || 'Error'; })
                    }}
                    className="bg-slate-700 hover:bg-slate-600 text-white px-3 rounded text-xs font-bold transition-colors"
                  >
                    Ping
                  </button>
                </div>
              </div>

              {/* Webhook Tool (SSRF) */}
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">Webhook Integration Tester</label>
                <div className="flex gap-2">
                  <input id="webhook-url" type="text" placeholder="http://internal-service/health" className="w-full p-2 bg-slate-900 border border-slate-600 rounded font-mono text-xs text-blue-400 focus:outline-none focus:border-blue-500" />
                  <button 
                    onClick={() => {
                      const url = (document.getElementById('webhook-url') as HTMLInputElement).value;
                      const output = document.getElementById('diag-output');
                      if(output) output.innerText = '> Fetching URL...';
                      fetch('/api/v1/diagnostics/webhook', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ url })
                      })
                      .then(res => res.json())
                      .then(data => { if(output) output.innerText = JSON.stringify(data, null, 2); })
                    }}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-3 rounded text-xs font-bold transition-colors"
                  >
                    Test
                  </button>
                </div>
              </div>

              {/* Legacy Config Import (XXE) */}
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">Legacy Config Import (XML)</label>
                <div className="flex gap-2">
                  <textarea 
                    id="xxe-input" 
                    placeholder={'<?xml version="1.0"?>\n<config>\n  <debug>true</debug>\n</config>'} 
                    className="w-full p-2 bg-slate-900 border border-slate-600 rounded font-mono text-xs text-yellow-400 focus:outline-none focus:border-yellow-500 h-16"
                  />
                  <button 
                    onClick={() => {
                      const xml = (document.getElementById('xxe-input') as HTMLTextAreaElement).value;
                      const output = document.getElementById('diag-output');
                      if(output) output.innerText = '> Importing Config...';
                      fetch('/api/v1/admin/attack/xxe', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ xml })
                      })
                      .then(res => res.json())
                      .then(data => { if(output) output.innerText = JSON.stringify(data, null, 2); })
                    }}
                    className="bg-yellow-600 hover:bg-yellow-500 text-white px-3 rounded text-xs font-bold transition-colors self-start h-full"
                  >
                    Import
                  </button>
                </div>
              </div>

              {/* Privilege Escalation */}
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">User Privilege Manager</label>
                <div className="flex gap-2">
                  <input id="elevate-user" type="text" placeholder="USR-0001" className="w-full p-2 bg-slate-900 border border-slate-600 rounded font-mono text-xs text-red-400 focus:outline-none focus:border-red-500" />
                  <button 
                    onClick={() => {
                      const userId = (document.getElementById('elevate-user') as HTMLInputElement).value;
                      const output = document.getElementById('diag-output');
                      if(output) output.innerText = '> Escalating Privileges...';
                      fetch(`/api/v1/admin/users/${userId}/elevate`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ role: 'admin' })
                      })
                      .then(res => res.json())
                      .then(data => { if(output) output.innerText = JSON.stringify(data, null, 2); })
                    }}
                    className="bg-red-600 hover:bg-red-500 text-white px-3 rounded text-xs font-bold transition-colors"
                  >
                    Escalate
                  </button>
                </div>
              </div>

              <div className="bg-black rounded p-3 font-mono text-[10px] text-slate-300 h-64 overflow-auto whitespace-pre-wrap" id="diag-output">
                {'>'} System ready.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
