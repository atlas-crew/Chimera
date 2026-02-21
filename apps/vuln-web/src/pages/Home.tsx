import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Activity, 
  Landmark, 
  ShoppingBag, 
  Radio, 
  Zap, 
  ShieldAlert, 
  Wifi, 
  Building2, 
  Cpu, 
  Shield, 
  Trophy 
} from 'lucide-react';

const PortalCard: React.FC<{
  to: string,
  title: string,
  description: string,
  icon: React.ReactNode,
  color: string,
  api: string,
  disabled?: boolean
}> = ({ to, title, description, icon, color, api, disabled }) => {
  return (
    <Link 
      to={disabled ? '#' : to} 
      className={`group block p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 hover:shadow-md transition-all relative overflow-hidden ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
    >
      <div className={`absolute top-0 left-0 w-1.5 h-full ${color}`} />
      
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg bg-slate-50 dark:bg-slate-700 text-slate-700 dark:text-slate-200 group-hover:scale-110 transition-transform`}>
          {icon}
        </div>
        {disabled && <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded">Coming Soon</span>}
      </div>

      <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">{title}</h3>
      <p className="text-slate-600 dark:text-slate-400 text-sm mb-6 line-clamp-2">{description}</p>
      
      <div className="mt-auto pt-4 border-t border-slate-50 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400 dark:text-slate-500">{api}</span>
          {!disabled && <span className="text-blue-600 dark:text-blue-400 text-sm font-semibold group-hover:translate-x-1 transition-transform">Enter Portal →</span>}
        </div>
      </div>
    </Link>
  );
};

export const Home: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-2xl mb-12">
        <h1 className="text-4xl font-extrabold text-slate-900 dark:text-white mb-4 tracking-tight">Multi-Industry Demo Portals</h1>
        <p className="text-lg text-slate-600 dark:text-slate-400">
          Select a industry-specific portal to test WAF policies, vulnerability detection, and resilience patterns across different data schemas.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">        <PortalCard 
          to="/healthcare"
          title="MediPortal Health"
          description="Patient Electronic Health Records (EHR), appointment scheduling, and prescription history."
          icon={<Activity className="w-6 h-6" />}
          color="bg-emerald-500"
          api="/api/v1/healthcare"
        />
        <PortalCard 
          to="/banking"
          title="SecureBank Pro"
          description="Personal banking dashboard, account transfers, and financial statement management."
          icon={<Landmark className="w-6 h-6" />}
          color="bg-blue-500"
          api="/api/v1/banking"
        />
        <PortalCard 
          to="/ecommerce"
          title="ShopRight Retail"
          description="B2C e-commerce platform with catalog management, checkout, and loyalty tracking."
          icon={<ShoppingBag className="w-6 h-6" />}
          color="bg-orange-500"
          api="/api/v1/ecommerce"
        />
        <PortalCard 
          to="/saas"
          title="Nexus SaaS"
          description="Tenant and user management for a multi-tenant SaaS application, including billing and SSO."
          icon={<Wifi className="w-6 h-6" />}
          color="bg-indigo-500"
          api="/api/v1/saas"
        />
        <PortalCard 
          to="/government"
          title="GovPortal Services"
          description="Citizen services portal for managing benefits, licenses, and public records requests."
          icon={<Building2 className="w-6 h-6" />}
          color="bg-slate-500"
          api="/api/v1/gov"
        />
        <PortalCard 
          to="/telecom"
          title="TelcoConnect"
          description="Subscriber management, SIM swapping, and network provisioning for telecommunications."
          icon={<Radio className="w-6 h-6" />}
          color="bg-purple-500"
          api="/api/v1/telecom"
        />
        <PortalCard 
          to="/energy"
          title="GridMatrix Utilities"
          description="Infrastructure operations, real-time grid load monitoring, and outage tracking."
          icon={<Zap className="w-6 h-6" />}
          color="bg-yellow-500"
          api="/api/v1/energy-utilities"
        />
        <PortalCard 
          to="/ics-ot"
          title="Industrial Command"
          description="Operational Technology (OT) interface for SCADA systems and industrial controllers."
          icon={<Cpu className="w-6 h-6" />}
          color="bg-blue-900"
          api="/api/ics"
        />
        <PortalCard 
          to="/insurance"
          title="ProtectFlow Insurance"
          description="Policy management dashboard for health, auto, and home insurance coverage."
          icon={<Shield className="w-6 h-6" />}
          color="bg-blue-600"
          api="/api/v1/insurance"
        />
        <PortalCard 
          to="/loyalty"
          title="EliteRewards"
          description="Customer loyalty program featuring point balances, transfers, and redemption."
          icon={<Trophy className="w-6 h-6" />}
          color="bg-violet-600"
          api="/api/v1/loyalty"
        />
        <PortalCard 
          to="/admin"
          title="Core Admin Console"
          description="System-wide administration, global audit logs, and security policy overrides."
          icon={<ShieldAlert className="w-6 h-6" />}
          color="bg-red-600"
          api="/api/v1/admin"
        />
      </div>
    </div>
  );
};
