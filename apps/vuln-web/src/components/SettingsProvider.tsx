import { API_BASE_URL } from '../lib/config';
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export interface SecurityConfig {
  sqli_protection: boolean;
  csrf_protection: boolean;
  ssrf_protection: boolean;
  xss_protection: boolean;
  bola_protection: boolean;
  debug_mode: boolean;
}

interface SettingsContextType {
  showHints: boolean;
  setShowHints: (value: boolean) => void;
  toggleHints: () => void;
  securityConfig: SecurityConfig;
  setSecurityConfig: (config: Partial<SecurityConfig>) => Promise<void>;
  refreshSecurityConfig: () => Promise<void>;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [showHints, setShowHints] = useState(() => {
    const saved = localStorage.getItem('chimera-show-hints');
    return saved ? JSON.parse(saved) : false;
  });

  const [securityConfig, setInternalSecurityConfig] = useState<SecurityConfig>({
    sqli_protection: false,
    csrf_protection: false,
    ssrf_protection: false,
    xss_protection: false,
    bola_protection: false,
    debug_mode: true
  });

  const refreshSecurityConfig = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/admin/security-config`);
      if (res.ok) {
        const data = await res.json();
        setInternalSecurityConfig(data);
      }
    } catch (err) {
      console.error('Failed to fetch security config:', err);
    }
  }, [API_BASE_URL]);

  const setSecurityConfig = async (newConfig: Partial<SecurityConfig>) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/admin/security-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      if (res.ok) {
        const data = await res.json();
        setInternalSecurityConfig(data.config);
      }
    } catch (err) {
      console.error('Failed to update security config:', err);
    }
  };

  useEffect(() => {
    localStorage.setItem('chimera-show-hints', JSON.stringify(showHints));
  }, [showHints]);

  useEffect(() => {
    refreshSecurityConfig();
  }, [refreshSecurityConfig]);

  const toggleHints = () => setShowHints((prev: boolean) => !prev);

  return (
    <SettingsContext.Provider value={{ 
      showHints, 
      setShowHints, 
      toggleHints, 
      securityConfig, 
      setSecurityConfig, 
      refreshSecurityConfig 
    }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};
