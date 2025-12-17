import { Metadata } from 'next';
import { TheTicker } from '@/components/store/TheTicker';
import { StoreHeader } from '@/components/store/StoreHeader';

export const metadata: Metadata = {
  title: 'Store',
  description: 'Browse rare specimens, field gear, and educational resources for gold mining enthusiasts.',
};

export default function StoreLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Store Header with Navigation */}
      <StoreHeader />

      {/* The Ticker Banner */}
      <TheTicker variant="banner" />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </div>
    </div>
  );
}
