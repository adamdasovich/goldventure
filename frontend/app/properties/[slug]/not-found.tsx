import Link from "next/link";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Property Not Found",
  description: "The requested property listing could not be found.",
};

export default function PropertyNotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <div className="text-center p-8">
        <h1 className="text-4xl font-bold text-white mb-4">
          Property Not Found
        </h1>
        <p className="text-slate-400 mb-6">
          The property listing you're looking for doesn't exist or has been
          removed.
        </p>
        <Link
          href="/properties"
          className="inline-flex items-center px-6 py-3 bg-gold-500 text-slate-900 font-semibold rounded-lg hover:bg-gold-400 transition-colors"
        >
          Browse Prospector's Exchange
        </Link>
      </div>
    </div>
  );
}
