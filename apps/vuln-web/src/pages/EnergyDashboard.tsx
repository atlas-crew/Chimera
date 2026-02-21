import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Activity, 
  Power, 
  MapPin, 
  BarChart3, 
  ShieldAlert,
  AlertCircle,
  Truck,
  Database
} from 'lucide-react';

export const EnergyDashboard: React.FC = () => {
  const [outages, setOutages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Generate some initial outage data
    fetch('/api/v1/energy-utilities/outages/EXP-1')
      .then(res => res.json())
      .then(data => {
        setOutages([data.outage]);
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
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <Zap className="w-8 h-8 text-yellow-500" />
            GridMatrix Utilities
          </h1>
          <p className="text-slate-500">Infrastructure Operations & Outage Management</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
            <Database className="w-4 h-4" />
            Export Grid Config
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-yellow-500 rounded-lg text-sm font-medium text-slate-900 hover:bg-yellow-600 shadow-sm transition-colors">
            <Power className="w-4 h-4" />
            Grid Dispatch
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Real-time Grid Status */}
          <div className="bg-slate-900 rounded-2xl p-6 text-white overflow-hidden relative border border-slate-800 shadow-xl">
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <Activity className="w-5 h-5 text-emerald-400" />
                  Live Grid Load
                </h2>
                <span className="text-xs font-mono bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded border border-emerald-500/30">OPERATIONAL</span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                <div>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Total Output</p>
                  <p className="text-3xl font-bold">1,242 <span className="text-lg font-medium text-slate-500">MW</span></p>
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Grid Frequency</p>
                  <p className="text-3xl font-bold">60.02 <span className="text-lg font-medium text-slate-500">Hz</span></p>
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Active Outages</p>
                  <p className="text-3xl font-bold text-orange-400">03</p>
                </div>
              </div>

              <div className="h-24 flex items-end gap-1 overflow-hidden">
                {[...Array(20)].map((_, i) => (
                  <div 
                    key={i} 
                    className="flex-1 bg-emerald-500/40 rounded-t-sm animate-pulse" 
                    style={{ height: `${Math.random() * 100}%`, animationDelay: `${i * 0.1}s` }} 
                  />
                ))}
              </div>
            </div>
            <div className="absolute right-0 top-0 w-1/2 h-full bg-gradient-to-l from-emerald-500/5 to-transparent pointer-events-none" />
          </div>

          {/* Outage Tracker */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h2 className="font-bold text-slate-900 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-orange-500" />
                Regional Outage Tracker
              </h2>
              <button className="text-sm font-bold text-blue-600 hover:text-blue-700">Dispatch Crew →</button>
            </div>
            <div className="divide-y divide-slate-100">
              {loading ? (
                <div className="p-12 text-center text-slate-400">Syncing telemetry...</div>
              ) : (
                outages.map((outage, i) => (
                  <div key={i} className="p-6 flex items-center justify-between hover:bg-slate-50 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-xl ${outage.status === 'restored' ? 'bg-emerald-100 text-emerald-600' : 'bg-orange-100 text-orange-600'}`}>
                        {outage.status === 'restored' ? <Zap className="w-6 h-6" /> : <AlertCircle className="w-6 h-6" />}
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-900 capitalize">{outage.region} Sector - {outage.status.replace('_', ' ')}</h3>
                        <p className="text-xs text-slate-500 font-medium">{outage.customers_impacted} customers affected • ID: {outage.outage_id}</p>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded ${
                      outage.status === 'restored' ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'
                    }`}>
                      {outage.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-yellow-500" />
              Smart Metering
            </h2>
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Meter #M-84291</p>
                <div className="flex justify-between items-end">
                  <p className="text-xl font-bold text-slate-900">428.5 <span className="text-sm font-medium text-slate-500">kWh</span></p>
                  <button className="text-xs font-bold text-blue-600">Read Telemetry</button>
                </div>
              </div>
              <button className="w-full py-2 border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors flex items-center justify-center gap-2">
                <ShieldAlert className="w-3 h-3 text-red-500" />
                Remote Disconnect
              </button>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Truck className="w-5 h-5 text-blue-500" />
              Asset Registry
            </h2>
            <div className="space-y-3">
              {[
                { type: 'Transformer', id: 'TR-001', status: 'Operational' },
                { type: 'Substation', id: 'SUB-NORTH', status: 'Warning' },
                { type: 'Feeder', id: 'F-12', status: 'Maintenance' },
              ].map((asset, i) => (
                <div key={i} className="flex items-center justify-between text-sm py-2 border-b border-slate-50 last:border-0">
                  <div>
                    <p className="font-bold text-slate-800">{asset.type}</p>
                    <p className="text-[10px] text-slate-500 font-mono">{asset.id}</p>
                  </div>
                  <span className={`text-[10px] font-bold ${
                    asset.status === 'Operational' ? 'text-emerald-600' : 'text-orange-500'
                  }`}>{asset.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
