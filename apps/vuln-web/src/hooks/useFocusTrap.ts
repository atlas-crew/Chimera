import { useEffect, useRef, RefObject } from 'react';

export const useFocusTrap = (
  isOpen: boolean, 
  onClose: () => void, 
  active: boolean = true
): RefObject<HTMLDivElement | null> => {
  const containerRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!isOpen) return;
    
    // Only capture focus if we are active
    if (active) {
      previouslyFocusedRef.current = document.activeElement as HTMLElement;
      // Focus the container
      containerRef.current?.focus();
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      // If this trap is currently inactive (e.g. background modal), ignore
      if (!active) return;

      if (e.key === 'Escape') {
        e.stopPropagation();
        onCloseRef.current();
      }

      if (e.key === 'Tab' && containerRef.current) {
        const focusableElements = containerRef.current.querySelectorAll<HTMLElement>(
          'button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) {
          e.preventDefault();
          return;
        }

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown, true);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown, true);
      // Restore focus if we were the active one
      if (active && previouslyFocusedRef.current) {
        previouslyFocusedRef.current.focus();
      }
    };
  }, [isOpen, active]); // removed onClose from deps

  return containerRef;
};
