"use client";

import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function CompanyDetailError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gold-400 mb-4">
          Something went wrong
        </h1>
        <p className="text-slate-400 mb-8 max-w-md mx-auto">
          We couldn&apos;t load this company profile. Please try again or browse
          our full company directory.
        </p>
        <div className="flex gap-4 justify-center">
          <Button variant="primary" onClick={reset}>
            Try Again
          </Button>
          <Link href="/companies">
            <Button variant="secondary">Browse Companies</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
