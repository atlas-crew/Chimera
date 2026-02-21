import React, { useState } from 'react';
import {
  Building2,
  Search,
  FileText,
  UserCheck,
  AlertTriangle
} from 'lucide-react';

export const GovernmentDashboard: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery) return;
    
    setSearching(true);
    try {
      // Vulnerable search endpoint
      const res = await fetch(`/api/v1/gov/benefits/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="bg-slate-100 min-h-full">
      <div className="bg-slate-800 text-white pb-24">
        <div className="container mx-auto px-4 pt-12 pb-12">
          <div className="flex items-center gap-3 mb-6">
            <Building2 className="w-10 h-10 text-slate-300" />
            <h1 className="text-3xl font-bold tracking-tight">GovPortal Services</h1>
          </div>
          <p className="text-xl text-slate-300 max-w-2xl">
            Secure access to government services, benefits, and public records for citizens and authorized personnel.
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 -mt-16 pb-12">
        {/* Main Search Card */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Find Benefits & Services</h2>
          <form onSubmit={handleSearch} className="flex gap-4">
            <div className="relative flex-grow">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input 
                type="text" 
                placeholder="Search by Applicant Name or ID..." 
                className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500 transition-all"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="bg-slate-900 text-white px-8 py-3 rounded-lg font-bold hover:bg-slate-800 transition-colors">
              Search
            </button>
          </form>

          {/* Search Results */}
          {(searching || searchResults.length > 0) && (
            <div className="mt-8 border-t border-slate-100 pt-6">
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Search Results</h3>
              {searching ? (
                <p className="text-slate-500">Searching records...</p>
              ) : (
                <div className="space-y-4">
                  {searchResults.map((result: any, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <div>
                        <p className="font-bold text-slate-900">{result.applicant_name || 'Restricted Record'}</p>
                        <p className="text-sm text-slate-600 font-mono">ID: {result.application_id || result.citizen_id}</p>
                      </div>
                      <span className="px-3 py-1 bg-white border border-slate-200 text-xs font-bold rounded-full text-slate-600">
                        {result.status || 'Pending'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Service Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 text-blue-700">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-slate-900 mb-2">My Cases</h3>
            <p className="text-slate-600 text-sm mb-4">Track the status of your applications and requests.</p>
            <a href="#" className="text-blue-700 font-medium text-sm hover:underline">View Active Cases →</a>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center mb-4 text-emerald-700">
              <UserCheck className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-slate-900 mb-2">Identity & Access</h3>
            <p className="text-slate-600 text-sm mb-4">Manage digital ID, access cards, and clearance levels.</p>
            <a href="#" className="text-emerald-700 font-medium text-sm hover:underline">Manage Identity →</a>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4 text-orange-700">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-slate-900 mb-2">Emergency Alerts</h3>
            <p className="text-slate-600 text-sm mb-4">Configure local notifications and broadcast settings.</p>
            <a href="#" className="text-orange-700 font-medium text-sm hover:underline">Alert Settings →</a>
          </div>
        </div>
      </div>
    </div>
  );
};