import React, { useState } from 'react';
import { 
  Trophy, 
  Gift, 
  ArrowRightLeft, 
  Star, 
  TrendingUp, 
  Clock,
  QrCode,
  Tag
} from 'lucide-react';

export const LoyaltyDashboard: React.FC = () => {
  const [transferAmount, setTransferAmount] = useState('');

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <Trophy className="w-8 h-8 text-indigo-600" />
            EliteRewards
          </h1>
          <p className="text-slate-500 font-medium">Premier Status • Member since 2022</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm">
            <QrCode className="w-4 h-4" />
            Digital Card
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 rounded-lg text-sm font-medium text-white hover:bg-indigo-700 shadow-sm transition-colors">
            <Gift className="w-4 h-4" />
            Redeem Points
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Balance Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-indigo-600 to-violet-700 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
              <Star className="w-24 h-24 text-white/10 absolute -right-4 -top-4 rotate-12" />
              <div className="relative z-10">
                <p className="text-indigo-100 text-xs font-bold uppercase tracking-widest mb-1">Available Balance</p>
                <p className="text-4xl font-extrabold mb-4">42,850 <span className="text-lg font-medium opacity-70">pts</span></p>
                <div className="flex items-center gap-2 text-sm text-indigo-100 bg-white/10 backdrop-blur-sm w-fit px-3 py-1 rounded-full">
                  <TrendingUp className="w-3 h-3" />
                  +1,200 earned this month
                </div>
              </div>
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
              <div>
                <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-1">Next Tier Progress</p>
                <p className="text-xl font-bold text-slate-900 mb-2">Diamond Status</p>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2">
                  <div className="bg-indigo-500 h-full w-[72%]" />
                </div>
                <p className="text-[10px] text-slate-500">7,150 points needed to upgrade tier</p>
              </div>
              <button className="text-xs font-bold text-indigo-600 hover:underline text-left mt-4">View Tier Benefits →</button>
            </div>
          </div>

          {/* Transfers */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-100 bg-slate-50/50">
              <h2 className="font-bold text-slate-900 flex items-center gap-2">
                <ArrowRightLeft className="w-5 h-5 text-indigo-500" />
                Peer-to-Peer Transfer
              </h2>
            </div>
            <div className="p-6">
              <p className="text-sm text-slate-500 mb-6 leading-relaxed">
                Send your points to friends or family instantly. Note: Transfers are final and cannot be reversed once processed.
              </p>
              <form className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-1">
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Recipient ID</label>
                  <input type="text" placeholder="MEM-84291" className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm" />
                </div>
                <div className="md:col-span-1">
                  <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Amount</label>
                  <input 
                    type="number" 
                    placeholder="0" 
                    className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
                    value={transferAmount}
                    onChange={e => setTransferAmount(e.target.value)}
                  />
                </div>
                <div className="md:col-span-1 flex items-end">
                  <button className="w-full py-2 bg-slate-900 text-white rounded-lg text-sm font-bold hover:bg-slate-800 transition-colors">
                    Send Points
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Recent History */}
        <div className="space-y-8">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-slate-50/50">
              <h2 className="font-bold text-slate-900 flex items-center gap-2 text-sm uppercase tracking-widest">
                <Clock className="w-4 h-4 text-indigo-500" />
                Recent Activity
              </h2>
            </div>
            <div className="divide-y divide-slate-100">
              {[
                { label: 'Booking Reward', pts: '+450', date: 'Dec 28', type: 'earn' },
                { label: 'Transfer Out', pts: '-1,000', date: 'Dec 24', type: 'spend' },
                { label: 'Partner Bonus', pts: '+250', date: 'Dec 20', type: 'earn' },
                { label: 'Retail Purchase', pts: '+85', date: 'Dec 15', type: 'earn' },
              ].map((act, i) => (
                <div key={i} className="p-4 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-slate-800">{act.label}</p>
                    <p className="text-[10px] text-slate-400">{act.date}</p>
                  </div>
                  <span className={`font-mono font-bold ${act.type === 'earn' ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {act.pts}
                  </span>
                </div>
              ))}
            </div>
            <button className="w-full py-3 bg-slate-50 text-[10px] font-bold text-slate-400 uppercase hover:bg-slate-100 transition-colors">View All Activity</button>
          </div>

          <div className="bg-amber-50 border border-amber-100 p-6 rounded-2xl">
            <div className="flex gap-3">
              <Tag className="w-6 h-6 text-amber-600 shrink-0" />
              <div>
                <h3 className="font-bold text-amber-900 text-sm italic">Flash Partner Offer</h3>
                <p className="text-xs text-amber-700 mt-1 leading-relaxed opacity-80 italic">
                  Earn 5x points on all purchases at participating Global Tech locations through the end of the year.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
