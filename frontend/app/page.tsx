'use client';

import { useState, useRef } from 'react';
import ChatInterface from '@/components/ChatInterface';
import NewsArticles from '@/components/NewsArticles';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import HeroCards from '@/components/HeroCards';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

export default function Home() {
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout } = useAuth();
  const newsSectionRef = useRef<HTMLElement>(null);

  const scrollToNews = () => {
    newsSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3">
              <LogoMono className="h-16" />
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/dashboard'}>Dashboard</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/companies'}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties'}>Prospector's Exchange</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/metals'}>Metals</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/financial-hub'}>Financial Hub</Button>

              {user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-slate-300">
                    Welcome, {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </div>
              ) : (
                <>
                  <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>
                    Login
                  </Button>
                  <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>
                    Register
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Auth Modals */}
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

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Background gradient effect */}
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-5xl md:text-6xl font-bold mb-6 text-gradient-gold animate-fade-in leading-tight pb-2">
              Junior Gold Mining Intelligence
            </h2>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto animate-slide-in-up">
              AI-powered investor relations platform for junior gold mining investors and companies.
              Instant access to projects, resources, prospector listings and technical data.
            </p>
          </div>

          {/* Three Content Cards */}
          <div className="mb-12">
            <HeroCards
              onLoginClick={() => setShowLogin(true)}
              onRegisterClick={() => setShowRegister(true)}
            />
          </div>

          {/* Navigation Buttons */}
          <div className="flex flex-wrap gap-4 justify-center">
            <Button variant="primary" size="lg" onClick={() => window.location.href = '/companies'}>
              Explore All Companies
            </Button>
            <Button variant="primary" size="lg" onClick={() => window.location.href = '/properties'}>
              Prospector's Exchange
            </Button>
            <Button variant="secondary" size="lg" onClick={scrollToNews}>
              Latest News Articles
            </Button>
          </div>
        </div>
      </section>

      {/* Chat Interface Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h3 className="text-4xl font-bold text-gold-400 mb-4">Ask Anything About Mining Companies of Properties</h3>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Natural language access to companies, projects, resources, prospector listings, and economic studies.
              Claude uses MCP servers to query your PostgreSQL database in real-time.
            </p>
          </div>

          <ChatInterface />
        </div>
      </section>

      {/* News Articles Section */}
      <section ref={newsSectionRef} id="news-section" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h3 className="text-4xl font-bold text-gold-400 mb-4">Latest Mining News</h3>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Stay informed with the latest news and developments from the mining industry.
            </p>
          </div>

          <div className="backdrop-blur-sm bg-slate-800/30 border border-slate-700/50 rounded-xl p-6">
            <NewsArticles initialLimit={10} showLoadMore={true} />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h3 className="text-4xl font-bold text-gold-400 mb-4">Platform Features</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: 'Claude AI Assistant',
                description: 'Natural language queries for mining data',
                badge: 'AI',
                svgPath: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'
              },
              {
                title: 'Resource Database',
                description: 'Comprehensive M&I resource tracking',
                badge: 'Data',
                svgPath: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4'
              },
              {
                title: 'Metals Prices',
                description: 'Real-time gold, silver, and metal pricing',
                badge: 'Markets',
                svgPath: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
              },
              {
                title: 'Project Analytics',
                description: 'Economic studies and feasibility data',
                badge: 'Analytics',
                svgPath: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
              }
            ].map((feature, idx) => (
              <Card key={idx} variant="glass-card" className="text-center animate-slide-in-up" style={{ animationDelay: `${idx * 100}ms` }}>
                <CardHeader>
                  <Badge variant="gold" className="mx-auto mb-4">{feature.badge}</Badge>
                  <div className="w-16 h-16 rounded-lg mx-auto mb-4 flex items-center justify-center"
                       style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
                    <svg className="w-8 h-8" style={{ color: '#d4af37' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={feature.svgPath} />
                    </svg>
                  </div>
                  <CardTitle className="text-lg mb-2">{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="glass-nav py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center mb-4">
            <LogoMono className="h-16" />
          </div>
          <p className="text-slate-400">
            AI-Powered Mining Intelligence Platform
          </p>
          <div className="mt-6 flex justify-center space-x-6">
            <Badge variant="slate">Next.js</Badge>
            <Badge variant="slate">Django</Badge>
            <Badge variant="slate">PostgreSQL</Badge>
          </div>
        </div>
      </footer>
    </div>
  );
}
