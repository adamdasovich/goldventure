# Prospector Property Exchange - Architecture & Implementation Plan

## Executive Summary

A comprehensive marketplace for mining property transactions, connecting prospectors with investors and mining companies. The platform enables prospectors to list their mineral claims with rich media documentation while providing investors with powerful search and evaluation tools.

---

## 1. Data Architecture

### 1.1 Database Models

#### User Extension - Prospector Profile
```
ProspectorProfile
├── user (OneToOne → User)
├── display_name (CharField)
├── company_name (CharField, optional)
├── bio (TextField)
├── years_experience (IntegerField)
├── specializations (JSONField) - ["gold", "silver", "copper"]
├── regions_active (JSONField) - ["British Columbia", "Ontario"]
├── certifications (JSONField) - [{name, issuer, year}]
├── website_url (URLField, optional)
├── phone (CharField, optional)
├── is_verified (BooleanField)
├── verification_date (DateTimeField)
├── profile_image_url (URLField)
├── total_listings (IntegerField, denormalized)
├── successful_transactions (IntegerField, denormalized)
├── average_rating (DecimalField)
├── created_at (DateTimeField)
└── updated_at (DateTimeField)
```

#### Core Property Listing Model
```
PropertyListing
├── id (AutoField)
├── prospector (ForeignKey → ProspectorProfile)
├── slug (SlugField, unique)
│
├── # Basic Information
├── title (CharField, 200)
├── summary (TextField, 500 chars max)
├── description (TextField)
├── property_type (CharField) - claim/lease/fee_simple/option
│
├── # Location
├── country (CharField) - ISO country code
├── province_state (CharField)
├── region_district (CharField)
├── nearest_town (CharField)
├── coordinates_lat (DecimalField)
├── coordinates_lng (DecimalField)
├── access_description (TextField)
├── access_type (CharField) - road/fly_in/boat/combination
│
├── # Claim Details
├── claim_numbers (JSONField) - ["123456", "123457"]
├── total_claims (IntegerField)
├── total_hectares (DecimalField)
├── total_acres (DecimalField, computed)
├── mineral_rights_type (CharField) - placer/lode/both
├── surface_rights_included (BooleanField)
├── claim_status (CharField) - active/pending/expiring
├── claim_expiry_date (DateField, optional)
├── annual_holding_cost (DecimalField)
│
├── # Minerals & Geology
├── primary_mineral (CharField) - gold/silver/copper/etc
├── secondary_minerals (JSONField) - ["silver", "lead"]
├── deposit_type (CharField) - vein/placer/porphyry/vms/etc
├── geological_setting (TextField)
├── mineralization_style (CharField)
│
├── # Exploration Status
├── exploration_stage (CharField) - grassroots/early/advanced/development
├── work_completed (JSONField) - [{type, date, summary}]
├── historical_production (TextField, optional)
├── assay_highlights (JSONField) - [{sample_id, mineral, grade, unit}]
├── resource_estimate (TextField, optional)
├── has_43_101_report (BooleanField)
│
├── # Transaction Terms
├── listing_type (CharField) - sale/option/joint_venture/lease
├── asking_price (DecimalField, optional)
├── price_currency (CharField) - CAD/USD
├── price_negotiable (BooleanField)
├── minimum_offer (DecimalField, optional)
├── option_terms (TextField, optional)
├── joint_venture_terms (TextField, optional)
├── lease_terms (TextField, optional)
├── nsr_royalty (DecimalField, optional) - percentage
├── includes_equipment (BooleanField)
├── equipment_description (TextField, optional)
│
├── # Status & Visibility
├── status (CharField) - draft/pending_review/active/under_offer/sold/withdrawn
├── is_featured (BooleanField)
├── featured_until (DateTimeField, optional)
├── views_count (IntegerField)
├── inquiries_count (IntegerField)
├── watchlist_count (IntegerField)
│
├── # Timestamps
├── created_at (DateTimeField)
├── updated_at (DateTimeField)
├── published_at (DateTimeField, optional)
└── expires_at (DateTimeField, optional)
```

#### Property Media & Documents
```
PropertyMedia
├── id (AutoField)
├── listing (ForeignKey → PropertyListing)
├── media_type (CharField) - image/video/document/map
├── category (CharField) - hero/gallery/geological_map/claim_map/assay/report/other
├── title (CharField)
├── description (TextField, optional)
├── file_url (URLField)
├── thumbnail_url (URLField, optional)
├── file_size_mb (DecimalField)
├── file_format (CharField)
├── sort_order (IntegerField)
├── is_primary (BooleanField) - for hero image
├── uploaded_at (DateTimeField)
└── uploaded_by (ForeignKey → User)
```

