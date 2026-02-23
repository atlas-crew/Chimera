import { useEffect, useRef } from 'react';
import { AttackLog, ATTACK_LOG_EVENT } from '../lib/objectives';

export const useAttackLog = (callback: (log: AttackLog) => void) => {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    const handleEvent = (e: Event) => {
      const customEvent = e as CustomEvent<AttackLog>;
      callbackRef.current(customEvent.detail);
    };

    window.addEventListener(ATTACK_LOG_EVENT, handleEvent);
    return () => window.removeEventListener(ATTACK_LOG_EVENT, handleEvent);
  }, []);
};
