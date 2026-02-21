import React, { useState, useEffect } from 'react';
import {
  FileText,
  Calendar,
  Pill,
  Search,
  Download,
  Plus,
  AlertCircle,
  User as UserIcon,
  MoreVertical,
  Info
} from 'lucide-react';
import { VulnerabilityModal, VulnerabilityInfo } from '../components/VulnerabilityModal';

const healthcareInfo: VulnerabilityInfo = {
  title: "Healthcare System Vulnerabilities",
  description: "This portal demonstrates common security flaws in Electronic Health Record (EHR) systems, focusing on PHI exposure and injection attacks.",
  swaggerTag: "Healthcare",
  vulns: [
    {
      name: "SQL Injection (Search)",
      description: "The patient search functionality is vulnerable to SQL injection. Attackers can bypass authentication or extract the entire database.",
      severity: "critical",
      endpoint: "GET /api/v1/healthcare/records/search?q="
    },
    {
      name: "Broken Object Level Authorization (BOLA/IDOR)",
      description: "Medical records can be accessed by changing the record ID in the API call, even without ownership permissions.",
      severity: "high",
      endpoint: "GET /api/v1/healthcare/records/{record_id}"
    },
    {
      name: "PHI Data Exposure",
      description: "API responses contain excessive sensitive data (SSNs, full addresses) that is not needed for the frontend view.",
      severity: "high",
      endpoint: "GET /api/v1/healthcare/records"
    }
  ]
};

export const HealthcareDashboard: React.FC = () => {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showInfo, setShowInfo] = useState(false);

  const fetchRecords = async (query = '') => {
    setLoading(true);
    try {
      const url = query 
        ? `/api/v1/healthcare/records/search?q=${encodeURIComponent(query)}` 
        : '/api/v1/healthcare/records';
      
      const response = await fetch(url);
      const data = await response.json();
      
      // The search endpoint returns {results, count}, list returns {records, total_count}
      const recordsList = data.results || data.records || [];
      setRecords(recordsList);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError('Connection to healthcare services failed. Verify the backend is online.');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchRecords(searchQuery);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <VulnerabilityModal isOpen={showInfo} onClose={() => setShowInfo(false)} info={healthcareInfo} />
      
      {/* Dashboard Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">MediPortal Online</h1>
            <button 
              onClick={() => setShowInfo(true)}
              className="p-1.5 text-blue-600 bg-blue-50 dark:bg-blue-900/30 dark:text-blue-400 rounded-full hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
              title="View Vulnerability Info"
            >
              <Info className="w-5 h-5" />
            </button>
          </div>
          <p className="text-slate-500 dark:text-slate-400">Welcome, Provider Admin. Managing 12 total patient records.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
            <Download className="w-4 h-4" />
            Export Audit Logs
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg text-sm font-medium text-white hover:bg-blue-700 shadow-sm transition-colors">
            <Plus className="w-4 h-4" />
            Add New Record
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[
          { label: 'Active Patients', value: '842', icon: UserIcon, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20' },
          { label: 'Appointments Today', value: '18', icon: Calendar, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
          { label: 'Pending Prescriptions', value: '42', icon: Pill, color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-900/20' },
          { label: 'System Alerts', value: '3', icon: AlertCircle, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20' },
        ].map((stat, i) => (
          <div key={i} className="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${stat.bg} ${stat.color}`}>
                <stat.icon className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{stat.label}</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Patient Records List */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50 flex flex-col md:flex-row justify-between items-center gap-4">
              <h2 className="font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-500" />
                Electronic Health Records
              </h2>
              <form onSubmit={handleSearch} className="relative w-full md:w-64" id="healthcare-search-form">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input 
                  id="healthcare-search-input"
                  type="text" 
                  placeholder="Search by name or ID..." 
                  className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </form>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-700">
              {loading ? (
                <div className="p-12 text-center text-slate-500 dark:text-slate-400">Loading patient records...</div>
              ) : error ? (
                <div className="p-12 text-center">
                  <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                  <p className="text-red-600 font-medium">{error}</p>
                </div>
              ) : records.length === 0 ? (
                <div className="p-12 text-center text-slate-500 dark:text-slate-400">No records found matching your search.</div>
              ) : (
                records.map((record) => (
                  <div key={record.record_id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-300 font-bold">
                          {record.patient_name?.charAt(0)}
                        </div>
                        <div>
                          <h3 className="font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{record.patient_name}</h3>
                          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
                            <span className="font-mono">ID: {record.patient_id}</span>
                            <span className="h-3 w-px bg-slate-200 dark:bg-slate-600" />
                            <span>DOB: {record.dob}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="hidden md:block text-right mr-4">
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                            record.diagnosis?.includes('Healthy') ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          }`}>
                            {record.diagnosis}
                          </span>
                        </div>
                        <button className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
                          <MoreVertical className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-700 text-center">
              <button className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">View All Patient Records</button>
            </div>
          </div>
        </div>

        {/* Sidebar Widgets */}
        <div className="space-y-8">
          {/* Quick Actions */}
          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
            <h2 className="font-bold text-slate-800 dark:text-white mb-4">Internal Tools</h2>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Upload Lab', icon: FileText },
                { label: 'Schedule', icon: Calendar },
                { label: 'Rx Refill', icon: Pill },
                { label: 'HIPAA Export', icon: Download },
              ].map((tool, i) => (
                <button key={i} className="flex flex-col items-center gap-2 p-4 rounded-lg border border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 hover:border-blue-200 dark:hover:border-blue-900 transition-all">
                  <tool.icon className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300">{tool.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* System Status / PHI Warning */}
          <div className="bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-900/30 p-6 rounded-xl">
            <div className="flex gap-3">
              <AlertCircle className="w-6 h-6 text-orange-600 dark:text-orange-500 shrink-0" />
              <div>
                <h3 className="font-bold text-orange-800 dark:text-orange-400 text-sm">Security Policy Alert</h3>
                <p className="text-xs text-orange-700 dark:text-orange-300 mt-1 leading-relaxed">
                  PHI data access is currently unrestricted for authorized testing. All activity is monitored by the  WAF.
                </p>
                <div className="mt-4 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-[10px] font-bold text-orange-800/60 dark:text-orange-400/60 uppercase">
                    <span>Audit Status</span>
                    <span className="text-emerald-600 dark:text-emerald-400">Active</span>
                  </div>
                  <div className="w-full bg-orange-200 dark:bg-orange-900/30 h-1 rounded-full overflow-hidden">
                    <div className="bg-orange-500 h-full w-3/4" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