#### Inquiry & Communication
```
PropertyInquiry
├── id (AutoField)
├── listing (ForeignKey → PropertyListing)
├── inquirer (ForeignKey → User)
├── inquiry_type (CharField) - general/site_visit/offer/information_request
├── message (TextField)
├── contact_preference (CharField) - email/phone/either
├── status (CharField) - new/read/responded/closed
├── response (TextField, optional)
├── responded_at (DateTimeField, optional)
├── created_at (DateTimeField)
└── is_nda_signed (BooleanField)
```

#### Saved Searches & Watchlist
```
PropertyWatchlist
├── user (ForeignKey → User)
├── listing (ForeignKey → PropertyListing)
├── notes (TextField, optional)
├── price_alert (BooleanField)
├── added_at (DateTimeField)
└── Meta: unique_together = ['user', 'listing']

SavedPropertySearch
├── user (ForeignKey → User)
├── name (CharField)
├── search_criteria (JSONField)
├── email_alerts (BooleanField)
├── alert_frequency (CharField) - instant/daily/weekly
├── created_at (DateTimeField)
└── last_alerted_at (DateTimeField, optional)
```

### 1.2 Choice Constants

```python
PROPERTY_TYPES = [
    ('claim', 'Mineral Claim'),
    ('lease', 'Mining Lease'),
    ('fee_simple', 'Fee Simple'),
    ('option', 'Option Agreement'),
    ('permit', 'Exploration Permit'),
]

MINERAL_TYPES = [
    ('gold', 'Gold'),
    ('silver', 'Silver'),
    ('copper', 'Copper'),
    ('zinc', 'Zinc'),
    ('lead', 'Lead'),
    ('nickel', 'Nickel'),
    ('cobalt', 'Cobalt'),
    ('lithium', 'Lithium'),
    ('uranium', 'Uranium'),
    ('rare_earth', 'Rare Earth Elements'),
    ('platinum', 'Platinum Group'),
    ('diamonds', 'Diamonds'),
    ('other', 'Other'),
]

MINERAL_RIGHTS_TYPES = [
    ('placer', 'Placer'),
    ('lode', 'Lode/Hardrock'),
    ('both', 'Both Placer & Lode'),
]

DEPOSIT_TYPES = [
    ('vein', 'Vein/Lode'),
    ('placer', 'Placer'),
    ('porphyry', 'Porphyry'),
    ('vms', 'VMS (Volcanogenic Massive Sulfide)'),
    ('sedex', 'SEDEX'),
    ('skarn', 'Skarn'),
    ('epithermal', 'Epithermal'),
    ('orogenic', 'Orogenic'),
    ('iocg', 'IOCG'),
    ('mvt', 'MVT'),
    ('laterite', 'Laterite'),
    ('bif', 'BIF (Banded Iron Formation)'),
    ('other', 'Other'),
]

EXPLORATION_STAGES = [
    ('grassroots', 'Grassroots'),
    ('early', 'Early Stage'),
    ('advanced', 'Advanced'),
    ('development', 'Development Ready'),
    ('past_producer', 'Past Producer'),
]

LISTING_TYPES = [
    ('sale', 'Outright Sale'),
    ('option', 'Option to Purchase'),
    ('joint_venture', 'Joint Venture'),
    ('lease', 'Lease'),
]

LISTING_STATUS = [
    ('draft', 'Draft'),
    ('pending_review', 'Pending Review'),
    ('active', 'Active'),
    ('under_offer', 'Under Offer'),
    ('sold', 'Sold'),
    ('withdrawn', 'Withdrawn'),
    ('expired', 'Expired'),
]

COUNTRIES_WITH_MINING = [
    ('CA', 'Canada'),
    ('US', 'United States'),
    ('AU', 'Australia'),
    ('MX', 'Mexico'),
    ('PE', 'Peru'),
    ('CL', 'Chile'),
    ('AR', 'Argentina'),
    ('BR', 'Brazil'),
    ('CO', 'Colombia'),
    ('ZA', 'South Africa'),
    ('GH', 'Ghana'),
    ('ML', 'Mali'),
    ('BF', 'Burkina Faso'),
    ('CD', 'DRC'),
    ('ZM', 'Zambia'),
    ('PH', 'Philippines'),
    ('ID', 'Indonesia'),
    ('CN', 'China'),
    ('MN', 'Mongolia'),
]

CANADIAN_PROVINCES = [
    ('BC', 'British Columbia'),
    ('AB', 'Alberta'),
    ('SK', 'Saskatchewan'),
    ('MB', 'Manitoba'),
    ('ON', 'Ontario'),
    ('QC', 'Quebec'),
    ('NB', 'New Brunswick'),
    ('NS', 'Nova Scotia'),
    ('NL', 'Newfoundland and Labrador'),
    ('PE', 'Prince Edward Island'),
    ('YT', 'Yukon'),
    ('NT', 'Northwest Territories'),
    ('NU', 'Nunavut'),
]
```

