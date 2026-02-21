import React, { useState, useEffect } from 'react';
import {
  Users,
  Layers,
  Settings,
  CreditCard,
  Plus,
  MoreHorizontal,
  Briefcase
} from 'lucide-react';

export const SaasDashboard: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const tenantId = 'tenant-1'; // Hardcoded for demo

  useEffect(() => {
    fetch(`/api/v1/saas/tenants/${tenantId}/projects`)
      .then(res => res.json())
      .then(data => {
        setProjects(data.projects || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-slate-200 hidden lg:flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-3 px-3 py-2 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-100 cursor-pointer">
            <div className="w-6 h-6 rounded bg-indigo-200 flex items-center justify-center font-bold text-xs">A</div>
            <span className="font-bold text-sm">Acme Corp</span>
            <MoreHorizontal className="w-4 h-4 ml-auto opacity-50" />
          </div>
        </div>
        <nav className="flex-1 px-4 space-y-1">
          {[
            { label: 'Projects', icon: Briefcase, active: true },
            { label: 'Team', icon: Users },
            { label: 'Integrations', icon: Layers },
            { label: 'Billing', icon: CreditCard },
            { label: 'Settings', icon: Settings },
          ].map((item) => (
            <a key={item.label} href="#" className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${item.active ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50'}`}>
              <item.icon className={`w-4 h-4 ${item.active ? 'text-indigo-600' : 'text-slate-400'}`} />
              {item.label}
            </a>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-200">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs font-semibold text-slate-500 mb-2">STORAGE USED</p>
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mb-2">
              <div className="bg-indigo-500 h-full w-3/4" />
            </div>
            <p className="text-xs text-slate-600">7.5 GB / 10 GB</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 bg-slate-50 p-8 overflow-y-auto">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Projects</h1>
            <p className="text-slate-500 text-sm">Manage your team's ongoing initiatives.</p>
          </div>
          <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Project
          </button>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {loading ? (
            <div className="col-span-full text-center py-12 text-slate-400">Loading projects...</div>
          ) : (
            projects.map((project: any) => (
              <div key={project.project_id} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                    <Briefcase className="w-5 h-5 text-indigo-600" />
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-[10px] font-bold uppercase rounded-full">Active</span>
                </div>
                <h3 className="font-bold text-slate-900 mb-1">{project.name}</h3>
                <p className="text-xs text-slate-500 mb-4">Last updated {new Date(project.last_updated).toLocaleDateString()}</p>
                <div className="flex items-center -space-x-2">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="w-6 h-6 rounded-full border-2 border-white bg-slate-200" />
                  ))}
                  <div className="w-6 h-6 rounded-full border-2 border-white bg-slate-100 flex items-center justify-center text-[10px] font-medium text-slate-500">+2</div>
                </div>
              </div>
            ))
          )}
          
          {/* Empty State / Add New Placeholder */}
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 flex flex-col items-center justify-center text-center hover:bg-slate-50/50 transition-colors cursor-pointer group h-full min-h-[200px]">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Plus className="w-6 h-6 text-slate-400" />
            </div>
            <h3 className="font-medium text-slate-900">Create Project</h3>
            <p className="text-xs text-slate-500 mt-1">Start a new workspace</p>
          </div>
        </div>
      </div>
    </div>
  );
};