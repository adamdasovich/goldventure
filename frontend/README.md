# GoldVenture Frontend

AI-powered mining intelligence platform with glassmorphism design.

## Design System: "Golden Depths"

Premium fintech aesthetic combining:
- **Gold** (#D4A12A) - Trust, value, precious metals
- **Deep Slate** (#0F172A) - Sophistication, geological depth
- **Copper** (#EA580C) - Innovation, AI/tech integration

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS v4** - Styling with custom design system
- **Claude API** - AI chat integration

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your Django backend URL
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with metadata
│   ├── page.tsx            # Home page with all sections
│   └── globals.css         # Design system CSS
├── components/
│   ├── ui/                 # Reusable UI components
│   │   ├── Button.tsx      # Primary, secondary, ghost variants
│   │   ├── Card.tsx        # Glass card with header/content/footer
│   │   ├── Input.tsx       # Text input and textarea
│   │   ├── Badge.tsx       # Status badges
│   │   └── index.ts        # Export barrel
│   ├── ChatInterface.tsx   # Claude AI chat component
│   └── CompanyList.tsx     # Company cards grid
├── lib/
│   └── api.ts             # API client for Django backend
├── types/
│   └── api.ts             # TypeScript types for API
└── .env.local             # Environment variables
```

## Components

### UI Components

All components follow the "Golden Depths" design system:

**Button**
```tsx
<Button variant="primary">Primary Action</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="ghost">Ghost</Button>
```

**Card**
```tsx
<Card variant="glass-card">
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

**Input**
```tsx
<Input label="Name" placeholder="Enter name..." />
<Textarea label="Message" />
```

**Badge**
```tsx
<Badge variant="gold">Gold</Badge>
<Badge variant="copper">Copper</Badge>
<Badge variant="success">Success</Badge>
```

### Feature Components

**ChatInterface**
- Claude AI integration
- Real-time chat with typing indicators
- Tool call visualization
- Message history

**CompanyList**
- Fetches from Django API
- Glass card grid layout
- Hover animations
- Loading skeletons

## Design System

### Colors

```css
--gold-500: #D4A12A      /* Primary brand */
--slate-900: #0F172A     /* Background */
--copper-500: #EA580C    /* Accent */
```

### Glassmorphism

```css
.glass                   /* Standard glass */
.glass-strong           /* Strong blur */
.glass-card             /* Interactive card */
.glass-nav              /* Navigation bar */
```

### Animations

```css
.animate-slide-in-up    /* Entrance animation */
.animate-fade-in        /* Fade in */
.animate-pulse-glow     /* Gold glow pulse */
.animate-shimmer        /* Loading shimmer */
```

### Transitions

- **Fast**: 150ms - Small UI changes
- **Base**: 250ms - Standard transitions
- **Slow**: 350ms - Complex animations

## API Integration

The frontend connects to the Django backend at `http://localhost:8000/api`:

**Endpoints:**
- `GET /companies/` - List companies
- `GET /companies/{id}/` - Company details
- `GET /projects/` - List projects
- `POST /claude/chat/` - Claude AI chat

**Example:**
```tsx
import { companyAPI, claudeAPI } from '@/lib/api';

// Fetch companies
const { results } = await companyAPI.getAll();

// Chat with Claude
const response = await claudeAPI.chat({
  message: "What are my total gold resources?",
  conversation_history: []
});
```

## Accessibility

- WCAG AA compliant contrast ratios
- Focus states on all interactive elements
- Keyboard navigation support
- Semantic HTML structure

## Development

**Run development server:**
```bash
npm run dev
```

**Build for production:**
```bash
npm run build
```

**Start production server:**
```bash
npm start
```

**Type checking:**
```bash
npm run type-check
```

## Design Principles

1. **Trust Through Transparency** - Glassmorphism creates depth
2. **Premium Simplicity** - Clean layouts with purposeful accents
3. **Depth & Layers** - Visual hierarchy through elevation
4. **Smooth Interactions** - Subtle animations enhance UX
5. **Professional Innovation** - Modern tech meets financial credibility

---

**Version:** 1.0.0
**Last Updated:** 2025-01-16
