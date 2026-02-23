import React, { createContext, useContext, useState, useCallback } from 'react';

export interface interceptedExchange {
  id: string;
  timestamp: string;
  method: string;
  url: string;
  requestHeaders: Record<string, string>;
  requestBody: any;
  status: number;
  responseHeaders: Record<string, string>;
  responseBody: any;
  duration: number;
}

interface RequestInspectorContextType {
  lastExchange: interceptedExchange | null;
  exchanges: interceptedExchange[];
  inspectExchange: (exchange: interceptedExchange) => void;
  clearExchanges: () => void;
}

const RequestInspectorContext = createContext<RequestInspectorContextType | undefined>(undefined);

export const RequestInspectorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [exchanges, setExchanges] = useState<interceptedExchange[]>([]);
  const [lastExchange, setLastExchange] = useState<interceptedExchange | null>(null);

  const inspectExchange = useCallback((exchange: interceptedExchange) => {
    setExchanges(prev => [exchange, ...prev].slice(0, 20));
    setLastExchange(exchange);
  }, []);

  const clearExchanges = useCallback(() => {
    setExchanges([]);
    setLastExchange(null);
  }, []);

  // Intercept global fetch
  React.useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = performance.now();
      const [resource, config] = args;
      const url = typeof resource === 'string' ? resource : (resource as Request).url;
      
      // Don't intercept internal Vite HMR or analytics if any
      if (url.includes('hmr') || url.includes('chrome-extension')) {
        return originalFetch(...args);
      }

      const method = (config?.method || 'GET').toUpperCase();
      let requestBody = null;
      try {
        if (config?.body) {
          requestBody = JSON.parse(config.body as string);
        }
      } catch (e) {
        requestBody = config?.body;
      }

      try {
        const response = await originalFetch(...args);
        const clone = response.clone();
        const duration = Math.round(performance.now() - startTime);
        
        let responseBody = null;
        const contentType = clone.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          responseBody = await clone.json();
        } else {
          responseBody = await clone.text();
        }

        const exchange: interceptedExchange = {
          id: Math.random().toString(36).substring(2, 9),
          timestamp: new Date().toLocaleTimeString(),
          method,
          url,
          requestHeaders: (config?.headers as Record<string, string>) || {},
          requestBody,
          status: response.status,
          responseHeaders: Object.fromEntries(clone.headers.entries()),
          responseBody,
          duration,
        };

        inspectExchange(exchange);
        return response;
      } catch (error) {
        // Log failed requests too
        return Promise.reject(error);
      }
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, [inspectExchange]);

  return (
    <RequestInspectorContext.Provider value={{ lastExchange, exchanges, inspectExchange, clearExchanges }}>
      {children}
    </RequestInspectorContext.Provider>
  );
};

export const useRequestInspector = () => {
  const context = useContext(RequestInspectorContext);
  if (context === undefined) {
    throw new Error('useRequestInspector must be used within a RequestInspectorProvider');
  }
  return context;
};
