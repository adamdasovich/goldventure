# GoldVenture Prospector Exchange - Property Listing Template Design

## Overview

This document outlines the comprehensive property listing template for the GoldVenture Prospector Exchange, connecting prospectors with investors and mining companies. The platform operates on a **5% commission model** on successful transactions, with free listings for prospectors.

---

## 1. Template Structure & Fields

### Section 1: Essential Property Information

#### 1.1 Basic Details (Required)
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `title` | String (200 chars) | Property listing headline | Required, min 10 chars |
| `summary` | Text (500 chars) | Brief description for cards/previews | Required, min 50 chars |
| `description` | Rich Text | Full property description | Required, min 200 chars |
| `listing_type` | Select | Sale, Option, Joint Venture, Lease | Required |
| `property_type` | Select | Claim, Lease, Fee Simple, Option, Permit | Required |

#### 1.2 Location (Required)
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `country` | Select | Country selection | Required |
| `province_state` | Select | Dynamic based on country | Required |
| `region_district` | String | Mining district/region | Optional |
| `nearest_town` | String | Closest community | Required |
| `coordinates_lat` | Decimal | GPS latitude | Optional, -90 to 90 |
| `coordinates_lng` | Decimal | GPS longitude | Optional, -180 to 180 |
| `access_description` | Text | How to access property | Required |
| `access_type` | Select | Year-round, Seasonal, Helicopter, etc. | Required |

**Supported Countries:** Canada, USA, Mexico, Australia, Brazil, Chile, Peru, Colombia, Argentina, South Africa, Ghana, Tanzania, DRC, Zambia, Namibia, Philippines, Indonesia, Papua New Guinea, Fiji, Other

**Canadian Provinces:** AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, QC, SK, YT

**US States:** AK, AZ, CA, CO, ID, MT, NV, NM, OR, SD, UT, WA, WY

#### 1.3 Legal Status & Claims
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `claim_numbers` | JSON Array | List of claim numbers | Optional |
| `total_claims` | Integer | Number of claims | Optional |
| `total_hectares` | Decimal | Property size in hectares | Auto-calculated |
| `total_acres` | Decimal | Property size in acres | Auto-calculated |
| `mineral_rights_type` | Select | Placer, Lode, Both | Required |
| `surface_rights_included` | Boolean | Surface rights included? | Required |
| `claim_status` | Select | Good Standing, Pending, Disputed | Required |
| `claim_expiry_date` | Date | When claims expire | Optional |
| `annual_holding_cost` | Decimal | Annual maintenance costs | Optional |

---

### Section 2: Geological/Mining Data

#### 2.1 Mineralization
| Field | Type | Description | Options |
|-------|------|-------------|---------|
| `primary_mineral` | Select | Main target mineral | Gold, Silver, Copper, Zinc, Lead, Nickel, Cobalt, Lithium, Platinum, Palladium, Uranium, Diamonds, REE, Iron, Molybdenum, Tungsten, Other |
| `secondary_minerals` | JSON Array | Additional minerals | Same as primary |
| `deposit_type` | Select | Deposit classification | Vein, Placer, Porphyry, VMS, SEDEX, Skarn, Epithermal, Orogenic, Carlin, IOCG, Intrusion-Related, Laterite, Podiform, Pegmatite, BIF, Alluvial, Other |
| `geological_setting` | Text | Geological context | Optional |
| `mineralization_style` | Text | Description of mineralization | Optional |

#### 2.2 Exploration Stage
| Stage | Description |
|-------|-------------|
| `grassroots` | Early-stage, minimal work completed |
| `early` | Some exploration, initial targets identified |
| `advanced` | Significant work, drill-ready targets |
| `development` | Resource defined, advancing toward production |
| `past_producer` | Former producing mine with known mineralization |

#### 2.3 Technical Data
| Field | Type | Description |
|-------|------|-------------|
| `work_completed` | JSON Array | List of exploration activities |
| `historical_production` | Text | Past production history |
| `assay_highlights` | JSON Array | Key assay results |
| `resource_estimate` | Text | Any resource calculations |
| `has_43_101_report` | Boolean | NI 43-101 technical report available |

