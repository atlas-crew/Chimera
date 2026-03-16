import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApparatusPanel } from './ApparatusPanel';

vi.mock('../features/apparatus/api', () => ({
  getApparatusStatus: vi.fn(),
  getApparatusHistory: vi.fn(),
  startApparatusGhosts: vi.fn(),
  stopApparatusGhosts: vi.fn(),
}));

import {
  getApparatusHistory,
  getApparatusStatus,
  startApparatusGhosts,
  stopApparatusGhosts,
} from '../features/apparatus/api';

const mockedStatus = vi.mocked(getApparatusStatus);
const mockedHistory = vi.mocked(getApparatusHistory);
const mockedStart = vi.mocked(startApparatusGhosts);
const mockedStop = vi.mocked(stopApparatusGhosts);

describe('ApparatusPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockedStatus.mockResolvedValue({
      enabled: true,
      configured: true,
      reachable: true,
      baseUrl: 'http://apparatus.local',
      health: { status: 'ok' },
      ghosts: { running: false },
    });
    mockedHistory.mockResolvedValue({
      count: 1,
      entries: [{
        id: 'evt-1',
        method: 'GET',
        path: '/history',
        statusCode: 200,
        timestamp: '2026-03-15T20:00:00Z',
      }],
    });
    mockedStart.mockResolvedValue({ running: true });
    mockedStop.mockResolvedValue({ running: false });
  });

  it('renders connected state and recent history', async () => {
    render(<ApparatusPanel />);

    expect(await screen.findByText(/Connected/i)).toBeInTheDocument();
    expect(screen.getByText('http://apparatus.local')).toBeInTheDocument();
    expect(screen.getByText(/GET \/history/i)).toBeInTheDocument();
  });

  it('renders disabled state from status payload', async () => {
    mockedStatus.mockResolvedValueOnce({
      enabled: false,
      configured: true,
      reachable: false,
      baseUrl: 'http://apparatus.local',
      health: null,
      ghosts: null,
      error: 'apparatus_disabled',
      message: 'Apparatus integration is disabled.',
    });
    mockedHistory.mockResolvedValueOnce({ count: 0, entries: [] });

    render(<ApparatusPanel />);

    expect(await screen.findByText(/^Disabled$/i)).toBeInTheDocument();
    expect(screen.getByText(/Apparatus integration is disabled\./i)).toBeInTheDocument();
  });

  it('renders unreachable error when status load fails', async () => {
    mockedStatus.mockRejectedValueOnce(new Error('network down'));
    mockedHistory.mockResolvedValueOnce({ count: 0, entries: [] });

    render(<ApparatusPanel />);

    expect(await screen.findByText(/network down/i)).toBeInTheDocument();
  });

  it('starts ghost traffic with current form values', async () => {
    render(<ApparatusPanel />);
    await screen.findByText(/Connected/i);

    fireEvent.change(screen.getByLabelText(/RPS/i), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText(/Duration \(ms\)/i), { target: { value: '45000' } });
    fireEvent.click(screen.getByRole('button', { name: /Start Ghosts/i }));

    await waitFor(() => {
      expect(mockedStart).toHaveBeenCalledWith({ rps: 8, duration: 45000 });
    });
  });

  it('stops ghost traffic from the control panel', async () => {
    render(<ApparatusPanel />);
    await screen.findByText(/Connected/i);

    fireEvent.click(screen.getByRole('button', { name: /Stop Ghosts/i }));

    await waitFor(() => {
      expect(mockedStop).toHaveBeenCalled();
    });
  });
});
