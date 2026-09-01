"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";

interface RegisterModalProps {
  onClose: () => void;
  onSwitchToLogin: () => void;
}

/**
 * Who is signing up — NOT which plan they are on.
 *
 * This writes `user_type`, which shows as a badge in the company forums and is
 * what the Financial Hub filters on. It has nothing to do with billing: every
 * registration gets the same thing regardless of what is picked here, so the
 * options must not read as plan names or someone choosing "Company" will expect
 * editing rights they have not been approved for.
 *
 * Three, matching the audiences the platform serves. "Student" was dropped on
 * 2026-09-01: it drove nothing and was the one option that did not describe a
 * customer. The model keeps its full list — `company` is written by the access
 * request approval, `admin` gates forum moderation, and existing `student` and
 * `analyst` rows still have to render their badge — so this is the offered set,
 * not the allowed set.
 */
const USER_TYPE_OPTIONS = [
  { value: "investor", label: "Investor" },
  { value: "mining_company", label: "Mining Company" },
  { value: "prospector", label: "Prospector" },
];

// Single password rule, matching the backend's MinimumLengthValidator in
// config/settings.py. No composition rules (uppercase/number/symbol) — length
// is what matters, and stacking extra rules only surprises people mid-signup.
const MIN_PASSWORD_LENGTH = 12;

function PasswordVisibilityToggle({
  visible,
  onToggle,
  label,
}: {
  visible: boolean;
  onToggle: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={visible ? `Hide ${label}` : `Show ${label}`}
      aria-pressed={visible}
      className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 hover:text-white transition-colors focus:outline-none focus:text-gold-400"
    >
      {visible ? (
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
          />
        </svg>
      ) : (
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
        </svg>
      )}
    </button>
  );
}

export function RegisterModal({
  onClose,
  onSwitchToLogin,
}: RegisterModalProps) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [userType, setUserType] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const passwordLongEnough = password.length >= MIN_PASSWORD_LENGTH;
  const passwordsMatch = password === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!userType) {
      setError("Please select a user type");
      return;
    }

    if (!passwordLongEnough) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters`);
      return;
    }

    if (!passwordsMatch) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      await register(username, email, password, fullName, userType);
      onClose();
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal onClose={onClose} size="md" labelledBy="register-modal-title">
      <Card variant="glass-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle id="register-modal-title">Create Account</CardTitle>
            <button
              onClick={onClose}
              aria-label="Close registration"
              className="-mr-2 p-2 text-slate-400 hover:text-white transition-colors"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label
                htmlFor="userType"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                I am a... <span className="text-red-400">*</span>
              </label>
              <div className="space-y-2">
                {USER_TYPE_OPTIONS.map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-center p-3 rounded-lg cursor-pointer transition-all border ${
                      userType === option.value
                        ? "bg-gold-500/20 border-gold-500 text-gold-400"
                        : "bg-slate-800/50 border-slate-700 hover:border-slate-600"
                    }`}
                  >
                    <input
                      type="radio"
                      name="userType"
                      value={option.value}
                      checked={userType === option.value}
                      onChange={(e) => setUserType(e.target.value)}
                      className="w-4 h-4 text-gold-500 bg-slate-800 border-slate-700 focus:ring-gold-500 focus:ring-2"
                    />
                    <span className="ml-3 text-white">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label
                htmlFor="fullName"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Full Name
              </label>
              <input
                type="text"
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                placeholder="Enter your full name"
                required
              />
            </div>

            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Username
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                placeholder="Choose a username"
                required
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Email
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                placeholder="Enter your email"
                required
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-4 pr-11 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                  placeholder={`At least ${MIN_PASSWORD_LENGTH} characters`}
                  required
                  minLength={MIN_PASSWORD_LENGTH}
                />
                <PasswordVisibilityToggle
                  visible={showPassword}
                  onToggle={() => setShowPassword((v) => !v)}
                  label="password"
                />
              </div>
              <p
                className={`mt-2 text-xs ${
                  passwordLongEnough ? "text-green-400" : "text-slate-400"
                }`}
              >
                {passwordLongEnough
                  ? "Looks good."
                  : `Use at least ${MIN_PASSWORD_LENGTH} characters. That's the only rule — a short phrase works well.`}
              </p>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-slate-300 mb-2"
              >
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-4 pr-11 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                  placeholder="Confirm your password"
                  required
                />
                <PasswordVisibilityToggle
                  visible={showConfirmPassword}
                  onToggle={() => setShowConfirmPassword((v) => !v)}
                  label="confirmed password"
                />
              </div>
              {confirmPassword.length > 0 && !passwordsMatch && (
                <p className="mt-2 text-xs text-red-400">
                  Passwords do not match
                </p>
              )}
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={loading}
            >
              {loading ? "Creating Account..." : "Create Account"}
            </Button>

            <div className="text-center text-sm text-slate-400">
              Already have an account?{" "}
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="text-gold-400 hover:text-gold-300 transition-colors"
              >
                Login
              </button>
            </div>
          </form>
        </CardContent>
      </Card>
    </Modal>
  );
}
