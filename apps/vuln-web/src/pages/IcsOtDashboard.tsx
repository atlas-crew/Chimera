import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Terminal, 
  Cpu, 
  ShieldAlert, 
  Eye, 
  Activity,
  Box,
  Binary,
  AlertTriangle,
  Lock
} from 'lucide-react';

export const IcsOtDashboard: React.FC = () => {
  const [systems, setSystems] = useState<any[]>([]);
  const [controllers, setControllers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sysRes, ctrlRes] = await Promise.all([
          fetch('/api/ics/scada/systems'),
          fetch('/api/ics/controllers/status')
        ]);
        const sysData = await sysRes.json();
        const ctrlData = await ctrlRes.json();
        setSystems(sysData.scada_systems || []);
        setControllers(ctrlData.controllers || []);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3 underline decoration-blue-500/30">
            <Cpu className="w-8 h-8 text-blue-600" />
            Industrial Command Center
          </h1>
          <p className="text-slate-500 font-mono text-sm tracking-tight mt-1">OT/ICS Operational Intelligence Interface</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded shadow-sm text-sm font-bold hover:bg-slate-800 transition-all">
            <Terminal className="w-4 h-4" />
            Modbus CLI
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded shadow-sm text-sm font-bold hover:bg-red-700 transition-all animate-pulse">
            <AlertTriangle className="w-4 h-4" />
            SIS Emergency Bypass
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* SCADA Systems Grid */}
        <div className="lg:col-span-8 space-y-8">
          <div className="bg-white border border-slate-200 shadow-sm rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between font-mono">
              <h2 className="font-bold text-slate-800 flex items-center gap-2 uppercase text-xs tracking-widest">
                <Activity className="w-4 h-4 text-blue-500" />
                Active SCADA Instances
              </h2>
              <span className="text-[10px] text-slate-400">Total Systems: {systems.length}</span>
            </div>
            <div className="divide-y divide-slate-100">
              {loading ? (
                <div className="p-12 text-center font-mono text-slate-400">Querying field bus...</div>
              ) : (
                systems.map((sys) => (
                  <div key={sys.system_id} className="p-6 hover:bg-blue-50/30 transition-colors group">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-slate-900">{sys.name}</h3>
                          <span className={`w-2 h-2 rounded-full ${sys.status === 'operational' ? 'bg-emerald-500' : 'bg-yellow-500'}`} />
                        </div>
                        <p className="text-xs text-slate-500 font-medium">{sys.vendor} • {sys.model} • Protocol: {sys.protocol}</p>
                        <div className="flex items-center gap-4 mt-3">
                          <div className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200 font-mono">
                            {sys.location}
                          </div>
                          <div className="text-[10px] text-blue-600 font-bold flex items-center gap-1 hover:underline cursor-pointer">
                            <Eye className="w-3 h-3" />
                            Launch HMI
                          </div>
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 group-hover:bg-white transition-colors">
                        <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">HMI Access Point</p>
                        <code className="text-xs text-blue-600 font-bold">{sys.hmi_access}</code>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Controllers Table */}
          <div className="bg-slate-900 rounded-xl overflow-hidden shadow-2xl border border-slate-800">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="font-bold text-slate-200 flex items-center gap-2 font-mono text-xs uppercase tracking-widest">
                <Settings className="w-4 h-4 text-blue-400" />
                Controller Telemetry
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-slate-300 font-mono text-xs">
                <thead className="bg-slate-800 text-slate-500 uppercase">
                  <tr>
                    <th className="p-4">Controller ID</th>
                    <th className="p-4">Vendor</th>
                    <th className="p-4">Mode</th>
                    <th className="p-4 text-center">CPU</th>
                    <th className="p-4 text-center">Loops</th>
                    <th className="p-4 text-center">Alarms</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {controllers.map((ctrl) => (
                    <tr key={ctrl.controller_id} className="hover:bg-blue-500/5 transition-colors">
                      <td className="p-4 font-bold text-blue-400">{ctrl.controller_id}</td>
                      <td className="p-4">{ctrl.vendor}</td>
                      <td className="p-4 capitalize">{ctrl.mode}</td>
                      <td className="p-4">
                        <div className="w-20 mx-auto bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-blue-500 h-full" style={{ width: `${ctrl.cpu_usage}%` }} />
                        </div>
                      </td>
                      <td className="p-4 text-center">{ctrl.active_loops}</td>
                      <td className="p-4 text-center">
                        <span className={`px-2 py-0.5 rounded-full ${ctrl.alarms_active > 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                          {ctrl.alarms_active}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-4 space-y-8">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2 font-mono text-xs uppercase tracking-widest border-b border-slate-100 pb-2">
              <Box className="w-4 h-4 text-orange-500" />
              Device Integrity
            </h2>
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-orange-50 border border-orange-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold text-orange-800 uppercase">Network Segment</span>
                  <span className="text-[10px] font-bold text-orange-600 bg-white px-1.5 py-0.5 rounded">OT-DMZ</span>
                </div>
                <p className="text-xs text-orange-700 leading-relaxed italic">Segmentation policy check: WARNING. Unpatched devices detected on critical segments.</p>
              </div>
              <button className="w-full py-2 bg-slate-900 text-white rounded-lg text-xs font-bold hover:bg-slate-800 transition-colors flex items-center justify-center gap-2">
                <ShieldAlert className="w-3 h-3 text-red-400" />
                Network Lockdown
              </button>
            </div>
          </div>

          <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 border-dashed">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2 font-mono text-xs uppercase tracking-widest">
              <Binary className="w-4 h-4 text-slate-500" />
              Register Manipulator
            </h2>
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Target Address</label>
                <input type="text" placeholder="0x40001" className="w-full p-2 bg-white border border-slate-200 rounded font-mono text-xs" />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Value (Integer)</label>
                <input type="number" placeholder="0" className="w-full p-2 bg-white border border-slate-200 rounded font-mono text-xs" />
              </div>
              <button className="w-full py-2 border-2 border-slate-900 text-slate-900 rounded font-bold text-xs hover:bg-slate-900 hover:text-white transition-all">
                Write Coils
              </button>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-blue-200 bg-blue-50 flex items-start gap-3">
            <Lock className="w-5 h-5 text-blue-600 shrink-0" />
            <div>
              <p className="text-xs font-bold text-blue-900">Safety Policy Enforcement</p>
              <p className="text-[10px] text-blue-700 mt-1">Interlock system is currently active. Bypassing safety limits requires administrative key-card authorization.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
