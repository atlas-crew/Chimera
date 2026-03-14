import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  ArrowLeft,
  ChevronDown,
  HelpCircle,
  Moon,
  PlayCircle,
  Radar,
  Scan,
  Shield,
  Sun,
  Target,
  Terminal,
} from 'lucide-react';
import ChimeraIcon from '/chimera-icon.svg';
import { AiAssistant } from './AiAssistant';
import { RedTeamConsole } from './RedTeamConsole';
import { XRayInspector } from './XRayInspector';
import { WafVisualizer } from './WafVisualizer';
import { KillChainTracker } from './KillChainTracker';
import { useTheme } from './ThemeProvider';
import { useSettings } from './SettingsProvider';
import { TourGuide } from './TourGuide';
import { ConnectivityStatus } from './ConnectivityStatus';
import { KILL_CHAIN_OBJECTIVES } from '../lib/objectives';
import { CHIMERA_EVENTS } from '../lib/config';

const MAIN_ACCENT_COLOR = '#ee4db9';
const KILL_CHAIN_STORAGE_KEY = 'chimera-kill-chain';

const PORTAL_MAP: Record<string, { name: string, accent: string; headerGradient: string }> = {
  '/healthcare': { name: 'MediPortal Online', accent: '#34d399', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #14532d 100%)' },
  '/banking': { name: 'SecureBank Pro', accent: '#60a5fa', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%)' },
  '/ecommerce': { name: 'ShopRight Retail', accent: '#fb923c', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #c2410c 100%)' },
  '/saas': { name: 'Nexus SaaS', accent: '#818cf8', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #4338ca 100%)' },
  '/government': { name: 'GovPortal Services', accent: '#cbd5e1', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #334155 100%)' },
  '/telecom': { name: 'TelcoConnect', accent: '#c084fc', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #6d28d9 100%)' },
  '/energy': { name: 'GridMatrix Utilities', accent: '#facc15', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #a16207 100%)' },
  '/ics-ot': { name: 'Industrial Command', accent: '#93c5fd', headerGradient: 'linear-gradient(135deg, #020617 0%, #1e3a8a 100%)' },
  '/insurance': { name: 'ProtectFlow Insurance', accent: '#93c5fd', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%)' },
  '/loyalty': { name: 'EliteRewards', accent: '#c4b5fd', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #7c3aed 100%)' },
  '/admin': { name: 'Core Admin Console', accent: '#f87171', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #991b1b 100%)' },
  '/ai-lab': { name: 'AI Research Lab', accent: '#f9a8d4', headerGradient: 'linear-gradient(135deg, #0f172a 0%, #a21caf 100%)' },
};

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const isHome = location.pathname === '/';
  const { theme, toggleTheme } = useTheme();
  const { showHints, setShowHints, toggleHints } = useSettings();
  const currentPortal = PORTAL_MAP[location.pathname] || null;
  const apiDocsHref = import.meta.env.DEV
    ? `${window.location.protocol}//${window.location.hostname}:8880/swagger`
    : '/swagger';
  const [showToolsMenu, setShowToolsMenu] = useState(false);
  const [completedObjectives, setCompletedObjectives] = useState(0);
  const toolsMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const syncKillChainProgress = (completedCount?: number) => {
      if (typeof completedCount === 'number') {
        setCompletedObjectives(completedCount);
        return;
      }

      const saved = localStorage.getItem(KILL_CHAIN_STORAGE_KEY);

      if (!saved) {
        setCompletedObjectives(0);
        return;
      }

      try {
        const parsed = JSON.parse(saved);
        setCompletedObjectives(Array.isArray(parsed) ? parsed.length : 0);
      } catch {
        setCompletedObjectives(0);
      }
    };

    const handleStorage = (event: StorageEvent) => {
      if (event.key === KILL_CHAIN_STORAGE_KEY) {
        syncKillChainProgress();
      }
    };

    const handleKillChainProgress = (event: Event) => {
      const customEvent = event as CustomEvent<{ completed?: number }>;
      syncKillChainProgress(customEvent.detail?.completed);
    };

    const handlePointerDown = (event: MouseEvent) => {
      if (toolsMenuRef.current && !toolsMenuRef.current.contains(event.target as Node)) {
        setShowToolsMenu(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowToolsMenu(false);
      }
    };

    syncKillChainProgress();
    window.addEventListener('storage', handleStorage);
    window.addEventListener(CHIMERA_EVENTS.KILL_CHAIN_PROGRESS, handleKillChainProgress as EventListener);
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleEscape);

    return () => {
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener(CHIMERA_EVENTS.KILL_CHAIN_PROGRESS, handleKillChainProgress as EventListener);
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const dispatchToolToggle = (eventName: string) => {
    window.dispatchEvent(new CustomEvent(eventName));
    setShowToolsMenu(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col transition-colors duration-200">
      <RedTeamConsole showLauncher={false} />
      <XRayInspector showLauncher={false} />
      <WafVisualizer showLauncher={false} />
      <KillChainTracker showLauncher={false} />
      <TourGuide />

      <header
        className="relative text-white shadow-lg sticky top-0 z-50 border-b-4 transition-colors border-b-slate-800 dark:border-b-slate-900 after:pointer-events-none after:absolute after:inset-x-0 after:bottom-0 after:h-px after:bg-white/10"
        style={{
          backgroundColor: '#0f172a',
          backgroundImage: currentPortal?.headerGradient,
          borderBottomColor: currentPortal?.accent ?? undefined,
        }}
      >
        <div className="container mx-auto px-4 py-3 flex flex-wrap lg:flex-nowrap items-center justify-between gap-3">
          <div className="flex min-w-0 flex-wrap lg:flex-nowrap items-center gap-2 md:gap-3">
            <Link to="/" className="flex items-center gap-2 group shrink-0">
              <img src={ChimeraIcon} alt="Chimera" className="w-12 h-12 shrink-0" />
              <span className="hidden md:flex items-baseline gap-1.5 leading-none text-white">
                <span className="font-bold text-lg tracking-tight">Chimera</span>
                <span className="font-medium text-sm italic" style={{ color: MAIN_ACCENT_COLOR }}>Portals</span>
              </span>
            </Link>

            {!isHome && (
              <div className="hidden sm:flex items-center gap-3 min-w-0">
                <div className="h-6 w-px bg-slate-700" />
                <Link to="/" className="flex items-center gap-1 text-xs font-bold text-slate-400 hover:text-white transition-colors uppercase tracking-widest shrink-0">
                  <ArrowLeft className="w-3 h-3" />
                  Directory
                </Link>
              </div>
            )}

            {currentPortal && (
              <span className="max-w-[13rem] md:max-w-[16rem] truncate rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold text-slate-100">
                {currentPortal.name}
              </span>
            )}
          </div>

          <div className="flex flex-wrap lg:flex-nowrap items-center justify-end gap-2">
            <div className="mr-3 pr-4 border-r border-white/10">
              <ConnectivityStatus />
            </div>
            <button
              onClick={toggleHints}
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold transition-all ${showHints ? 'bg-yellow-500 text-slate-950 ring-4 ring-yellow-500/20' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'}`}
              title={showHints ? 'Hide Exploit Hints' : 'Show Exploit Hints'}
              aria-pressed={showHints}
              aria-label={showHints ? 'Hide Exploit Hints' : 'Show Exploit Hints'}
            >
              <HelpCircle className="w-3.5 h-3.5" />
              {showHints ? 'Hints: ON' : 'Hints: OFF'}
            </button>
            <button
              onClick={() => {
                setShowHints(true);
                if ((window as { startTour?: () => void }).startTour) {
                  (window as { startTour?: () => void }).startTour?.();
                }
              }}
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-full text-xs font-bold transition-colors"
              aria-label="Start Exploit Tour"
            >
              <PlayCircle className="w-3.5 h-3.5" />
              <span>Exploit Tour</span>
            </button>

            <div className="relative" ref={toolsMenuRef}>
              <button
                onClick={() => setShowToolsMenu((prev) => !prev)}
                className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-bold text-slate-200 transition-colors hover:bg-slate-700"
                aria-expanded={showToolsMenu}
                aria-label="Open Lab Tools Menu"
              >
                <Radar className="h-3.5 w-3.5 text-cyan-300" />
                <span>Tools</span>
                <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showToolsMenu ? 'rotate-180' : ''}`} />
              </button>

              {showToolsMenu && (
                <div className="absolute right-0 mt-2 w-72 overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl z-[70] animate-in fade-in zoom-in-95 duration-200">
                  <div className="border-b border-slate-800 bg-slate-950/70 px-4 py-3">
                    <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-slate-500">Header Utilities</p>
                    <p className="mt-1 text-sm font-semibold text-white">Launch the operator tooling from here.</p>
                  </div>
                  <div className="p-2">
                    <button
                      onClick={() => dispatchToolToggle(CHIMERA_EVENTS.TOGGLE_RED_TEAM_CONSOLE)}
                      className="flex w-full items-start gap-3 rounded-xl px-3 py-2 text-left text-slate-200 transition-colors hover:bg-slate-800"
                    >
                      <Terminal className="mt-0.5 h-4 w-4 text-red-400" />
                      <span>
                        <span className="block text-xs font-bold uppercase tracking-wider">Red Team Console</span>
                        <span className="block text-[11px] text-slate-400">Live attack traffic feed and operator telemetry.</span>
                      </span>
                    </button>
                    <button
                      onClick={() => dispatchToolToggle(CHIMERA_EVENTS.TOGGLE_XRAY_INSPECTOR)}
                      className="flex w-full items-start gap-3 rounded-xl px-3 py-2 text-left text-slate-200 transition-colors hover:bg-slate-800"
                    >
                      <Scan className="mt-0.5 h-4 w-4 text-emerald-400" />
                      <span>
                        <span className="block text-xs font-bold uppercase tracking-wider">X-Ray Inspector</span>
                        <span className="block text-[11px] text-slate-400">Inspect captured request and response payloads.</span>
                      </span>
                    </button>
                    <button
                      onClick={() => dispatchToolToggle(CHIMERA_EVENTS.TOGGLE_WAF_VISUALIZER)}
                      className="flex w-full items-start gap-3 rounded-xl px-3 py-2 text-left text-slate-200 transition-colors hover:bg-slate-800"
                    >
                      <Shield className="mt-0.5 h-4 w-4 text-blue-400" />
                      <span>
                        <span className="block text-xs font-bold uppercase tracking-wider">WAF Visualizer</span>
                        <span className="block text-[11px] text-slate-400">Trace how requests move through the defense pipeline.</span>
                      </span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() => dispatchToolToggle(CHIMERA_EVENTS.TOGGLE_KILL_CHAIN)}
              className="inline-flex items-center gap-2 rounded-full border border-red-400/30 bg-red-500/10 px-3 py-1.5 text-xs font-bold text-red-100 transition-colors hover:bg-red-500/20"
              aria-label="Open Kill Chain Status"
            >
              <Target className="h-3.5 w-3.5 text-red-300" />
              <span className="rounded-full bg-red-500/20 px-2 py-0.5 font-mono text-[10px] text-red-200">
                {completedObjectives}/{KILL_CHAIN_OBJECTIVES.length}
              </span>
            </button>
            <button
              onClick={toggleTheme}
              className="p-2 text-slate-400 hover:text-white transition-colors rounded-full hover:bg-slate-800 shrink-0"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              aria-label={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      <main className="portal-theme flex-grow dark:text-slate-200">
        {children}
      </main>

      <AiAssistant />

      <footer className="bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 py-8 transition-colors duration-200">
        <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-slate-500 dark:text-slate-400 text-sm">
            &copy; 2026 Nicholas Crew Ferguson. Intentionally vulnerable for testing purposes.
          </div>
          <div className="flex gap-6 text-sm font-medium text-slate-400 dark:text-slate-500">
            <span className="hidden lg:inline text-slate-600 dark:text-slate-400 opacity-50 font-mono text-xs pt-0.5 "><em>Powered by Chimera API</em></span>
            <a href={apiDocsHref} className="hover:text-slate-600 dark:hover:text-slate-300">API Docs</a>
            <a href="https://github.com/NickCrew/Chimera/Issues" className="hover:text-slate-600 dark:hover:text-slate-300">Issues</a>
            <a href="https://github.com/NickCrew/Chimera" className="hover:text-slate-600 dark:hover:text-slate-300">Github</a>
            <a href="https://github.com/NickCrew/apparatus" className="hover:text-slate-600 dark:hover:text-slate-300">Apparatus</a>
          </div>
        </div>
      </footer>
    </div>
  );
};