**Work Completed Example Structure:**
```json
[
  {
    "type": "Geological Mapping",
    "date": "2023-06",
    "details": "1:5000 scale mapping of 500 hectares"
  },
  {
    "type": "Soil Sampling",
    "date": "2023-07",
    "details": "1,200 samples, 25m grid spacing"
  },
  {
    "type": "Diamond Drilling",
    "date": "2024-02",
    "details": "8 holes, 2,400m total"
  }
]
```

**Assay Highlights Example Structure:**
```json
[
  {
    "hole_id": "DDH-001",
    "from_m": 45.5,
    "to_m": 52.3,
    "width_m": 6.8,
    "au_gpt": 8.45,
    "ag_gpt": 125.0,
    "notes": "Including 2.1m @ 24.5 g/t Au"
  }
]
```

---

### Section 3: Financial Information

#### 3.1 Pricing
| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `asking_price` | Decimal | Listed price | Required for sales |
| `price_currency` | Select | CAD, USD, AUD | Default: CAD |
| `price_negotiable` | Boolean | Open to negotiation | Default: true |
| `minimum_offer` | Decimal | Minimum acceptable offer | Optional |

#### 3.2 Transaction Terms
| Field | Type | Description |
|-------|------|-------------|
| `option_terms` | Text | Option agreement terms |
| `joint_venture_terms` | Text | JV structure and earn-in |
| `lease_terms` | Text | Lease payment structure |
| `nsr_royalty` | Decimal (%) | Existing or required NSR |
| `includes_equipment` | Boolean | Equipment included in sale |
| `equipment_description` | Text | List of equipment if included |

#### 3.3 Encumbrances
- Existing NSR/NPI royalties
- Liens or mortgages
- Environmental liabilities
- Outstanding assessment work requirements

---

### Section 4: Transaction Terms Detail

#### 4.1 Sale Terms Template
```
ASKING PRICE: $[amount] [currency]
NEGOTIABLE: [Yes/No]
MINIMUM OFFER: $[amount]

INCLUDES:
- [X] All mineral claims (100%)
- [ ] Surface rights
- [ ] Camp and infrastructure
- [ ] Exploration data
- [ ] Equipment (list below)

EXISTING ENCUMBRANCES:
- NSR Royalty: [X]% to [holder]
- Back-in Rights: [details]
- Environmental bonds: $[amount]

CLOSING TIMELINE: [X] days from acceptance
```

#### 4.2 Option Agreement Template
```
OPTION PAYMENT STRUCTURE:
- Signing: $[amount]
- Year 1: $[amount]
- Year 2: $[amount]
- Year 3: $[amount]
- Final: $[amount]

TOTAL CONSIDERATION: $[amount]

WORK COMMITMENTS:
- Year 1: $[amount] minimum
- Year 2: $[amount] minimum
- Year 3: $[amount] minimum

EARN-IN: [X]% interest upon completion
BUYBACK: [details if applicable]
```

#### 4.3 Joint Venture Template
```
JV STRUCTURE:
- Initial Contribution: $[amount] for [X]% interest
- Earn-in: Spend $[amount] for additional [X]%
- Maximum Earn-in: [X]% interest

OPERATOR: [Prospector/Partner/TBD]
MANAGEMENT COMMITTEE: [X] members each party
DILUTION: Standard dilution provisions apply
```

---

### Section 5: Supporting Materials

#### 5.1 Media Types
| Type | Category | Purpose | Max Size |
|------|----------|---------|----------|
| Image | hero | Main listing image | 10MB |
| Image | gallery | Additional photos | 10MB each |
| Image | geological_map | Geological maps | 10MB |
| Image | claim_map | Claim boundary maps | 10MB |
| Image | location_map | Regional location | 10MB |
| Image | core_photo | Drill core photos | 10MB |
| Document | assay | Assay certificates | 25MB |
| Document | report | Technical reports | 50MB |
| Document | permit | Permits/licenses | 25MB |
| Video | video | Property videos | 100MB |

#### 5.2 Required vs Recommended Materials
**Required:**
- At least 1 hero image
- Location/claim map

