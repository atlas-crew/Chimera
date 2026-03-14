import { API_BASE_URL } from '../lib/config';
import React, { createContext, useContext, useState, useEffect, useCallback, useRef, useMemo } from 'react';

interface ConnectivityContextType {
  isOnline: boolean | null; // null means unknown
  lastChecked: Date | null;
  latency: number | null;
  isPinging: boolean;
  checkConnectivity: () => Promise<void>;
  autoPing: boolean;
  setAutoPing: (value: boolean) => void;
  pingInterval: number;
  setPingInterval: (value: number) => void;
}

const ConnectivityContext = createContext<ConnectivityContextType | undefined>(undefined);

export const ConnectivityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [isPinging, setIsPinging] = useState(false);
  
  const [autoPing, setAutoPing] = useState(() => {
    try {
      const saved = localStorage.getItem('chimera-auto-ping');
      return saved ? JSON.parse(saved) === true : true;
    } catch {
      return true;
    }
  });
  
  const [pingInterval, setPingInterval] = useState(() => {
    try {
      const saved = localStorage.getItem('chimera-ping-interval');
      return Math.max(5000, Number(saved) || 30000); // Default 30s, minimum 5s
    } catch {
      return 30000;
    }
  });

  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    localStorage.setItem('chimera-auto-ping', JSON.stringify(autoPing));
    localStorage.setItem('chimera-ping-interval', JSON.stringify(pingInterval));
  }, [autoPing, pingInterval]);

  const checkConnectivity = useCallback(async () => {
    setIsPinging(true);
    const start = performance.now();
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/healthz`, { 
        cache: 'no-store',
        signal: AbortSignal.timeout(5000) 
      });
      const end = performance.now();
      
      if (response.ok) {
        setIsOnline(prev => prev !== true ? true : prev);
        setLatency(Math.round(end - start));
      } else {
        setIsOnline(false);
        setLatency(null);
      }
    } catch (err) {
      console.error('Connectivity check failed:', err);
      setIsOnline(false);
      setLatency(null);
    } finally {
      setIsPinging(false);
      setLastChecked(new Date());
    }
  }, [API_BASE_URL]);

  // Initial check on mount
  useEffect(() => {
    checkConnectivity();
  }, [checkConnectivity]);

  useEffect(() => {
    if (autoPing) {
      timerRef.current = window.setInterval(checkConnectivity, pingInterval);
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [autoPing, pingInterval, checkConnectivity]);

  const contextValue = useMemo(() => ({
    isOnline, 
    lastChecked, 
    latency, 
    isPinging, 
    checkConnectivity,
    autoPing,
    setAutoPing,
    pingInterval,
    setPingInterval
  }), [isOnline, lastChecked, latency, isPinging, checkConnectivity, autoPing, pingInterval]);

  return (
    <ConnectivityContext.Provider value={contextValue}>
      {children}
    </ConnectivityContext.Provider>
  );
};

export const useConnectivity = () => {
  const context = useContext(ConnectivityContext);
  if (context === undefined) {
    throw new Error('useConnectivity must be used within a ConnectivityProvider');
  }
  return context;
};

