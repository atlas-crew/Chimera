import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { useAttackLog } from './useAttackLog';
import { ATTACK_LOG_EVENT, AttackLog } from '../lib/objectives';

describe('useAttackLog', () => {
  it('calls the callback when a chimera:attack-log event is dispatched', () => {
    const callback = vi.fn();
    renderHook(() => useAttackLog(callback));

    const mockLog: AttackLog = {
      id: '123',
      timestamp: '12:00:00',
      method: 'POST',
      path: '/api/v1/test',
      payload: 'test payload',
      type: 'SQLi',
      status: 'allowed',
      source_ip: '127.0.0.1'
    };

    const event = new CustomEvent(ATTACK_LOG_EVENT, { detail: mockLog });
    
    act(() => {
      window.dispatchEvent(event);
    });

    expect(callback).toHaveBeenCalledWith(mockLog);
  });

  it('unregisters the listener on unmount', () => {
    const callback = vi.fn();
    const { unmount } = renderHook(() => useAttackLog(callback));

    unmount();

    const event = new CustomEvent(ATTACK_LOG_EVENT, { detail: {} });
    act(() => {
      window.dispatchEvent(event);
    });

    expect(callback).not.toHaveBeenCalled();
  });
});