**Highly Recommended:**
- 5+ gallery images
- Geological map
- Assay certificates for any reported results
- NI 43-101 report (if referenced)

**Optional but Valuable:**
- Drone footage/video
- Core photos
- Historical reports
- Permit documentation

---

### Section 6: Prospector Information

#### 6.1 Profile Fields
| Field | Type | Description |
|-------|------|-------------|
| `display_name` | String | Public display name |
| `company_name` | String | Company if applicable |
| `bio` | Text | Background and experience |
| `years_experience` | Integer | Years in industry |
| `specializations` | JSON Array | Areas of expertise |
| `regions_active` | JSON Array | Geographic focus areas |
| `certifications` | JSON Array | P.Geo, P.Eng, etc. |
| `website_url` | URL | Company/personal website |
| `phone` | String | Contact number |
| `profile_image_url` | URL | Profile photo |

#### 6.2 Verification & Trust Indicators
| Metric | Description |
|--------|-------------|
| `is_verified` | Platform-verified identity |
| `total_listings` | Number of properties listed |
| `active_listings` | Current active listings |
| `successful_transactions` | Completed deals |
| `average_rating` | Rating from past buyers |
| `avg_response_time` | Response time to inquiries |

---

## 2. UX Flow for Prospectors

### 2.1 Onboarding Flow

```
Step 1: Account Registration
├── Select user type: "Prospector"
├── Basic account creation
└── Email verification

Step 2: Profile Setup
├── Display name and bio
├── Years of experience
├── Specializations selection
├── Active regions
├── Certifications (optional)
├── Profile photo upload
└── Contact preferences

Step 3: Commission Agreement
├── Review 5% commission terms
├── Full agreement text display
├── Acknowledgment checkboxes
├── Digital signature
└── Agreement confirmation email
```

### 2.2 Listing Creation Wizard (8 Steps)

```
STEP 1: BASIC INFO
├── Listing title (compelling headline)
├── Listing type (Sale/Option/JV/Lease)
├── Property type
├── Summary (for cards)
└── Full description (rich text)

STEP 2: LOCATION
├── Country selection
├── Province/State (dynamic)
├── Region/District
├── Nearest town
├── GPS coordinates (map picker)
├── Access description
└── Access type

STEP 3: CLAIMS & RIGHTS
├── Claim numbers (add multiple)
├── Total claims
├── Hectares/Acres (auto-calc)
├── Mineral rights type
├── Surface rights included?
├── Claim status
├── Expiry date
└── Annual holding costs

STEP 4: GEOLOGY & MINERALS
├── Primary mineral target
├── Secondary minerals
├── Deposit type
├── Geological setting
├── Mineralization style
└── Exploration stage

STEP 5: TECHNICAL DATA
├── Work completed (add entries)
├── Historical production
├── Assay highlights (add entries)
├── Resource estimate
└── NI 43-101 available?

STEP 6: INFRASTRUCTURE
├── Camp facilities
├── Road access details
├── Power availability
├── Water sources
└── Equipment included

STEP 7: TRANSACTION TERMS
├── Asking price
├── Currency
├── Negotiable?
├── Minimum offer
├── Option/JV/Lease terms
├── NSR royalty
└── Equipment list

STEP 8: MEDIA & REVIEW
├── Upload hero image
├── Upload gallery images
├── Upload maps
├── Upload documents
├── Final review all sections
└── Submit for review
```

### 2.3 Draft & Save Functionality
- Auto-save every 30 seconds
- Manual "Save Draft" button
- Draft accessible from dashboard
- Resume from any step
- Drafts expire after 90 days

### 2.4 Listing Management Dashboard

```
MY LISTINGS
├── Active Listings
│   ├── Views count
│   ├── Inquiries count
│   ├── Watchlist adds
│   └── Quick actions (Edit, Pause, Feature)
├── Under Offer
│   └── Transaction status tracking
├── Drafts
│   └── Resume editing
├── Sold/Completed
│   └── Archive view
└── Expired/Withdrawn
    └── Re-list option
```

---

## 3. Display Format for Investors

