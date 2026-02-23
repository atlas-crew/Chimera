import { render, screen, fireEvent, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { CodeRemediationModal } from './CodeRemediationModal';

describe('CodeRemediationModal', () => {
  const defaultProps = {
    onClose: vi.fn(),
    vulnName: 'SQL Injection',
    example: {
      vulnerable: 'SELECT * FROM users WHERE id = ' + "'1'",
      secure: 'SELECT * FROM users WHERE id = ?',
      language: 'sql'
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    
    // Mock navigator.clipboard
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('renders the vulnerability name in the modal title', () => {
    render(<CodeRemediationModal {...defaultProps} />);
    expect(screen.getByText(/Remediation Guide: SQL Injection/i)).toBeInTheDocument();
  });

  it('renders correctly with special characters and multiline strings', () => {
    const specialProps = {
      ...defaultProps,
      vulnName: 'XSS & Injection',
      example: {
        vulnerable: '<script>\n  alert("XSS");\n</script>',
        secure: 'const sanitized = DOMPurify.sanitize(input);',
        language: 'javascript'
      }
    };
    render(<CodeRemediationModal {...specialProps} />);
    expect(screen.getByText(/XSS & Injection/i)).toBeInTheDocument();
    
    const codeElements = screen.getAllByRole('code');
    const vulnerableCode = codeElements.find(el => el.textContent?.includes('<script>'));
    expect(vulnerableCode).toBeInTheDocument();
    expect(vulnerableCode?.textContent).toContain('alert("XSS")');
  });

  it('renders correctly with empty props', () => {
    render(<CodeRemediationModal {...defaultProps} vulnName="" />);
    expect(screen.getByText(/Remediation Guide:/i)).toBeInTheDocument();
  });

  it('renders section labels and footer note', () => {
    render(<CodeRemediationModal {...defaultProps} />);
    expect(screen.getByText(/Vulnerable Code/i)).toBeInTheDocument();
    expect(screen.getByText(/Secure Fix/i)).toBeInTheDocument();
    expect(screen.getByText(/for educational purposes/i)).toBeInTheDocument();
  });

  describe('dismissal', () => {
    it('calls onClose when the X button is clicked', () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const closeButton = screen.getByLabelText(/Close Remediation Guide/i);
      fireEvent.click(closeButton);
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose and stops propagation when the backdrop is clicked', () => {
      const parentSpy = vi.fn();
      render(
        <div onClick={parentSpy}>
          <CodeRemediationModal {...defaultProps} />
        </div>
      );
      const backdrop = screen.getByTestId('modal-backdrop');
      fireEvent.click(backdrop);
      
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
      expect(parentSpy).not.toHaveBeenCalled();
    });

    it('does not call onClose when the dialog content is clicked', () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const dialog = screen.getByRole('dialog');
      fireEvent.click(dialog);
      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });

    it('calls onClose when the Escape key is pressed', () => {
      render(<CodeRemediationModal {...defaultProps} />);
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('clipboard copy', () => {
    it('copies vulnerable code to clipboard when its copy button is clicked', async () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const copyButton = screen.getByLabelText(/Copy vulnerable code/i);
      await act(async () => {
        fireEvent.click(copyButton);
      });
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(defaultProps.example.vulnerable);
      expect(screen.getByText(/Vulnerable code copied to clipboard/i)).toBeInTheDocument();
    });

    it('copies secure code to clipboard when its copy button is clicked', async () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const copyButton = screen.getByLabelText(/Copy secure fix code/i);
      await act(async () => {
        fireEvent.click(copyButton);
      });
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(defaultProps.example.secure);
      expect(screen.getByText(/Secure fix copied to clipboard/i)).toBeInTheDocument();
    });

    it('clears live region announcement after timeout', async () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const copyButton = screen.getByLabelText(/Copy vulnerable code/i);
      
      await act(async () => {
        fireEvent.click(copyButton);
      });
      
      const liveRegion = screen.getByText(/Vulnerable code copied to clipboard/i);
      expect(liveRegion).toBeInTheDocument();
      
      act(() => {
        vi.advanceTimersByTime(2000);
      });
      
      expect(liveRegion.textContent).toBe('');
    });

    it('shows check icon after successful copy and reverts at exactly 2 seconds', async () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const copyButton = screen.getByLabelText(/Copy vulnerable code/i);
      
      await act(async () => {
        fireEvent.click(copyButton);
      });
      
      expect(copyButton).toHaveAttribute('data-copied', 'true');
      
      act(() => {
        vi.advanceTimersByTime(1999);
      });
      expect(copyButton).toHaveAttribute('data-copied', 'true');
      
      act(() => {
        vi.advanceTimersByTime(1);
      });
      
      expect(copyButton).toHaveAttribute('data-copied', 'false');
    });

    it('clears pending timeout on component unmount', async () => {
      const clearSpy = vi.spyOn(global, 'clearTimeout');
      const { unmount } = render(<CodeRemediationModal {...defaultProps} />);
      const copyButton = screen.getByLabelText(/Copy vulnerable code/i);
      
      await act(async () => {
        fireEvent.click(copyButton);
      });
      
      unmount();
      expect(clearSpy).toHaveBeenCalled();
      clearSpy.mockRestore();
    });

    it('replaces one panel indicator when another is clicked', async () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const vulnBtn = screen.getByLabelText(/Copy vulnerable code/i);
      const secureBtn = screen.getByLabelText(/Copy secure fix code/i);
      
      await act(async () => {
        fireEvent.click(vulnBtn);
      });
      expect(vulnBtn).toHaveAttribute('data-copied', 'true');
      
      await act(async () => {
        fireEvent.click(secureBtn);
      });
      expect(vulnBtn).toHaveAttribute('data-copied', 'false');
      expect(secureBtn).toHaveAttribute('data-copied', 'true');
    });

    it('handles multiple rapid copies without producing stale timer callbacks', async () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const vulnBtn = screen.getByLabelText(/Copy vulnerable code/i);
      
      await act(async () => {
        fireEvent.click(vulnBtn); // Timer 1 set
      });
      
      act(() => {
        vi.advanceTimersByTime(1000);
      });
      
      await act(async () => {
        fireEvent.click(vulnBtn); // Timer 2 set, Timer 1 cleared
      });
      
      act(() => {
        vi.advanceTimersByTime(1000); // Timer 1 would have fired now if not cleared
      });
      
      expect(vulnBtn).toHaveAttribute('data-copied', 'true');
      
      act(() => {
        vi.advanceTimersByTime(1000); // Timer 2 fires
      });
      
      expect(vulnBtn).toHaveAttribute('data-copied', 'false');
    });

    it('handles empty code strings', async () => {
      const emptyProps = {
        ...defaultProps,
        example: { vulnerable: '', secure: '', language: 'text' }
      };
      render(<CodeRemediationModal {...emptyProps} />);
      const copyButton = screen.getByLabelText(/Copy vulnerable code/i);
      await act(async () => {
        fireEvent.click(copyButton);
      });
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('');
    });

    it('does not crash when clipboard.writeText rejects', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      render(<CodeRemediationModal {...defaultProps} />);
      const error = new Error('Clipboard error');
      (navigator.clipboard.writeText as any).mockRejectedValueOnce(error);
      
      const copyButton = screen.getByLabelText(/Copy vulnerable code/i);
      
      await act(async () => {
        fireEvent.click(copyButton);
      });
      
      expect(consoleSpy).toHaveBeenCalledWith('Failed to copy: ', error);
      expect(copyButton).toHaveAttribute('data-copied', 'false');
    });

    it('recovers and allows successful copy after a previous rejection', async () => {
      vi.spyOn(console, 'error').mockImplementation(() => {});
      render(<CodeRemediationModal {...defaultProps} />);
      const error = new Error('Transient error');
      (navigator.clipboard.writeText as any)
        .mockRejectedValueOnce(error)
        .mockResolvedValueOnce(undefined);
      
      const copyButton = screen.getByLabelText(/Copy vulnerable code/i);
      
      // Attempt 1: Fails
      await act(async () => {
        fireEvent.click(copyButton);
      });
      expect(copyButton).toHaveAttribute('data-copied', 'false');

      // Attempt 2: Succeeds
      await act(async () => {
        fireEvent.click(copyButton);
      });
      expect(copyButton).toHaveAttribute('data-copied', 'true');
    });

    it('is no-op when navigator.clipboard is undefined', async () => {
      vi.stubGlobal('navigator', { clipboard: undefined });
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
      render(<CodeRemediationModal {...defaultProps} />);
      
      const copyButton = screen.getByLabelText(/Copy vulnerable code/i);
      
      await act(async () => {
        fireEvent.click(copyButton);
      });
      
      expect(alertSpy).toHaveBeenCalledWith('Clipboard API unavailable in this context.');
      expect(copyButton).toHaveAttribute('data-copied', 'false');
      
      alertSpy.mockRestore();
    });
  });

  describe('accessibility', () => {
    it('has role dialog with aria-modal true', () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('verifies visual code assignment (vulnerable vs secure panels)', () => {
      render(<CodeRemediationModal {...defaultProps} />);
      
      const vulnPanel = screen.getByTestId('vulnerable-panel');
      const securePanel = screen.getByTestId('secure-panel');
      
      expect(vulnPanel.querySelector('code')?.textContent).toBe(defaultProps.example.vulnerable);
      expect(securePanel.querySelector('code')?.textContent).toBe(defaultProps.example.secure);
    });

    it('links aria-labelledby to the title element', () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const dialog = screen.getByRole('dialog');
      const title = screen.getByText(/Remediation Guide: SQL Injection/i);
      expect(dialog).toHaveAttribute('aria-labelledby', title.id);
    });

    it('traps focus and cycles through elements', () => {
      render(<CodeRemediationModal {...defaultProps} />);
      const dialog = screen.getByRole('dialog');
      const focusable = dialog.querySelectorAll('button');
      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      // Initial focus
      expect(document.activeElement).toBe(dialog);

      // Focus first
      act(() => { first.focus(); });
      expect(document.activeElement).toBe(first);

      // Tab from last element
      act(() => { last.focus(); });
      fireEvent.keyDown(last, { key: 'Tab', shiftKey: false });
      expect(document.activeElement).toBe(first);

      // Shift+Tab from first element
      act(() => { first.focus(); });
      fireEvent.keyDown(first, { key: 'Tab', shiftKey: true });
      expect(document.activeElement).toBe(last);
    });
  });
});
