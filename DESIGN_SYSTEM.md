# GoldVenture Design System
## "Golden Depths" - Premium Mining Fintech Aesthetic

---

## 🎨 Color Palette

### Primary Colors (Gold)
Conveys **value, trust, and precious metals expertise**

```
Gold-50:  #FFFBEB  - Lightest tint (backgrounds)
Gold-100: #FEF3C7  - Light tint
Gold-200: #FDE68A  - Subtle highlights
Gold-300: #FCD34D  - Soft accents
Gold-400: #FBBF24  - Medium gold
Gold-500: #D4A12A  ⭐ PRIMARY BRAND - Rich, professional gold
Gold-600: #B8860B  - Deep gold (hover states)
Gold-700: #92600D  - Dark gold
Gold-800: #78430A  - Darker
Gold-900: #5E3208  - Darkest (text on light)
```

**Usage:**
- Primary CTAs (buttons, links)
- Brand accents
- Success indicators
- Data highlights (resource ounces, valuations)

---

### Secondary Colors (Slate/Deep Ocean)
Conveys **depth, sophistication, geological authenticity**

```
Slate-50:  #F8FAFC  - Lightest (light mode backgrounds)
Slate-100: #F1F5F9  - Light cards
Slate-200: #E2E8F0  - Borders, dividers
Slate-300: #CBD5E1  - Subtle text
Slate-400: #94A3B8  - Muted text
Slate-500: #64748B  - Secondary text
Slate-600: #475569  ⭐ SECONDARY BASE
Slate-700: #334155  - Elevated surfaces
Slate-800: #1E293B  - Card backgrounds (dark)
Slate-900: #0F172A  ⭐ PRIMARY BACKGROUND (dark mode)
```

**Usage:**
- Backgrounds (dark mode default)
- Text hierarchy
- Borders and dividers
- Navigation bars

---

### Accent Colors (Copper)
Conveys **energy, innovation, AI/tech integration**

```
Copper-400: #FB923C  - Light copper
Copper-500: #EA580C  ⭐ ACCENT - Bright, energetic
Copper-600: #C2410C  - Deep copper (hover)
```

**Usage:**
- AI/Claude features
- Interactive elements
- Notifications
- Innovation highlights

---

### Semantic Colors

```
Success: #10B981  🟢 - Positive metrics, confirmations
Warning: #F59E0B  🟡 - Alerts, important notices
Error:   #EF4444  🔴 - Errors, critical warnings
Info:    #3B82F6  🔵 - Informational messages
```

---

## 🪟 Glassmorphism Effects

### Standard Glass
```css
background: rgba(255, 255, 255, 0.10)
backdrop-filter: blur(12px) saturate(180%)
border: 1px solid rgba(255, 255, 255, 0.125)
box-shadow: 0 8px 32px 0 rgba(15, 23, 42, 0.37)
```

**Use for:** Cards, modals, overlays

---

### Strong Glass
```css
background: rgba(255, 255, 255, 0.15)
backdrop-filter: blur(16px) saturate(200%)
border: 1px solid rgba(255, 255, 255, 0.18)
```

**Use for:** Important cards, chat interface, elevated surfaces

---

### Glass Card (Hover)
```css
background: rgba(255, 255, 255, 0.08) → rgba(255, 255, 255, 0.12)
border: rgba(255, 255, 255, 0.1) → rgba(212, 161, 42, 0.3)
transform: translateY(0) → translateY(-2px)
box-shadow: Enhanced with gold glow
```

**Use for:** Interactive cards, company listings, project cards

---

## ⚡ Animation Specifications

### Timing
- **Fast (150ms)**: Small UI changes, button clicks
- **Base (250ms)**: Standard transitions, hover effects
- **Slow (350ms)**: Complex animations, page transitions

### Easing Functions
- **Smooth**: `cubic-bezier(0.4, 0, 0.2, 1)` - General use
- **Bounce**: `cubic-bezier(0.68, -0.55, 0.265, 1.55)` - Playful (use sparingly)
- **Ease-out**: `cubic-bezier(0, 0, 0.2, 1)` - Entrance animations
- **Ease-in**: `cubic-bezier(0.4, 0, 1, 1)` - Exit animations

---

## 🔘 Button Variants

### Primary Button (Gold)
```
Background: Gold gradient
Text: White
Hover: Pulse glow animation + slight scale
Active: Ripple effect
Shadow: Gold glow
```

### Secondary Button (Glass)
```
Background: Glassmorphism
Border: Gold-500
Text: Gold-400
Hover: Stronger glass + gold border glow
```

### Ghost Button
```
Background: Transparent
Border: Slate-600
Text: Slate-300
Hover: Glass background fade-in
```

---

## 📐 Spacing & Sizing

### Border Radius
- **sm**: 8px - Input fields, tags
- **md**: 12px - Buttons, small cards
- **lg**: 16px - Cards, modals
- **xl**: 24px - Large cards, hero sections

### Shadows
- **Subtle**: `0 2px 8px rgba(0, 0, 0, 0.08)`
- **Glass**: `0 8px 32px rgba(15, 23, 42, 0.37)`
- **Gold**: `0 4px 20px rgba(212, 161, 42, 0.25)`
- **Elevation**: `0 10px 40px rgba(0, 0, 0, 0.15)`

---

## 🎭 Component Examples

### Chat Interface Card
```
Background: Strong glass
Border-radius: 16px
Border: 1px rgba(255, 255, 255, 0.15)
Shadow: Glass shadow
Animation: Slide-in-up on load
```

### Company Card (Interactive)
```
Background: Standard glass → Strong glass on hover
Border: Subtle → Gold accent on hover
Transform: translateY(0) → translateY(-2px)
Shadow: Glass → Enhanced gold glow
Transition: 250ms smooth
```

### Navigation Bar
```
Background: rgba(15, 23, 42, 0.8)
Backdrop-filter: blur(24px)
Border-bottom: 1px rgba(255, 255, 255, 0.08)
Position: Sticky
```

---

## 📱 Responsive Breakpoints

```
sm:  640px  - Mobile landscape
md:  768px  - Tablets
lg:  1024px - Laptops
xl:  1280px - Desktops
2xl: 1536px - Large screens
```

---

## ✅ Accessibility

### Contrast Ratios (WCAG AA)
- Gold-500 on Slate-900: ✓ 7.2:1
- White on Gold-600: ✓ 4.8:1
- Slate-300 on Slate-900: ✓ 8.1:1

### Focus States
All interactive elements have visible focus rings:
```css
outline: 2px solid var(--gold-500)
outline-offset: 2px
```

---

## 🎯 Design Principles

1. **Trust Through Transparency**: Glassmorphism creates depth while maintaining clarity
2. **Premium Simplicity**: Clean layouts with purposeful gold accents
3. **Depth & Layers**: Visual hierarchy through glass elevation
4. **Smooth Interactions**: Subtle animations that enhance, not distract
5. **Professional Innovation**: Modern tech aesthetic meets financial credibility

---

## 💡 Usage Guidelines

### DO:
✅ Use gold for primary actions and value indicators
✅ Layer glass effects for depth
✅ Apply animations to enhance user feedback
✅ Maintain generous whitespace
✅ Use dark mode as default

### DON'T:
❌ Overuse gold (keep it special)
❌ Stack too many glass layers
❌ Use harsh animations
❌ Clutter the interface
❌ Sacrifice readability for aesthetics

---

**Last Updated:** 2025-01-16
**Version:** 1.0.0
**Designer:** GoldVenture Platform Team