---

## 2. API Endpoints Design

### 2.1 Prospector Profile Endpoints

```
GET    /api/prospectors/                    # List all prospectors (public profiles)
GET    /api/prospectors/{id}/               # Get prospector detail
GET    /api/prospectors/{id}/listings/      # Get prospector's listings
POST   /api/prospectors/register/           # Register as prospector
PUT    /api/prospectors/me/                 # Update own profile
GET    /api/prospectors/me/                 # Get own profile
POST   /api/prospectors/me/verify/          # Request verification
```

### 2.2 Property Listing Endpoints

```
GET    /api/properties/                     # List properties (with filters)
GET    /api/properties/{slug}/              # Get property detail
POST   /api/properties/                     # Create listing (prospector only)
PUT    /api/properties/{slug}/              # Update listing (owner only)
DELETE /api/properties/{slug}/              # Soft delete (owner only)
POST   /api/properties/{slug}/publish/      # Submit for review
POST   /api/properties/{slug}/withdraw/     # Withdraw listing
GET    /api/properties/{slug}/similar/      # Get similar properties
POST   /api/properties/{slug}/view/         # Record view (increment counter)

# Media Management
GET    /api/properties/{slug}/media/        # List media for property
POST   /api/properties/{slug}/media/        # Upload media
PUT    /api/properties/{slug}/media/{id}/   # Update media metadata
DELETE /api/properties/{slug}/media/{id}/   # Delete media
POST   /api/properties/{slug}/media/reorder/ # Reorder media
```

### 2.3 Search & Discovery Endpoints

```
GET    /api/properties/search/              # Advanced search with filters
GET    /api/properties/featured/            # Featured listings
GET    /api/properties/recent/              # Recent listings
GET    /api/properties/by-mineral/{mineral}/ # Filter by mineral
GET    /api/properties/by-region/{region}/  # Filter by region
GET    /api/properties/map/                 # Get properties for map view
```

### 2.4 Inquiry & Communication Endpoints

```
POST   /api/properties/{slug}/inquire/      # Submit inquiry
GET    /api/inquiries/                      # List user's inquiries
GET    /api/inquiries/received/             # Prospector's received inquiries
PUT    /api/inquiries/{id}/respond/         # Respond to inquiry
PUT    /api/inquiries/{id}/status/          # Update inquiry status
```

### 2.5 Watchlist & Saved Searches

```
GET    /api/watchlist/                      # User's watchlist
POST   /api/watchlist/                      # Add to watchlist
DELETE /api/watchlist/{listing_id}/         # Remove from watchlist
GET    /api/saved-searches/                 # User's saved searches
POST   /api/saved-searches/                 # Create saved search
PUT    /api/saved-searches/{id}/            # Update saved search
DELETE /api/saved-searches/{id}/            # Delete saved search
```

### 2.6 Query Parameters for Search

```
GET /api/properties/?
    # Location filters
    country=CA
    province=BC,ON
    region=Cariboo
    lat=51.5&lng=-120.5&radius=50  # km radius search

    # Mineral filters
    primary_mineral=gold
    minerals=gold,silver,copper
    deposit_type=vein,placer

    # Property filters
    property_type=claim
    mineral_rights=placer
    min_hectares=100
    max_hectares=1000
    has_surface_rights=true

    # Stage & Status
    exploration_stage=advanced
    has_43_101=true

    # Price filters
    listing_type=sale
    min_price=50000
    max_price=500000
    currency=CAD

    # Sorting
    ordering=-created_at  # newest first
    ordering=asking_price  # price low to high
    ordering=-views_count  # most viewed

    # Pagination
    page=1
    page_size=20

    # Text search
    search=gold+cariboo+placer
```

---

## 3. Frontend Architecture

### 3.1 Route Structure

```
/property-exchange/                         # Main landing/search page
/property-exchange/search                   # Advanced search
/property-exchange/map                      # Map-based search
/property-exchange/listings/{slug}          # Property detail page
/property-exchange/prospectors              # Browse prospectors
/property-exchange/prospectors/{id}         # Prospector profile page

# Authenticated Routes
/property-exchange/dashboard                # User dashboard
/property-exchange/my-listings              # Prospector's listings
/property-exchange/my-listings/create       # Create new listing
/property-exchange/my-listings/{slug}/edit  # Edit listing
/property-exchange/my-inquiries             # User's sent inquiries
/property-exchange/received-inquiries       # Prospector's received inquiries
/property-exchange/watchlist                # User's watchlist
/property-exchange/saved-searches           # User's saved searches
/property-exchange/profile                  # Prospector profile settings
```