### 3.1 Listing Card (Grid View)
```
┌─────────────────────────────────────┐
│ [HERO IMAGE]                        │
│ ┌───────────┐  ┌──────────────────┐ │
│ │ FEATURED  │  │ GOLD             │ │
│ └───────────┘  └──────────────────┘ │
├─────────────────────────────────────┤
│ Property Title Goes Here            │
│ Location, Province, Country         │
├─────────────────────────────────────┤
│ 📍 50 Claims  │  📐 2,500 Ha       │
│ 🔬 Advanced   │  👁 1,234 views    │
├─────────────────────────────────────┤
│ FOR SALE                            │
│ $2,500,000 CAD                      │
├─────────────────────────────────────┤
│ 👤 John Smith  │  Listed 5 days ago│
└─────────────────────────────────────┘
```

### 3.2 Full Listing Page Layout

```
┌─────────────────────────────────────────────────────────┐
│ HEADER                                                   │
│ [Back to Listings]                                       │
│ Property Title - Location, Province                      │
│ [Share] [Watchlist] [Print]                             │
├─────────────────────────────────────────────────────────┤
│ IMAGE GALLERY                                            │
│ ┌─────────────────────────────────────────┐             │
│ │                                         │             │
│ │          [MAIN IMAGE]                   │             │
│ │                                         │             │
│ └─────────────────────────────────────────┘             │
│ [thumb1] [thumb2] [thumb3] [thumb4] [thumb5]            │
├─────────────────────────────────────────────────────────┤
│ MAIN CONTENT                    │ SIDEBAR               │
│                                 │                       │
│ ┌─ OVERVIEW ─────────────────┐  │ ┌─ PRICING ────────┐  │
│ │ Summary text and key       │  │ │ $2,500,000 CAD   │  │
│ │ highlights                 │  │ │ [Negotiable]     │  │
│ │                            │  │ │                  │  │
│ │ Quick Stats:               │  │ │ [Contact Button] │  │
│ │ • 50 Claims / 2,500 Ha     │  │ │ [Schedule Visit] │  │
│ │ • Placer & Lode Rights     │  │ └──────────────────┘  │
│ │ • Surface Rights: Yes      │  │                       │
│ │ • Good Standing            │  │ ┌─ PROSPECTOR ─────┐  │
│ └────────────────────────────┘  │ │ [Photo]          │  │
│                                 │ │ John Smith       │  │
│ ┌─ GEOLOGY ──────────────────┐  │ │ ⭐ Verified      │  │
│ │ Primary: Gold              │  │ │ 15 yrs exp      │  │
│ │ Secondary: Silver, Copper  │  │ │ 12 listings     │  │
│ │ Deposit: Orogenic          │  │ │ Avg 4hr reply   │  │
│ │ Stage: Advanced            │  │ └──────────────────┘  │
│ │                            │  │                       │
│ │ Geological Setting:        │  │ ┌─ QUICK ACTIONS ──┐  │
│ │ [detailed description]     │  │ │ [Add to Watchlst]│  │
│ └────────────────────────────┘  │ │ [Download Pkg]   │  │
│                                 │ │ [Share Listing]  │  │
│ ┌─ EXPLORATION DATA ─────────┐  │ └──────────────────┘  │
│ │ Work Completed:            │  │                       │
│ │ • 2023: 8 DDH / 2,400m    │  │                       │
│ │ • 2022: Soil sampling     │  │                       │
│ │ • 2021: Geological mapping│  │                       │
│ │                            │  │                       │
│ │ Assay Highlights:         │  │                       │
│ │ ┌─────────────────────┐   │  │                       │
│ │ │ DDH-001: 6.8m @     │   │  │                       │
│ │ │ 8.45 g/t Au         │   │  │                       │
│ │ │ incl 2.1m @ 24.5 g/t│   │  │                       │
│ │ └─────────────────────┘   │  │                       │
│ └────────────────────────────┘  │                       │
│                                 │                       │
│ ┌─ LOCATION & ACCESS ────────┐  │                       │
│ │ [INTERACTIVE MAP]          │  │                       │
│ │                            │  │                       │
│ │ Access: Year-round road    │  │                       │
│ │ Nearest Town: Smithers, BC │  │                       │
│ └────────────────────────────┘  │                       │
│                                 │                       │
│ ┌─ TRANSACTION TERMS ────────┐  │                       │
│ │ Listing Type: Sale         │  │                       │
│ │ Price: $2,500,000 CAD      │  │                       │
│ │ NSR: 2% existing           │  │                       │
│ │ Includes: All data, camp   │  │                       │
│ └────────────────────────────┘  │                       │
│                                 │                       │
│ ┌─ DOCUMENTS ────────────────┐  │                       │
│ │ 📄 NI 43-101 Report (2024) │  │                       │
│ │ 📄 Assay Certificates      │  │                       │
│ │ 📄 Claim Map               │  │                       │
│ │ [Sign NDA to Access]       │  │                       │
│ └────────────────────────────┘  │                       │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Comparison View (Side-by-Side)
Allow investors to compare up to 3 properties:
- Side-by-side specifications
- Price comparison
- Size/claims comparison
- Exploration stage comparison
- Export comparison to PDF

### 3.4 Search & Filter Options

**Filter Categories:**
1. **Mineral Type** - Multi-select checkboxes
2. **Country/Region** - Cascading dropdowns
3. **Exploration Stage** - Checkboxes
4. **Price Range** - Dual slider
5. **Property Size** - Dual slider (hectares)
6. **Listing Type** - Sale/Option/JV/Lease
7. **Property Type** - Claim/Lease/Fee Simple
8. **Has NI 43-101** - Checkbox
9. **Open to Offers** - Checkbox

**Sort Options:**
- Newest First
- Price: Low to High
- Price: High to Low
- Size: Largest First
- Most Viewed
- Recently Updated

---

## 4. Promotion Recommendations

### 4.1 Featured Listings Program
```
FEATURED LISTING TIERS:

