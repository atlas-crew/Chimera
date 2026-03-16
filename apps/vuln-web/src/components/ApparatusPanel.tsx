import React, { useEffect, useState } from 'react';
import { Activity, Radio, RefreshCw, Server, Zap } from 'lucide-react';
import {
  ApparatusHistoryEntry,
  ApparatusStatusResponse,
  getApparatusHistory,
  getApparatusStatus,
  startApparatusGhosts,
  stopApparatusGhosts,
} from '../features/apparatus/api';

function formatTimestamp(value?: string) {
  if (!value) {
    return 'Unknown';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export const ApparatusPanel: React.FC = () => {
  const [status, setStatus] = useState<ApparatusStatusResponse | null>(null);
  const [history, setHistory] = useState<ApparatusHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<'start' | 'stop' | 'refresh' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rps, setRps] = useState('5');
  const [duration, setDuration] = useState('30000');

  const load = async (mode: 'initial' | 'refresh' = 'initial') => {
    if (mode === 'refresh') {
      setActionLoading('refresh');
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const [statusResponse, historyResponse] = await Promise.all([
        getApparatusStatus(),
        getApparatusHistory(5),
      ]);
      setStatus(statusResponse);
      setHistory(historyResponse.entries);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Apparatus state.');
    } finally {
      setLoading(false);
      setActionLoading(null);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleStart = async () => {
    setActionLoading('start');
    setError(null);

    try {
      await startApparatusGhosts({
        rps: Number(rps),
        duration: Number(duration),
      });
      await load('refresh');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start ghost traffic.');
      setActionLoading(null);
    }
  };

  const handleStop = async () => {
    setActionLoading('stop');
    setError(null);

    try {
      await stopApparatusGhosts();
      await load('refresh');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop ghost traffic.');
      setActionLoading(null);
    }
  };

  const connectionTone = !status
    ? 'bg-slate-100 text-slate-600'
    : !status.enabled
      ? 'bg-amber-100 text-amber-700'
      : status.reachable
        ? 'bg-emerald-100 text-emerald-700'
        : 'bg-red-100 text-red-700';

  const connectionLabel = !status
    ? 'Loading'
    : !status.enabled
      ? 'Disabled'
      : status.reachable
        ? 'Connected'
        : 'Unreachable';

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between gap-4">
        <div>
          <h2 className="font-bold text-slate-900 flex items-center gap-2 text-xs uppercase tracking-widest">
            <Server className="w-4 h-4 text-cyan-600" />
            Apparatus Integration
          </h2>
          <p className="text-[11px] text-slate-500 mt-1">
            External traffic orchestration, ghost controls, and recent Apparatus activity.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load('refresh')}
          className="inline-flex items-center gap-2 px-3 py-2 rounded text-xs font-bold text-slate-700 bg-white border border-slate-200 hover:bg-slate-100 transition-colors"
          disabled={actionLoading === 'refresh'}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${actionLoading === 'refresh' ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="p-6 space-y-6">
        <div className="flex flex-col lg:flex-row gap-4 lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${connectionTone}`}>
              <Radio className="w-3 h-3" />
              {connectionLabel}
            </div>
            <div className="text-xs text-slate-600">
              <span className="font-bold text-slate-800">Base URL:</span>{' '}
              {status?.baseUrl || 'Not configured'}
            </div>
            <div className="text-xs text-slate-600">
              <span className="font-bold text-slate-800">Health:</span>{' '}
              {status?.health?.status || 'Unavailable'}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 min-w-[220px]">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Ghost Traffic</div>
              <div className="text-lg font-bold text-slate-900 mt-1">
                {status?.ghosts?.running ? 'Running' : 'Stopped'}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">History</div>
              <div className="text-lg font-bold text-slate-900 mt-1">{history.length}</div>
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {error}
          </div>
        )}

        {!error && status?.message && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
            {status.message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-6">
          <div className="p-4 rounded-xl bg-slate-900 text-white border border-slate-800">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-cyan-300 mb-4">
              <Zap className="w-4 h-4" />
              Ghost Traffic Controls
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                RPS
                <input
                  value={rps}
                  onChange={(event) => setRps(event.target.value)}
                  className="mt-1 w-full p-2 bg-slate-950 border border-slate-700 rounded text-xs text-cyan-300 font-mono"
                />
              </label>
              <label className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Duration (ms)
                <input
                  value={duration}
                  onChange={(event) => setDuration(event.target.value)}
                  className="mt-1 w-full p-2 bg-slate-950 border border-slate-700 rounded text-xs text-cyan-300 font-mono"
                />
              </label>
            </div>
            <div className="flex gap-3 mt-4">
              <button
                type="button"
                onClick={() => void handleStart()}
                disabled={loading || actionLoading === 'start' || status?.enabled === false}
                className="px-4 py-2 rounded bg-cyan-500 text-slate-950 text-xs font-bold hover:bg-cyan-400 transition-colors disabled:opacity-50"
              >
                {actionLoading === 'start' ? 'Starting...' : 'Start Ghosts'}
              </button>
              <button
                type="button"
                onClick={() => void handleStop()}
                disabled={loading || actionLoading === 'stop' || status?.enabled === false}
                className="px-4 py-2 rounded bg-slate-700 text-white text-xs font-bold hover:bg-slate-600 transition-colors disabled:opacity-50"
              >
                {actionLoading === 'stop' ? 'Stopping...' : 'Stop Ghosts'}
              </button>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-700 mb-4">
              <Activity className="w-4 h-4 text-cyan-600" />
              Recent Apparatus History
            </div>

            {loading ? (
              <p className="text-xs text-slate-500">Loading Apparatus activity...</p>
            ) : history.length === 0 ? (
              <p className="text-xs text-slate-500">No Apparatus events have been returned yet.</p>
            ) : (
              <div className="space-y-3">
                {history.map((entry, index) => (
                  <div key={`${entry.id || entry.path || 'entry'}-${index}`} className="rounded-lg border border-slate-200 bg-white p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-xs font-bold text-slate-900">
                        {entry.method || 'REQUEST'} {entry.path || '/'}
                      </div>
                      <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                        {entry.statusCode || 'N/A'}
                      </div>
                    </div>
                    <div className="mt-1 text-[11px] text-slate-500">
                      {formatTimestamp(entry.timestamp)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
