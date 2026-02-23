import { render, fireEvent, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import React from 'react';
import { useFocusTrap } from './useFocusTrap';

const TestComponent: React.FC<{ isOpen: boolean; onClose: () => void; active?: boolean }> = ({ isOpen, onClose, active }) => {
  const containerRef = useFocusTrap(isOpen, onClose, active);
  return (
    <div ref={containerRef} tabIndex={-1} role="dialog">
      <button id="first">First</button>
      <button id="second">Second</button>
      <button id="last">Last</button>
    </div>
  );
};

describe('useFocusTrap', () => {
  const onClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  it('focuses the container on mount when open and active', () => {
    const { getByRole } = render(<TestComponent isOpen={true} onClose={onClose} />);
    const dialog = getByRole('dialog');
    expect(document.activeElement).toBe(dialog);
  });

  it('restores focus on unmount', () => {
    const trigger = document.createElement('button');
    document.body.appendChild(trigger);
    trigger.focus();
    expect(document.activeElement).toBe(trigger);

    const { unmount } = render(<TestComponent isOpen={true} onClose={onClose} />);
    expect(document.activeElement).not.toBe(trigger);

    unmount();
    expect(document.activeElement).toBe(trigger);
  });

  it('calls onClose when Escape is pressed', () => {
    render(<TestComponent isOpen={true} onClose={onClose} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('traps focus with Tab', () => {
    const { getByText } = render(<TestComponent isOpen={true} onClose={onClose} />);
    const first = getByText('First');
    const last = getByText('Last');

    act(() => { last.focus(); });
    expect(document.activeElement).toBe(last);

    fireEvent.keyDown(last, { key: 'Tab', shiftKey: false });
    expect(document.activeElement).toBe(first);
  });

  it('traps focus with Shift+Tab', () => {
    const { getByText } = render(<TestComponent isOpen={true} onClose={onClose} />);
    const first = getByText('First');
    const last = getByText('Last');

    act(() => { first.focus(); });
    expect(document.activeElement).toBe(first);

    fireEvent.keyDown(first, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(last);
  });

  it('ignores events when not active (stacked modal case)', () => {
    render(<TestComponent isOpen={true} onClose={onClose} active={false} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).not.toHaveBeenCalled();
  });
});