### 3.2 Component Architecture

```
components/property-exchange/
├── PropertyCard.tsx              # Listing card for grid/list views
├── PropertyCardSkeleton.tsx      # Loading skeleton
├── PropertyGrid.tsx              # Grid layout wrapper
├── PropertyList.tsx              # List layout wrapper
├── PropertyMap.tsx               # Map view with markers
├── PropertyMapMarker.tsx         # Custom map marker
├── PropertyFilters.tsx           # Filter sidebar
├── PropertySearchBar.tsx         # Main search input
├── PropertySort.tsx              # Sort dropdown
├── PropertyHero.tsx              # Property detail hero section
├── PropertyGallery.tsx           # Image gallery with lightbox
├── PropertyDetails.tsx           # Property specifications
├── PropertyLocation.tsx          # Location map & info
├── PropertyDocuments.tsx         # Document list & viewer
├── PropertyInquiryForm.tsx       # Contact form
├── PropertySimilar.tsx           # Similar listings carousel
├── ProspectorCard.tsx            # Prospector summary card
├── ProspectorProfile.tsx         # Full prospector profile
├── ProspectorListings.tsx        # Prospector's listings grid
├── WatchlistButton.tsx           # Add/remove watchlist
├── ShareButton.tsx               # Social sharing
├── ListingForm/                  # Multi-step listing form
│   ├── BasicInfoStep.tsx
│   ├── LocationStep.tsx
│   ├── ClaimDetailsStep.tsx
│   ├── MineralsStep.tsx
│   ├── ExplorationStep.tsx
│   ├── TermsStep.tsx
│   ├── MediaStep.tsx
│   └── ReviewStep.tsx
├── DashboardStats.tsx            # Dashboard metrics
├── InquiryList.tsx               # Inquiry management
├── InquiryThread.tsx             # Inquiry conversation
└── SavedSearchCard.tsx           # Saved search display
```

### 3.3 Page Layouts