BASIC (Free)
├── Standard search placement
├── 10 photos max
└── Basic analytics

SPOTLIGHT ($99/month)
├── Highlighted in search results
├── "Spotlight" badge
├── 25 photos
├── Enhanced analytics
└── Priority in category pages

PREMIUM ($249/month)
├── Top of search results
├── Homepage rotation
├── "Premium" badge
├── Unlimited photos
├── Full analytics dashboard
├── Social media promotion
└── Newsletter feature (1x/month)

PLATINUM ($499/month)
├── All Premium features
├── Dedicated landing page
├── Video hosting
├── Custom URL
├── Priority support
├── Newsletter feature (2x/month)
└── Investor email blast (1x/month)
```

### 4.2 Visibility Boosters
| Booster | Price | Effect | Duration |
|---------|-------|--------|----------|
| Bump to Top | $25 | Return to top of listings | 24 hours |
| Highlight | $15 | Yellow highlight in results | 7 days |
| Bold Title | $10 | Bold listing title | 14 days |
| Urgent Badge | $35 | "Hot Property" badge | 7 days |

### 4.3 Marketing Channels
1. **Email Newsletters**
   - Weekly "New Listings" digest
   - Monthly "Featured Properties" showcase
   - Targeted alerts based on saved searches

2. **Social Media**
   - Automated LinkedIn posts for Premium listings
   - Twitter/X property highlights
   - Instagram gallery posts

3. **Partner Networks**
   - Mining news site partnerships
   - Investment forum placements
   - Industry conference promotions

---

## 5. Monetization Recommendations

### 5.1 Revenue Streams

#### Primary: Transaction Commission (5%)
```
Commission Structure:
├── 5% of final transaction value
├── Minimum: $500
├── Maximum: $50,000
├── Payment: Due at closing
└── Split: 100% to platform (prospector pays)
```

#### Secondary: Subscription Tiers

**Prospector Plans:**
| Plan | Monthly | Annual | Features |
|------|---------|--------|----------|
| Free | $0 | $0 | 3 active listings |
| Pro | $49 | $490 | 15 listings, analytics |
| Business | $149 | $1,490 | Unlimited, priority support |

**Investor Plans:**
| Plan | Monthly | Annual | Features |
|------|---------|--------|----------|
| Free | $0 | $0 | Basic search, 5 saved |
| Premium | $29 | $290 | Advanced filters, alerts |
| Professional | $99 | $990 | API access, bulk export |

### 5.2 Value-Added Services

| Service | Price | Description |
|---------|-------|-------------|
| NDA Processing | $25 | Platform-managed NDAs |
| Escrow Service | 1% | Secure transaction escrow |
| Due Diligence Pack | $199 | Standardized DD checklist |
| Valuation Estimate | $499 | AI-assisted valuation |
| Virtual Data Room | $149/mo | Secure document sharing |
| Transaction Support | $999 | Full transaction coordination |

### 5.3 Advertising Revenue
- Banner ads: $500-2000/month CPM
- Sponsored search results: $2-5 CPC
- Newsletter sponsorship: $500/issue
- Webinar sponsorship: $1,500/event

### 5.4 Data & Analytics Products
- Market reports: $199-499 each
- Price index subscription: $99/month
- API access for institutions: $499/month
- Custom analytics: Enterprise pricing

---

## 6. Implementation Priorities

### Phase 1: Core Template (Current)
- [x] PropertyListing model with all fields
- [x] 8-step listing wizard
- [x] Basic search and filters
- [x] Property detail page
- [x] Inquiry system
- [x] Commission agreement flow

### Phase 2: Enhanced Features
- [ ] Comparison tool
- [ ] Saved searches with alerts
- [ ] Email notifications
- [ ] Mobile app optimization
- [ ] Advanced analytics dashboard

### Phase 3: Monetization
- [ ] Featured listings program
- [ ] Subscription tiers
- [ ] Payment processing integration
- [ ] Escrow service
- [ ] Virtual data room

### Phase 4: Growth
- [ ] API for partners
- [ ] Mobile apps
- [ ] International expansion
- [ ] AI-powered recommendations
- [ ] Automated valuation tools

---

## 7. Technical Implementation Notes

### API Endpoints (Existing)
```
GET    /api/properties/listings/          # List all properties
POST   /api/properties/listings/          # Create new listing
GET    /api/properties/listings/{id}/     # Get property detail
PUT    /api/properties/listings/{id}/     # Update listing
DELETE /api/properties/listings/{id}/     # Delete listing
POST   /api/properties/listings/{id}/record_view/  # Track view

