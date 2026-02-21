import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Menu, User, Sun, Moon, PlayCircle } from 'lucide-react';
import { AiAssistant } from './AiAssistant';
import { RedTeamConsole } from './RedTeamConsole';
import { useTheme } from './ThemeProvider';
import { TourGuide } from './TourGuide';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const isHome = location.pathname === '/';
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col transition-colors duration-200">
      <RedTeamConsole />
      <TourGuide />
      
      <header className="bg-slate-900 dark:bg-slate-950 text-white shadow-lg sticky top-0 z-50 border-b border-slate-800 dark:border-slate-900">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="bg-blue-600 p-1.5 rounded-lg group-hover:bg-blue-500 transition-colors">
              <Shield className="w-6 h-6" />
            </div>
            <span className="font-bold text-xl tracking-tight">EdgeResilience <span className="text-blue-400 font-medium text-lg italic">Portals</span></span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link to="/" className={`text-sm font-medium transition-colors ${isHome ? 'text-blue-400' : 'text-slate-300 hover:text-white'}`}>Directory</Link>
            {!isHome && (
              <div className="h-4 w-px bg-slate-700 mx-2" />
            )}
            {!isHome && location.pathname.includes('healthcare') && (
              <span className="text-sm font-semibold text-blue-400">MediPortal Online</span>
            )}
          </nav>

          <div className="flex items-center gap-4">
            <button
              onClick={() => (window as any).startTour && (window as any).startTour()}
              className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-full text-xs font-bold transition-colors animate-pulse"
            >
              <PlayCircle className="w-3.5 h-3.5" />
              Start Exploit Tour
            </button>
            <button 
              onClick={toggleTheme}
              className="p-2 text-slate-400 hover:text-white transition-colors rounded-full hover:bg-slate-800"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <button className="p-2 text-slate-400 hover:text-white transition-colors">
              <User className="w-5 h-5" />
            </button>
            <button className="md:hidden p-2 text-slate-400 hover:text-white transition-colors">
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="flex-grow dark:text-slate-200">
        {children}
      </main>

      <AiAssistant />

      <footer className="bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 py-8 transition-colors duration-200">
        <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-slate-500 dark:text-slate-400 text-sm">
            &copy; 2025 Edge Resilience Lab. Intentionally vulnerable for testing purposes.
          </div>
          <div className="flex gap-6 text-sm font-medium text-slate-400 dark:text-slate-500">
            <span className="hidden lg:inline text-slate-600 dark:text-slate-400 opacity-50 font-mono text-xs pt-0.5 red-team-console-hint">Console: Ctrl + ~</span>
            <a href="#" className="hover:text-slate-600 dark:hover:text-slate-300">Privacy Policy</a>
            <a href="#" className="hover:text-slate-600 dark:hover:text-slate-300">Terms of Service</a>
            <a href="#" className="hover:text-slate-600 dark:hover:text-slate-300">Security</a>
          </div>
        </div>
      </footer>
    </div>
  );
};