#### Main Search Page (`/property-exchange`)
```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  Property Exchange   [Search Bar]   [Login/Profile] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Hero Section                      │   │
│  │  "Discover Mining Properties Across Canada"          │   │
│  │  [Quick Filters: Gold | Silver | British Columbia]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Featured Properties                          [View All →]  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Property │ │ Property │ │ Property │ │ Property │       │
│  │   Card   │ │   Card   │ │   Card   │ │   Card   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                             │
│  Browse by Mineral                                          │
│  [Gold] [Silver] [Copper] [Lithium] [Rare Earth] [More]    │
│                                                             │
│  Browse by Region                                           │
│  [British Columbia] [Ontario] [Quebec] [Yukon] [More]      │
│                                                             │
│  Recent Listings                              [View All →]  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Property │ │ Property │ │ Property │ │ Property │       │
│  │   Card   │ │   Card   │ │   Card   │ │   Card   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  CTA: "List Your Property"                          │   │
│  │  Join hundreds of prospectors reaching investors    │   │
│  │  [Get Started - It's Free]                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Search Results Page (`/property-exchange/search`)
```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  Property Exchange   [Search Bar]   [Login/Profile] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │   Filters    │  │  Results (47 properties)           │  │
│  │              │  │  [Grid] [List] [Map]  Sort: [▼]    │  │
│  │ Location     │  │                                    │  │
│  │ [Country ▼]  │  │  ┌──────────┐ ┌──────────┐        │  │
│  │ [Province ▼] │  │  │ Property │ │ Property │        │  │
│  │              │  │  │   Card   │ │   Card   │        │  │
│  │ Minerals     │  │  └──────────┘ └──────────┘        │  │
│  │ [x] Gold     │  │  ┌──────────┐ ┌──────────┐        │  │
│  │ [ ] Silver   │  │  │ Property │ │ Property │        │  │
│  │ [ ] Copper   │  │  │   Card   │ │   Card   │        │  │
│  │              │  │  └──────────┘ └──────────┘        │  │
│  │ Property     │  │                                    │  │
│  │ [Type ▼]     │  │  [Load More / Pagination]         │  │
│  │              │  │                                    │  │
│  │ Price        │  └────────────────────────────────────┘  │
│  │ [$___-$___]  │                                          │
│  │              │                                          │
│  │ Size         │                                          │
│  │ [___-___ ha] │                                          │
│  │              │                                          │
│  │ Stage        │                                          │
│  │ [ ] Grassrts │                                          │
│  │ [x] Advanced │                                          │
│  │              │                                          │
│  │ [Clear All]  │                                          │
│  │ [Save Search]│                                          │
│  └──────────────┘                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Property Detail Page (`/property-exchange/listings/{slug}`)
```
┌─────────────────────────────────────────────────────────────┐
│  [← Back]  Property Exchange              [Login/Profile]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Hero Image                        │   │
│  │  [Gallery: 1/12]                    [♡] [Share]     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────┐ ┌──────────────────────┐   │
│  │                            │ │  Price & Action      │   │
│  │  Golden Valley Claims      │ │  ────────────────    │   │
│  │  Cariboo, British Columbia │ │  $450,000 CAD        │   │
│  │                            │ │  (Negotiable)        │   │
│  │  [Gold] [Placer] [Advanced]│ │                      │   │
│  │                            │ │  Listing Type: Sale  │   │
│  │  12 Claims • 450 Hectares  │ │  NSR Royalty: 2%     │   │
│  │                            │ │                      │   │
│  │  Listed by:                │ │  [Contact Seller]    │   │
│  │  ┌────┐ John Smith         │ │  [Add to Watchlist]  │   │
│  │  │ 👤 │ Verified Prospector│ │  [Download Info]     │   │
│  │  └────┘ [View Profile →]   │ │                      │   │
│  │                            │ └──────────────────────┘   │
│  └────────────────────────────┘                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [Overview] [Location] [Claims] [Exploration] [Docs]│   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                     │   │
│  │  Description                                        │   │
│  │  ─────────────                                      │   │
│  │  This exceptional placer gold property features     │   │
│  │  12 contiguous claims along historic gold-bearing  │   │
│  │  creeks in the heart of the Cariboo gold region... │   │
│  │                                                     │   │
│  │  Key Highlights                                     │   │
│  │  ─────────────                                      │   │
│  │  • Historical production of 50,000+ oz             │   │
│  │  • Road accessible, 45 min from Quesnel           │   │
│  │  • Multiple high-grade assays (up to 15 g/t Au)   │   │
│  │  • NI 43-101 compliant resource estimate          │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Similar Properties                           [View All →]  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ Property │ │ Property │ │ Property │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Multi-Step Listing Form Design

### Step 1: Basic Information
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Listing                    Step 1 of 8         │
│  ━━━━━━━━○○○○○○○○                                          │
│                                                             │
│  Basic Information                                          │
│  ─────────────────                                          │
│                                                             │
│  Property Title *                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Golden Valley Placer Claims                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Short Summary * (max 200 chars)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 12 contiguous placer gold claims in historic        │   │
│  │ Cariboo region with proven gold recovery...         │   │
│  └─────────────────────────────────────────────────────┘   │
│  145/200 characters                                         │
│                                                             │
│  Full Description *                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │ Rich text editor with formatting options            │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Property Type *                                            │
│  ○ Mineral Claim    ○ Mining Lease    ○ Fee Simple         │
│  ○ Option Agreement ○ Exploration Permit                   │
│                                                             │
│                               [Save Draft]  [Next →]       │
└─────────────────────────────────────────────────────────────┘
```

### Step 2: Location
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Listing                    Step 2 of 8         │
│  ━━━━━━━━━━○○○○○○○                                         │
│                                                             │
│  Location Details                                           │
│  ────────────────                                           │
│                                                             │
│  Country *                    Province/State *              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ Canada        ▼  │         │ British Columbia▼│         │
│  └──────────────────┘         └──────────────────┘         │
│                                                             │
│  Region/District              Nearest Town                  │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ Cariboo          │         │ Quesnel          │         │
│  └──────────────────┘         └──────────────────┘         │
│                                                             │
│  Coordinates (click map or enter manually)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │              [Interactive Map]                      │   │
│  │                     📍                              │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  Latitude: [52.9784]      Longitude: [-122.4927]           │
│                                                             │
│  Access Description                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 45 km from Quesnel via Highway 97, then 12 km on   │   │
│  │ well-maintained gravel forestry road...             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Access Type *                                              │
│  ● Road Accessible  ○ Fly-in Only  ○ Boat  ○ Combination  │
│                                                             │
│                      [← Back]  [Save Draft]  [Next →]      │
└─────────────────────────────────────────────────────────────┘
```

### Step 3: Claim Details
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Listing                    Step 3 of 8         │
│  ━━━━━━━━━━━━━━○○○○○                                       │
│                                                             │
│  Claim Details                                              │
│  ─────────────                                              │
│                                                             │
│  Claim Numbers (one per line or comma-separated)           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1234567                                             │   │
│  │ 1234568                                             │   │
│  │ 1234569                                             │   │
│  └─────────────────────────────────────────────────────┘   │
│  12 claims entered                                          │
│                                                             │
│  Total Area                                                 │
│  Hectares: [450]          Acres: [1,112] (auto-calculated) │
│                                                             │
│  Mineral Rights Type *                                      │
│  ○ Placer    ● Lode/Hardrock    ○ Both                     │
│                                                             │
│  Surface Rights Included? *                                 │
│  ● Yes    ○ No    ○ Partial (describe below)               │
│                                                             │
│  Claim Status *                                             │
│  ● Active    ○ Pending Renewal    ○ Expiring Soon          │
│                                                             │
│  Claim Expiry Date (if applicable)                         │
│  ┌──────────────────┐                                      │
│  │ 2025-12-31       │                                      │
│  └──────────────────┘                                      │
│                                                             │
│  Annual Holding Cost (assessment work, fees, etc.)         │
│  $ ┌──────────┐ CAD per year                               │
│    │ 5,400    │                                            │
│    └──────────┘                                            │
│                                                             │
│                      [← Back]  [Save Draft]  [Next →]      │
└─────────────────────────────────────────────────────────────┘
```