GET    /api/properties/prospectors/       # List prospectors
GET    /api/properties/prospectors/me/    # Current user profile
POST   /api/properties/prospectors/accept_agreement/  # Accept commission

GET    /api/properties/inquiries/         # List inquiries
POST   /api/properties/inquiries/         # Send inquiry

GET    /api/properties/watchlist/         # User's watchlist
POST   /api/properties/watchlist/         # Add to watchlist
```

### Frontend Components (Existing)
- `PropertyCard.tsx` - Grid listing card
- `PropertyFilters.tsx` - Search sidebar
- `InquiryForm.tsx` - Contact modal

### Database Schema
See `backend/core/models.py` lines 1717-2250 for complete model definitions.

---

## Appendix A: Field Validation Rules

| Field | Rule |
|-------|------|
| title | 10-200 chars, no special chars |
| summary | 50-500 chars |
| description | 200-10000 chars |
| asking_price | > 0, max 999,999,999 |
| total_hectares | > 0, max 1,000,000 |
| coordinates_lat | -90 to 90 |
| coordinates_lng | -180 to 180 |
| nsr_royalty | 0-25% |
| claim_numbers | Valid claim format per jurisdiction |

## Appendix B: Status Workflow

```
DRAFT → PENDING_REVIEW → ACTIVE → UNDER_OFFER → SOLD
                ↓           ↓          ↓
            REJECTED    WITHDRAWN   EXPIRED
```

## Appendix C: Commission Agreement Text

The full commission agreement is stored in the database and includes:
- 5% transaction fee acknowledgment
- Payment terms (due at closing)
- Prospector responsibilities
- Platform responsibilities
- Dispute resolution
- Termination clauses
- Legal jurisdiction

See `ProspectorCommissionAgreement` model for current agreement text.
