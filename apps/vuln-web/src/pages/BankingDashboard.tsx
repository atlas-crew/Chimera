import React, { useState, useEffect } from 'react';
import {
  Landmark,
  CreditCard,
  ArrowRightLeft,
  DollarSign,
  Shield,
  TrendingUp,
  History,
  Send
} from 'lucide-react';

export const BankingDashboard: React.FC = () => {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [transferAmount, setTransferAmount] = useState('');
  const [transferStatus, setTransferStatus] = useState<'idle' | 'success' | 'error'>('idle');

  useEffect(() => {
    fetch('/api/v1/banking/accounts')
      .then(res => res.json())
      .then(data => {
        setAccounts(data.accounts || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accounts.length) return;

    try {
      const res = await fetch('/api/v1/banking/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_account: accounts[0].account_id,
          to_account: 'ACC-external-999', // Simulating external transfer
          amount: parseFloat(transferAmount)
        })
      });
      
      if (res.ok) {
        setTransferStatus('success');
        setTransferAmount('');
        // Refresh accounts
        const accRes = await fetch('/api/v1/banking/accounts');
        const accData = await accRes.json();
        setAccounts(accData.accounts || []);
      } else {
        setTransferStatus('error');
      }
    } catch (err) {
      setTransferStatus('error');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <Landmark className="w-8 h-8 text-blue-600" />
            SecureBank Pro
          </h1>
          <p className="text-slate-500">Personal Banking Dashboard • Welcome back, User</p>
        </div>
        <div className="bg-blue-50 text-blue-700 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
          <Shield className="w-4 h-4" />
          Secure Session Active
        </div>
      </div>

      {/* Account Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {loading ? (
          <div className="col-span-2 text-center py-12 text-slate-400">Loading accounts...</div>
        ) : (
          accounts.map((acc, idx) => (
            <div key={acc.account_id} className={`p-6 rounded-xl border ${idx === 0 ? 'bg-gradient-to-br from-blue-600 to-blue-800 text-white border-blue-600' : 'bg-white border-slate-200 text-slate-900'}`}>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className={`text-sm font-medium ${idx === 0 ? 'text-blue-100' : 'text-slate-500'}`}>{acc.account_type.toUpperCase()}</p>
                  <p className="text-2xl font-bold mt-1">
                    {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(acc.balance)}
                  </p>
                </div>
                <CreditCard className={`w-6 h-6 ${idx === 0 ? 'text-blue-200' : 'text-slate-400'}`} />
              </div>
              <div className="flex justify-between items-end">
                <p className={`font-mono text-sm ${idx === 0 ? 'text-blue-200' : 'text-slate-500'}`}>**** **** **** {acc.account_id.slice(-4)}</p>
                <span className={`text-xs px-2 py-1 rounded ${idx === 0 ? 'bg-blue-500/50 text-white' : 'bg-slate-100 text-slate-600'}`}>Active</span>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quick Transfer */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
            <ArrowRightLeft className="w-5 h-5 text-blue-500" />
            Quick Transfer
          </h2>
          <form onSubmit={handleTransfer} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">From Account</label>
              <select className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm">
                {accounts.map(acc => (
                  <option key={acc.account_id} value={acc.account_id}>
                    {acc.account_type} (...{acc.account_id.slice(-4)})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Amount ($)</label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input 
                  type="number" 
                  step="0.01"
                  className="w-full pl-9 p-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="0.00"
                  value={transferAmount}
                  onChange={e => setTransferAmount(e.target.value)}
                />
              </div>
            </div>
            <button className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
              <Send className="w-4 h-4" />
              Transfer Funds
            </button>
            {transferStatus === 'success' && (
              <p className="text-xs text-emerald-600 font-medium text-center">Transfer successful!</p>
            )}
            {transferStatus === 'error' && (
              <p className="text-xs text-red-600 font-medium text-center">Transfer failed. Try again.</p>
            )}
          </form>
        </div>

        {/* Recent Transactions */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <h2 className="font-bold text-slate-900 flex items-center gap-2">
              <History className="w-5 h-5 text-blue-500" />
              Recent Activity
            </h2>
            <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">View Statement</button>
          </div>
          <div className="divide-y divide-slate-100">
            {[1, 2, 3, 4, 5].map((_, i) => (
              <div key={i} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-full ${i % 2 === 0 ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-600'}`}>
                    {i % 2 === 0 ? <TrendingUp className="w-4 h-4" /> : <DollarSign className="w-4 h-4" />}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-900">{i % 2 === 0 ? 'Payroll Deposit' : 'Merchant Payment'}</p>
                    <p className="text-xs text-slate-500">Today, 10:2{i} AM</p>
                  </div>
                </div>
                <span className={`font-mono font-medium ${i % 2 === 0 ? 'text-emerald-600' : 'text-slate-900'}`}>
                  {i % 2 === 0 ? '+' : '-'}${Math.floor(Math.random() * 500)}.00
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};