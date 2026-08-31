"use client";

import { useState } from "react";
import { LoginModal } from "./LoginModal";
import { RegisterModal } from "./RegisterModal";
import { Button } from "@/components/ui/Button";

/**
 * The "you need to be signed in" state, for pages that require an account.
 *
 * Replaces four `router.push('/auth/login?redirect=...')` calls that pointed at
 * a route this site has never had — logging in happens in a modal, so the page
 * was never built and all four sent people to a 404.
 *
 * Signing in here needs no callback: AuthContext updates, the parent's
 * `isAuthenticated` flips, and the parent stops rendering this and shows the
 * real page. That is also why it keeps the visitor where they were, which the
 * old redirect could not do even if the page had existed.
 */

interface SignInRequiredProps {
  /** What they were trying to reach, e.g. "the admin area". */
  destination?: string;
  title?: string;
}

export function SignInRequired({
  destination,
  title = "Sign in to continue",
}: SignInRequiredProps) {
  // Open on arrival: they came here meaning to do something, so put the form
  // in front of them rather than making them click twice.
  const [showLogin, setShowLogin] = useState(true);
  const [showRegister, setShowRegister] = useState(false);

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-bold text-slate-100 mb-3">{title}</h1>
        <p className="text-slate-400 mb-6">
          {destination
            ? `You need to be signed in to reach ${destination}.`
            : "You need to be signed in to view this page."}
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            variant="primary"
            size="lg"
            onClick={() => {
              setShowRegister(false);
              setShowLogin(true);
            }}
          >
            Sign in
          </Button>
          <Button
            variant="secondary"
            size="lg"
            onClick={() => {
              setShowLogin(false);
              setShowRegister(true);
            }}
          >
            Create an account
          </Button>
        </div>
      </div>

      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}
    </div>
  );
}

export default SignInRequired;
