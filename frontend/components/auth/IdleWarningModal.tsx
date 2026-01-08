'use client';

import { useIdleTimeout } from '@/contexts/IdleTimeoutContext';
import { useAuth } from '@/contexts/AuthContext';

export default function IdleWarningModal() {
  const { showWarning, remainingTime, resetTimer } = useIdleTimeout();
  const { logout } = useAuth();

  if (!showWarning) return null;

  const minutes = Math.floor(remainingTime / 60000);
  const seconds = Math.floor((remainingTime % 60000) / 1000);
  const timeDisplay = minutes > 0
    ? `${minutes}:${seconds.toString().padStart(2, '0')}`
    : `${seconds} seconds`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        {/* Warning Icon */}
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 bg-yellow-500/10 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-yellow-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h2 className="text-xl font-semibold text-white text-center mb-2">
          Session Expiring Soon
        </h2>

        {/* Message */}
        <p className="text-zinc-400 text-center mb-4">
          Your session will expire due to inactivity.
        </p>

        {/* Countdown */}
        <div className="bg-zinc-800 rounded-lg p-4 mb-6 text-center">
          <p className="text-sm text-zinc-500 mb-1">Time remaining</p>
          <p className="text-3xl font-mono font-bold text-yellow-500">
            {timeDisplay}
          </p>
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={logout}
            className="flex-1 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg transition-colors"
          >
            Log Out Now
          </button>
          <button
            onClick={resetTimer}
            className="flex-1 px-4 py-2.5 bg-yellow-600 hover:bg-yellow-500 text-black font-medium rounded-lg transition-colors"
          >
            Stay Logged In
          </button>
        </div>

        {/* Help text */}
        <p className="text-xs text-zinc-500 text-center mt-4">
          Click &quot;Stay Logged In&quot; or interact with the page to continue your session.
        </p>
      </div>
    </div>
  );
}
