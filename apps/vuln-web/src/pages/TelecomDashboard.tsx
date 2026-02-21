import React, { useState, useEffect } from 'react';
import {
  User,
  Smartphone,
  Radio,
  Activity,
  CreditCard,
  ShieldAlert,
  Settings,
  RefreshCw,
  Zap
} from 'lucide-react';

export const TelecomDashboard: React.FC = () => {
  const [subscriber, setSubscriber] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const subscriberId = 'SUB-12345'; // Hardcoded for demo

  useEffect(() => {
    fetch(`/api/v1/telecom/subscribers/${subscriberId}/profile`)
      .then(res => res.json())
      .then(data => {
        setSubscriber(data.subscriber);
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
            <Radio className="w-8 h-8 text-purple-600" />
            TelcoConnect
          </h1>
          <p className="text-slate-500">Network & Subscriber Management Portal</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
            <Activity className="w-4 h-4" />
            Network Status
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-lg text-sm font-medium text-white hover:bg-purple-700 shadow-sm transition-colors">
            <Zap className="w-4 h-4" />
            Provision Device
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Subscriber Profile */}
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h2 className="font-bold text-slate-900 flex items-center gap-2">
                <User className="w-5 h-5 text-purple-500" />
                Subscriber Profile
              </h2>
              <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-[10px] font-bold uppercase rounded-full">Active</span>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="py-8 text-center text-slate-400 font-medium">Loading subscriber data...</div>
              ) : subscriber ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Subscriber Name</p>
                      <p className="text-lg font-bold text-slate-900">{subscriber.name}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Phone Number (MSISDN)</p>
                      <p className="text-lg font-mono font-bold text-slate-900">{subscriber.msisdn}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Account ID</p>
                      <p className="text-sm font-mono text-slate-600">{subscriber.subscriber_id}</p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Service Plan</p>
                      <p className="text-lg font-bold text-slate-900 capitalize">{subscriber.plan_id} Data</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Last Activity</p>
                      <p className="text-sm text-slate-600">{new Date(subscriber.last_seen).toLocaleString()}</p>
                    </div>
                    <button className="text-sm font-bold text-purple-600 hover:text-purple-700 transition-colors">Edit Profile Details →</button>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-red-500">Failed to load subscriber profile.</div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center mb-4 text-orange-600">
                <Smartphone className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 mb-2">SIM Management</h3>
              <p className="text-xs text-slate-500 mb-4 leading-relaxed">Change SIM cards or activate an eSIM for this subscriber. Identity verification is required.</p>
              <button className="w-full py-2 bg-slate-900 text-white rounded-lg text-xs font-bold hover:bg-slate-800 transition-colors flex items-center justify-center gap-2">
                <RefreshCw className="w-3 h-3" />
                Initiate SIM Swap
              </button>
            </div>
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center mb-4 text-blue-600">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 mb-2">Usage Policies</h3>
              <p className="text-xs text-slate-500 mb-4 leading-relaxed">Manage network throttling, roaming overrides, and bandwidth limits for this account.</p>
              <button className="w-full py-2 border border-slate-200 text-slate-700 rounded-lg text-xs font-bold hover:bg-slate-50 transition-colors flex items-center justify-center gap-2">
                <Settings className="w-3 h-3" />
                Update Policy
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-4">Billing Summary</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-end pb-4 border-b border-slate-100">
                <div>
                  <p className="text-xs font-bold text-slate-400 uppercase">Current Balance</p>
                  <p className="text-2xl font-bold text-slate-900">$142.50</p>
                </div>
                <CreditCard className="w-6 h-6 text-slate-300" />
              </div>
              <div className="space-y-2">
                <p className="text-xs font-bold text-slate-400 uppercase">Latest Invoice</p>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Inv-2024-12</span>
                  <span className="font-bold text-slate-900">$85.00</span>
                </div>
                <button className="text-xs font-bold text-purple-600 hover:underline">Download Statement</button>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 border border-purple-100 p-6 rounded-2xl">
            <div className="flex gap-3 mb-4">
              <ShieldAlert className="w-6 h-6 text-purple-600 shrink-0" />
              <div>
                <h3 className="font-bold text-purple-900 text-sm italic">Lawful Intercept Active</h3>
                <p className="text-xs text-purple-700 mt-1 leading-relaxed italic opacity-80">
                  This account is subject to enhanced network monitoring. CDR records are being streamed to authorized endpoints.
                </p>
              </div>
            </div>
            <div className="bg-white/50 rounded-lg p-3">
              <div className="flex items-center justify-between text-[10px] font-bold text-purple-800 uppercase mb-1">
                <span>Buffer Status</span>
                <span>Healthy</span>
              </div>
              <div className="w-full bg-purple-200 h-1 rounded-full overflow-hidden">
                <div className="bg-purple-600 h-full w-1/4" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