### Step 4: Minerals & Geology
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Listing                    Step 4 of 8         │
│  ━━━━━━━━━━━━━━━━━━○○○○                                    │
│                                                             │
│  Minerals & Geology                                         │
│  ──────────────────                                         │
│                                                             │
│  Primary Target Mineral *                                   │
│  ┌──────────────────┐                                      │
│  │ Gold          ▼  │                                      │
│  └──────────────────┘                                      │
│                                                             │
│  Secondary Minerals (select all that apply)                │
│  [x] Silver    [ ] Copper    [ ] Zinc    [ ] Lead          │
│  [ ] Nickel    [ ] Cobalt    [ ] PGE     [ ] Other         │
│                                                             │
│  Deposit Type *                                             │
│  ┌──────────────────────────────────────┐                  │
│  │ Placer                            ▼  │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  Mineralization Style                                       │
│  ┌──────────────────────────────────────┐                  │
│  │ Coarse free gold in gravels       ▼  │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
│  Geological Setting                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Property lies within the historic Cariboo gold belt │   │
│  │ along paleochannel gravels derived from nearby      │   │
│  │ orogenic gold systems...                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                      [← Back]  [Save Draft]  [Next →]      │
└─────────────────────────────────────────────────────────────┘
```

### Step 5: Exploration History
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Listing                    Step 5 of 8         │
│  ━━━━━━━━━━━━━━━━━━━━━○○○                                  │
│                                                             │
│  Exploration & History                                      │
│  ─────────────────────                                      │
│                                                             │
│  Exploration Stage *                                        │
│  ○ Grassroots    ○ Early Stage    ● Advanced               │
│  ○ Development Ready    ○ Past Producer                    │
│                                                             │
│  Work Completed (add multiple)                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Type: [Sampling ▼]  Year: [2023]                   │    │
│  │ Summary: [Collected 250 pan samples across claims] │    │
│  │                                        [+ Add More]│    │
│  ├────────────────────────────────────────────────────┤    │
│  │ ✓ Sampling - 2023: Collected 250 pan samples...   │    │
│  │ ✓ Trenching - 2022: 12 test trenches revealing... │    │
│  │ ✓ Drilling - 2021: 15 RC holes totaling 1,200m... │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Historical Production (if applicable)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Property produced approximately 50,000 oz gold      │   │
│  │ between 1885-1942 via hydraulic mining methods...   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Assay Highlights (add best results)                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Sample ID │ Mineral │ Grade │ Unit │               │   │
│  │ TR-23-001 │ Gold    │ 15.2  │ g/t  │ [Delete]      │   │
│  │ TR-23-007 │ Gold    │ 8.7   │ g/t  │ [Delete]      │   │
│  │ [Add Sample]                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  NI 43-101 Technical Report? *                             │
│  ● Yes    ○ No                                             │
│                                                             │
│  Resource Estimate (if available)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Inferred resource of 125,000 oz Au at average      │   │
│  │ grade of 1.2 g/t Au...                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                      [← Back]  [Save Draft]  [Next →]      │
└─────────────────────────────────────────────────────────────┘
```

