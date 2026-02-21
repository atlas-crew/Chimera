import React, { useState } from 'react';
import ReactJoyride, { Step, CallBackProps, STATUS, EVENTS } from 'react-joyride';
import { useTheme } from './ThemeProvider';
import { useNavigate, useLocation } from 'react-router-dom';

export const TourGuide: React.FC = () => {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [run, setRun] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  // Auto-start tour if requested (can be expanded with URL params or context)
  // For now, we'll start it manually via a button in the UI or if on Home
  
  const steps: Step[] = [
    {
      target: 'body',
      content: (
        <div>
          <h3 className="font-bold text-lg mb-2">Welcome to the Vulnerable Portal</h3>
          <p>This application is designed to demonstrate real-world security vulnerabilities. Let's take a quick tour of a SQL Injection exploit.</p>
        </div>
      ),
      placement: 'center',
      disableBeacon: true,
    },
    {
      target: 'a[href="/healthcare"]',
      content: 'Navigate to the Healthcare Dashboard. This vertical contains a classic SQL Injection vulnerability in the search bar.',
      spotlightClicks: true,
      disableBeacon: true,
    },
    {
      target: '#healthcare-search-input',
      content: (
        <div>
          <h3 className="font-bold text-sm mb-2">The Vulnerable Target</h3>
          <p className="mb-2">This search bar is vulnerable. Try entering this payload:</p>
          <code className="block bg-slate-100 dark:bg-slate-800 p-2 rounded text-xs font-mono text-red-600 mb-2">
            ' OR 1=1 --
          </code>
          <p>This payload injects a tautology (1=1) into the SQL query, forcing the database to return all records instead of filtering them.</p>
        </div>
      ),
      placement: 'bottom',
    },
    {
      target: '.red-team-console-hint', // We need to add this class to the footer hint
      content: 'Keep an eye on the Red Team Console (Ctrl + ~) to see the attack log in real-time as you execute exploits.',
      placement: 'top',
    }
  ];

  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status, type, index, action } = data;
    
    if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
      setRun(false);
      setStepIndex(0);
    } else if (type === EVENTS.STEP_AFTER && index === 1) {
      // Automatically navigate to healthcare if the user clicks next on the link step
      if (location.pathname !== '/healthcare') {
        navigate('/healthcare');
        // Give time for navigation
        setTimeout(() => {
            setStepIndex(2);
        }, 500);
      }
    } else if (type === EVENTS.STEP_AFTER || type === EVENTS.TARGET_NOT_FOUND) {
        // Update state to advance the tour
        setStepIndex(index + (action === 'prev' ? -1 : 1));
    }
  };

  // Expose a global way to start the tour (simplistic for this demo)
  React.useEffect(() => {
    (window as any).startTour = () => {
        setRun(true);
        setStepIndex(0);
        if (location.pathname !== '/') navigate('/');
    };
  }, [navigate, location]);

  return (
    <ReactJoyride
      steps={steps}
      run={run}
      stepIndex={stepIndex}
      continuous
      showSkipButton
      showProgress
      callback={handleJoyrideCallback}
      styles={{
        options: {
          primaryColor: '#2563eb',
          textColor: theme === 'dark' ? '#e2e8f0' : '#1e293b',
          backgroundColor: theme === 'dark' ? '#1e293b' : '#ffffff',
          arrowColor: theme === 'dark' ? '#1e293b' : '#ffffff',
        },
      }}
    />
  );
};
