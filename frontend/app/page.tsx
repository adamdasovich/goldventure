import ChatInterface from '@/components/ChatInterface';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3">
              <LogoMono className="h-18" />
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="copper">AI-Powered</Badge>
              <Button variant="ghost" size="sm">Dashboard</Button>
              <Button variant="ghost" size="sm">Companies</Button>
              <Button variant="primary" size="sm">Sign In</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Background gradient effect */}
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-6">
            Powered by Claude AI
          </Badge>
          <h2 className="text-5xl md:text-6xl font-bold mb-6 text-gradient-gold animate-fade-in leading-tight pb-2">
            Junior Mining Intelligence
          </h2>
          <h1></h1>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto mb-12 animate-slide-in-up">
            AI-powered investor relations platform for junior gold mining companies.
            Instant access to projects, resources, and technical data.
          </p>

          <div className="flex flex-wrap gap-4 justify-center">
            <Button variant="primary" size="lg">Explore Companies</Button>
            <Button variant="secondary" size="lg">Start Chat</Button>
          </div>
        </div>
      </section>

      {/* Chat Interface Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <Badge variant="copper" className="mb-4">Claude AI Integration</Badge>
            <h3 className="text-4xl font-bold text-gold-400 mb-4">Ask Anything About Your Mining Data</h3>
            <p className="text-slate-300 text-lg max-w-2xl mx-auto">
              Natural language access to companies, projects, resources, and economic studies.
              Claude uses MCP servers to query your PostgreSQL database in real-time.
            </p>
          </div>

          <ChatInterface />
        </div>
      </section>

      {/* Companies Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h3 className="text-4xl font-bold text-gold-400 mb-4">Mining Companies</h3>
            <p className="text-slate-300 text-lg mb-8">
              Explore our portfolio of junior gold mining companies
            </p>
            <Button variant="primary" size="lg">View All Companies</Button>
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
                icon: '🤖',
                badge: 'AI'
              },
              {
                title: 'Resource Database',
                description: 'Comprehensive M&I resource tracking',
                icon: '📊',
                badge: 'Data'
              },
              {
                title: 'Project Analytics',
                description: 'Economic studies and feasibility data',
                icon: '📈',
                badge: 'Analytics'
              },
              {
                title: 'Real-time Market',
                description: 'Stock prices and market capitalization',
                icon: '💹',
                badge: 'Markets'
              }
            ].map((feature, idx) => (
              <Card key={idx} variant="glass-card" className="text-center animate-slide-in-up" style={{ animationDelay: `${idx * 100}ms` }}>
                <CardHeader>
                  <Badge variant="gold" className="mx-auto mb-4">{feature.badge}</Badge>
                  <div className="text-5xl mb-4">{feature.icon}</div>
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
            <Badge variant="slate">Powered by Claude</Badge>
            <Badge variant="slate">Next.js</Badge>
            <Badge variant="slate">Django</Badge>
            <Badge variant="slate">PostgreSQL</Badge>
          </div>
        </div>
      </footer>
    </div>
  );
}
