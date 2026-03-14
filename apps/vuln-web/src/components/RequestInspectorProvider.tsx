import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import { CHIMERA_EVENTS } from '../lib/config';
import { AttackLog } from '../lib/objectives';

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

/**
 * Pure utility function for attack detection.
 * Extracted outside the component to avoid stale closure issues and ensure a stable contract.
 */
const detectAttacksHeuristic = (ex: interceptedExchange, origin: string): AttackLog | null => {
  let type = '';
  let confidence: 'high' | 'low' = 'low';
  const status: 'allowed' | 'blocked' = ex.status >= 400 ? 'blocked' : 'allowed';
  
  // Short-circuit body processing if requestBody is missing to avoid "undefined" searches
  let payload = typeof ex.requestBody === 'string' ? ex.requestBody : (ex.requestBody ? JSON.stringify(ex.requestBody) : '');
  if (payload) {
    try {
      payload = decodeURIComponent(payload);
    } catch {}
  }

  let url = ex.url;
  try {
    url = decodeURIComponent(url);
  } catch {}
  
  // Only check SSRF keywords inside parameters, not the origin
  const pathAndQuery = url.replace(origin, '').toLowerCase();

  // --- Heuristic Detection blocks with Precedence ---
  // P1-001 Fix (Review 6): Use if/else if to ensure highest confidence match wins.

  // 1. SQL Injection Detection (High Confidence)
  const sqlKeywords = ["' or", "union select", "--", "drop table", "select * from"];
  if (pathAndQuery.includes('?') && sqlKeywords.some(k => pathAndQuery.split('?')[1].includes(k))) {
    type = 'SQL Injection';
    confidence = 'high';
  } else if (payload && sqlKeywords.some(k => payload.toLowerCase().includes(k))) {
    type = 'SQL Injection';
    confidence = 'high';
  }

  // 2. SSRF Detection (High Confidence for URL params)
  if (!type && pathAndQuery.includes('url=') && ["169.254.169.254", "localhost", "127.0.0.1", "metadata"].some(k => pathAndQuery.includes(k))) {
    type = 'SSRF';
    confidence = 'high';
  } 

  // 3. Broken Logic (High Confidence for specific payload patterns)
  if (!type && pathAndQuery.includes('transfer') && payload && (payload.includes('"-') || payload.includes(':-'))) {
    type = 'Broken Logic';
    confidence = 'high';
  }

  // 4. SSRF Detection (Low Confidence for general body content)
  if (!type && payload && ["169.254.169.254", "localhost", "127.0.0.1", "metadata"].some(k => payload.toLowerCase().includes(k))) {
    type = 'SSRF';
    confidence = 'low';
  }

  // 5. IDOR / BOLA Detection (Low Confidence heuristic)
  const idorPatterns = ["/records/", "/policies/", "/subscribers/", "/tenants/", "/outages/"];
  if (!type && idorPatterns.some(p => pathAndQuery.includes(p)) && !pathAndQuery.endsWith('search')) {
    type = 'BOLA';
    confidence = 'low'; 
  }

  // --- Server-Confirmed Detection (Override Priority) ---
  
  if (ex.responseHeaders['x-chimera-vulnerable']) {
    // P2-001 Fix (Review 6): Replace all hyphens for better display
    type = ex.responseHeaders['x-chimera-vulnerable'].replaceAll('-', ' ');
    confidence = 'high';
  }

  if (ex.responseBody && typeof ex.responseBody === 'object' && ex.responseBody.vulnerability) {
    type = ex.responseBody.vulnerability_type || type || 'Vulnerability Detected';
    confidence = 'high';
  }

  if (type) {
    return {
      id: ex.id,
      timestamp: ex.timestamp,
      method: ex.method,
      path: pathAndQuery,
      payload: payload || url,
      type: type,
      status: status,
      source_ip: '127.0.0.1',
      origin_defense: ex.responseHeaders['x-chimera-defense'] || (ex.responseBody?.origin_defense),
      confidence
    } as AttackLog;
  }

  return null;
};

export const RequestInspectorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [exchanges, setExchanges] = useState<interceptedExchange[]>([]);
  const [lastExchange, setLastExchange] = useState<interceptedExchange | null>(null);
  const originalFetchRef = useRef<typeof fetch | null>(null);

  const inspectExchange = useCallback((exchange: interceptedExchange) => {
    setExchanges(prev => [exchange, ...prev].slice(0, 20));
    setLastExchange(exchange);
    
    // Detection
    const attackLog = detectAttacksHeuristic(exchange, window.location.origin);
    if (attackLog) {
      window.dispatchEvent(new CustomEvent(CHIMERA_EVENTS.ATTACK_LOG, { detail: attackLog }));
    }
  }, []);

  const clearExchanges = useCallback(() => {
    setExchanges([]);
    setLastExchange(null);
  }, []);

  // Intercept global fetch
  useEffect(() => {
    // Assumes this provider is the sole fetch interceptor; re-entrant patching is not supported.
    if (!originalFetchRef.current) {
      originalFetchRef.current = window.fetch;
    }

    const originalFetch = originalFetchRef.current;

    /**
     * Patched fetch that captures traffic metadata.
     * Always uses originalFetchRef.current to ensure we don't wrap a wrapper if the effect re-runs.
     */
    const patchedFetch = async (...args: Parameters<typeof fetch>): Promise<Response> => {
      const startTime = performance.now();
      const [resource, config] = args;
      const url = typeof resource === 'string' ? resource : (resource as Request).url;
      
      // Filter internal traffic
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
        
        // Always read as text first to avoid "stream already read" TypeError on fallback
        let responseBody = null;
        const textBody = await clone.text();
        const contentType = clone.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
          try {
            responseBody = textBody ? JSON.parse(textBody) : null;
          } catch {
            responseBody = textBody;
          }
        } else {
          responseBody = textBody;
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
      } catch (error: any) {
        // Capture network errors in the inspector
        const failedExchange: interceptedExchange = {
          id: Math.random().toString(36).substring(2, 9),
          timestamp: new Date().toLocaleTimeString(),
          method,
          url,
          requestHeaders: (config?.headers as Record<string, string>) || {},
          requestBody,
          status: 0,
          responseHeaders: {},
          responseBody: { error: error.message || 'Network Error' },
          duration: Math.round(performance.now() - startTime),
        };
        inspectExchange(failedExchange);
        return Promise.reject(error);
      }
    };

    window.fetch = patchedFetch;

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
