import React, { createContext, useContext, useState, useEffect } from 'react';

interface SettingsContextType {
  showHints: boolean;
  toggleHints: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [showHints, setShowHints] = useState(() => {
    const saved = localStorage.getItem('chimera-show-hints');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('chimera-show-hints', JSON.stringify(showHints));
  }, [showHints]);

  const toggleHints = () => setShowHints((prev: boolean) => !prev);

  return (
    <SettingsContext.Provider value={{ showHints, toggleHints }}>
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
