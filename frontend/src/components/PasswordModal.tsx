"use client";

import React, { useState } from "react";

interface PasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (password: string) => void;
  apiBaseUrl: string;
}

export default function PasswordModal({
  isOpen,
  onClose,
  onSuccess,
  apiBaseUrl,
}: PasswordModalProps) {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      setError("Password cannot be empty.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
      });

      if (response.ok) {
        onSuccess(password);
        onClose();
        setPassword("");
      } else {
        const errData = await response.json().catch(() => ({}));
        setError(errData.detail || "Authentication failed. Invalid password.");
      }
    } catch (err) {
      console.error("Auth error:", err);
      setError("Unable to connect to the authentication server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Dark backdrop with smooth blur */}
      <div
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Premium Glassmorphic Card Container */}
      <div className="relative w-full max-w-md transform overflow-hidden rounded-3xl border border-slate-700/60 bg-slate-900/90 p-8 shadow-2xl transition-all duration-300 hover:border-indigo-500/30 backdrop-blur-xl">
        {/* Glow Element */}
        <div className="absolute -top-24 -left-24 h-48 w-48 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-48 w-48 rounded-full bg-purple-500/10 blur-3xl" />

        {/* Modal Header */}
        <div className="relative z-10 text-center mb-6">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-white tracking-tight">
            Security Gate
          </h3>
          <p className="mt-2 text-sm text-slate-400">
            Please verify the Master Password to complete this state mutation.
          </p>
        </div>

        {/* Challenge Input Form */}
        <form onSubmit={handleSubmit} className="relative z-10 space-y-5">
          <div>
            <label
              htmlFor="password"
              className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2"
            >
              Master Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
              className="w-full rounded-2xl border border-slate-700/80 bg-slate-950/50 px-4 py-3.5 text-white placeholder-slate-600 transition-all focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
              autoFocus
            />
          </div>

          {error && (
            <div className="flex items-center gap-2.5 rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-400 animate-shake">
              <svg
                className="h-5 w-5 shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 rounded-2xl border border-slate-800 bg-slate-800/80 py-3.5 text-sm font-semibold text-slate-300 transition-colors hover:bg-slate-800 hover:text-white focus:outline-none disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex justify-center items-center rounded-2xl bg-indigo-600 py-3.5 text-sm font-semibold text-white transition-all hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 focus:outline-none disabled:opacity-50"
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                "Authorize"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
