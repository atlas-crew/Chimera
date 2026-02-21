import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  FileCheck, 
  AlertCircle, 
  Search, 
  Plus, 
  Heart, 
  Car, 
  Home as HomeIcon,
  ChevronRight,
  ClipboardList
} from 'lucide-react';

export const InsuranceDashboard: React.FC = () => {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/insurance/policies')
      .then(res => res.json())
      .then(data => {
        setPolicies(data.policies || []);
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
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            ProtectFlow Insurance
          </h1>
          <p className="text-slate-500">Policy Management & Claims Processing</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
            <Search className="w-4 h-4" />
            Check Coverage
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg text-sm font-medium text-white hover:bg-blue-700 shadow-sm transition-colors">
            <Plus className="w-4 h-4" />
            Submit New Claim
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Active Policies */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h2 className="font-bold text-slate-900 flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-emerald-500" />
                Active Policies
              </h2>
              <span className="text-[10px] font-bold text-slate-400 uppercase">Coverage Active</span>
            </div>
            <div className="divide-y divide-slate-100">
              {loading ? (
                <div className="p-12 text-center text-slate-400">Retrieving policies...</div>
              ) : (
                policies.map((policy) => (
                  <div key={policy.policy_id} className="p-6 hover:bg-slate-50 transition-colors group cursor-pointer">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                          {policy.policy_type === 'Health' ? <Heart className="w-6 h-6" /> : 
                           policy.policy_type === 'Auto' ? <Car className="w-6 h-6" /> : <HomeIcon className="w-6 h-6" />}
                        </div>
                        <div>
                          <h3 className="font-bold text-slate-900 group-hover:text-blue-600 transition-colors">{policy.insurance_provider} • {policy.policy_type}</h3>
                          <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                            <span className="font-mono">ID: {policy.policy_number}</span>
                            <span className="h-3 w-px bg-slate-200" />
                            <span>Expires: {policy.coverage_end}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right flex items-center gap-4">
                        <div className="hidden md:block">
                          <p className="text-sm font-bold text-slate-900">${policy.premium_monthly}/mo</p>
                          <p className="text-[10px] text-slate-400 uppercase font-bold">Premium</p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-slate-300 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Pending Claims Placeholder */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-100 bg-slate-50/50">
              <h2 className="font-bold text-slate-900 flex items-center gap-2">
                <ClipboardList className="w-5 h-5 text-blue-500" />
                Recent Claims
              </h2>
            </div>
            <div className="p-12 text-center text-slate-400">
              <p className="text-sm font-medium">No active claims found.</p>
              <button className="mt-4 text-xs font-bold text-blue-600 hover:underline">Start a claim request</button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-4 text-sm uppercase tracking-widest border-b border-slate-100 pb-2">Account Overview</h2>
            <div className="space-y-4 pt-2">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500 font-medium">Total Deductible</span>
                <span className="font-bold text-slate-900">$2,500.00</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500 font-medium">Remaining OOP</span>
                <span className="font-bold text-slate-900 text-emerald-600">$420.15</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full w-[85%]" />
              </div>
              <p className="text-[10px] text-slate-400 text-center uppercase font-bold italic">You have almost reached your out-of-pocket maximum</p>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-100 p-6 rounded-2xl relative overflow-hidden">
            <AlertCircle className="w-12 h-12 text-blue-200 absolute -right-2 -bottom-2" />
            <h3 className="font-bold text-blue-900 text-sm mb-2">Need Assistance?</h3>
            <p className="text-xs text-blue-700 leading-relaxed opacity-90">
              Our 24/7 claims advocates are available to help you navigate the process. Contact us at 1-800-PRO-FLOW.
            </p>
            <button className="mt-4 w-full py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors shadow-sm">
              Launch Live Chat
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