### Step 6: Transaction Terms
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Listing                    Step 6 of 8         │
│  ━━━━━━━━━━━━━━━━━━━━━━━○○                                 │
│                                                             │
│  Transaction Terms                                          │
│  ─────────────────                                          │
│                                                             │
│  Listing Type *                                             │
│  ● Outright Sale    ○ Option to Purchase                   │
│  ○ Joint Venture    ○ Lease                                │
│                                                             │
│  ── Sale Terms ──────────────────────────────────────────  │
│                                                             │
│  Asking Price *                   Currency *                │
│  $ ┌──────────────┐              ┌────────┐                │
│    │ 450,000      │              │ CAD ▼  │                │
│    └──────────────┘              └────────┘                │
│                                                             │
│  [x] Price is Negotiable                                   │
│                                                             │
│  Minimum Acceptable Offer (optional)                        │
│  $ ┌──────────────┐                                        │
│    │ 350,000      │                                        │
│    └──────────────┘                                        │
│                                                             │
│  NSR Royalty to be Retained (optional)                     │
│  ┌──────────────┐ %                                        │
│  │ 2.0          │                                          │
│  └──────────────┘                                          │
│                                                             │
│  Includes Equipment? *                                      │
│  ○ Yes    ● No                                             │
│                                                             │
│  Additional Terms or Conditions                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Buyer to assume all assessment work obligations     │   │
│  │ from closing date. Environmental baseline data     │   │
│  │ available upon request...                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                      [← Back]  [Save Draft]  [Next →]      │
└─────────────────────────────────────────────────────────────┘
```

### Step 7: Media & Documents
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Listing                    Step 7 of 8         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━○                               │
│                                                             │
│  Media & Documents                                          │
│  ─────────────────                                          │
│                                                             │
│  Property Photos * (at least 1 required)                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────┐  │   │
│  │  │  📷    │ │  📷    │ │  📷    │ │    + Add    │  │   │
│  │  │ Hero   │ │ Site   │ │ Sample │ │    Photo    │  │   │
│  │  │ ★      │ │        │ │        │ │             │  │   │
│  │  └────────┘ └────────┘ └────────┘ └─────────────┘  │   │
│  │  Drag to reorder • Click ★ to set as hero image    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Maps                                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ┌────────┐ ┌────────┐ ┌─────────────┐             │   │
│  │  │  🗺️    │ │  🗺️    │ │    + Add    │             │   │
│  │  │ Claim  │ │ Geol   │ │    Map      │             │   │
│  │  │ Map    │ │ Map    │ │             │             │   │
│  │  └────────┘ └────────┘ └─────────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Technical Documents                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📄 NI_43-101_Report_2023.pdf        45 MB [x]     │   │
│  │  📄 Assay_Certificates.pdf           2.3 MB [x]    │   │
│  │  📊 Drill_Results_Summary.xlsx       156 KB [x]    │   │
│  │                                                     │   │
│  │  [+ Upload Document]                                │   │
│  │                                                     │   │
│  │  Accepted: PDF, DOC, DOCX, XLS, XLSX (max 100MB)   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Videos (optional)                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  YouTube or Vimeo URL:                              │   │
│  │  ┌───────────────────────────────────────────────┐ │   │
│  │  │ https://youtube.com/watch?v=...               │ │   │
│  │  └───────────────────────────────────────────────┘ │   │
│  │  [+ Add Video]                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                      [← Back]  [Save Draft]  [Next →]      │
└─────────────────────────────────────────────────────────────┘
```

### Step 8: Review & Submit
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Listing                    Step 8 of 8         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━                              │
│                                                             │
│  Review Your Listing                                        │
│  ───────────────────                                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [Preview Card - How it will appear in search]      │   │
│  │  ┌────────────────────────────────────────────┐    │   │
│  │  │ 🖼️ Golden Valley Placer Claims             │    │   │
│  │  │    Cariboo, British Columbia               │    │   │
│  │  │    [Gold] [Placer] 450 ha                  │    │   │
│  │  │    $450,000 CAD                            │    │   │
│  │  └────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Checklist                                                  │
│  ─────────                                                  │
│  ✓ Basic information complete                              │
│  ✓ Location details added                                  │
│  ✓ Claim details entered (12 claims)                       │
│  ✓ Minerals & geology described                            │
│  ✓ Exploration history documented                          │
│  ✓ Transaction terms set ($450,000 CAD)                    │
│  ✓ Photos uploaded (3 images)                              │
│  ✓ Documents attached (3 files)                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⓘ Your listing will be reviewed before going      │   │
│  │    live. This typically takes 1-2 business days.   │   │
│  │    You'll be notified by email when approved.      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [x] I confirm all information is accurate                 │
│  [x] I have rights to sell/transfer this property          │
│  [x] I agree to the Terms of Service                       │
│                                                             │
│           [← Back]  [Save as Draft]  [Submit for Review]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Enhanced Features & Differentiators

### 5.1 Interactive Map Search
- Leaflet/Mapbox integration for property visualization
- Cluster markers for dense areas
- Draw polygon to search within area
- Layer toggles: claims, geology, infrastructure
- Satellite/terrain view options

### 5.2 Property Comparison Tool
- Side-by-side comparison of up to 4 properties
- Compare key metrics: size, price, mineral, stage
- Exportable comparison PDF

### 5.3 Market Intelligence
- Price per hectare analytics by region/mineral
- Trending regions based on listing activity
- Similar property price suggestions for sellers

### 5.4 Verified Prospector Program
- Identity verification badge
- Claim ownership verification
- Professional credentials display
- Increases buyer confidence

### 5.5 Inquiry Management Dashboard
- CRM-lite for prospectors
- Track inquiry stages
- Quick response templates
- Analytics on listing performance

### 5.6 Automated Alerts
- New listings matching saved searches
- Price changes on watchlist items
- Expiring claims notifications
- Market updates for specific regions

### 5.7 Document Data Room
- Secure document sharing for serious inquiries
- NDA-gated access to sensitive documents
- View tracking for prospectors
- Watermarked downloads

### 5.8 Mobile-Optimized Experience
- Responsive design for field access
- Offline property viewing (PWA)
- GPS-enabled nearby property search

---

## 6. File Storage Strategy

### 6.1 Recommended: DigitalOcean Spaces (S3-compatible)
```
Bucket Structure:
goldventure-media/
├── property-exchange/
│   ├── listings/
│   │   ├── {listing_id}/
│   │   │   ├── images/
│   │   │   │   ├── hero.jpg
│   │   │   │   ├── gallery/
│   │   │   │   └── thumbnails/
│   │   │   ├── maps/
│   │   │   ├── documents/
│   │   │   └── videos/
│   └── prospectors/
│       └── {prospector_id}/
│           └── profile/
```

### 6.2 Implementation
```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.environ.get('DO_SPACES_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('DO_SPACES_SECRET')
AWS_STORAGE_BUCKET_NAME = 'goldventure-media'
AWS_S3_ENDPOINT_URL = 'https://tor1.digitaloceanspaces.com'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_DEFAULT_ACL = 'public-read'
AWS_LOCATION = 'property-exchange'
```

---

## 7. Future Monetization Architecture

### 7.1 User Tiers (Database Ready)
```python
class SubscriptionTier(models.Model):
    TIERS = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    name = models.CharField(choices=TIERS)
    price_monthly = models.DecimalField()
    price_yearly = models.DecimalField()
    features = models.JSONField()
    max_listings = models.IntegerField()
    max_saved_searches = models.IntegerField()
    can_contact_sellers = models.BooleanField()
    can_export_data = models.BooleanField()
    can_view_market_analytics = models.BooleanField()
    priority_support = models.BooleanField()
```

### 7.2 Future Paid Features
**For Investors:**
- Unlimited property views (free tier limited)
- Direct seller contact
- Market analytics access
- Bulk data export
- Priority alerts

**For Prospectors:**
- Featured listings
- Analytics dashboard
- Lead scoring
- CRM features
- Promoted profile

---

## 8. Implementation Phases

### Phase 1: Foundation (MVP)
- [ ] Database models for properties & prospectors
- [ ] Basic CRUD API endpoints
- [ ] Property listing form (all steps)
- [ ] Property search & detail pages
- [ ] Prospector registration & profile
- [ ] Basic inquiry system

### Phase 2: Discovery & Engagement
- [ ] Advanced search filters
- [ ] Map-based search
- [ ] Watchlist functionality
- [ ] Saved searches with alerts
- [ ] Similar properties recommendation

### Phase 3: Trust & Verification
- [ ] Prospector verification system
- [ ] Document secure sharing (data room)
- [ ] Inquiry management dashboard
- [ ] Review/rating system

### Phase 4: Intelligence & Growth
- [ ] Market analytics
- [ ] Property comparison tool
- [ ] Automated valuations
- [ ] Mobile PWA
- [ ] Monetization tiers

---

## 9. Success Metrics

### Platform Health
- Number of active listings
- Prospector registrations
- Inquiry volume
- Conversion rate (inquiry → transaction)

### User Engagement
- Average session duration
- Search-to-contact ratio
- Watchlist additions
- Return visitor rate

### Business Metrics
- Featured listing revenue
- Subscription conversions
- Transaction facilitation (future)

---

## Approval Checklist

Please review and confirm:

1. [ ] Data model structure meets requirements
2. [ ] API endpoint design is comprehensive
3. [ ] UI/UX layouts align with vision
4. [ ] Multi-step form covers all needed fields
5. [ ] File storage approach is acceptable
6. [ ] Monetization structure is future-ready
7. [ ] Phase breakdown is prioritized correctly

Ready to proceed with implementation upon approval.
