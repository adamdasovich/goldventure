# Google Search Console Diagnostic Checklist

## Phase 1B: Critical SEO Diagnostics

### 1. Canonical URL Verification

#### Current Status:
✅ **IMPLEMENTED**: Homepage has canonical URL
- Found: `<link rel="canonical" href="https://juniorgoldminingintelligence.com"/>`

#### Action Items for You:
1. **Go to Google Search Console** → https://search.google.com/search-console
2. Navigate to **URL Inspection** tool
3. Enter: `https://juniorgoldminingintelligence.com`
4. Check the following:
   - **User-declared canonical**: Should be `https://juniorgoldminingintelligence.com`
   - **Google-selected canonical**: Should MATCH the user-declared canonical

#### Red Flags to Watch For:
❌ **If Google selected a DIFFERENT URL**, you have duplicate content issues
- Common examples:
  - `https://www.juniorgoldminingintelligence.com` (www vs non-www)
  - `https://juniorgoldminingintelligence.com/` (trailing slash)
  - `http://juniorgoldminintelligence.com` (http vs https)

#### If Canonical Mismatch Found:
1. Check your Nginx/server configuration for redirects
2. Ensure ALL variants redirect to: `https://juniorgoldminintelligence.com` (no www, no trailing slash, https only)
3. Submit the correct URL for indexing in GSC

---

### 2. Keyword Impression Analysis

#### Target Keywords to Check:
1. **junior gold mining** (primary target)
2. **junior gold mining companies**
3. **junior gold mining stocks**
4. **NI 43-101**
5. **TSXV mining**
6. **gold exploration companies**

#### Steps to Perform:
1. Go to GSC → **Performance** → **Search Results**
2. Click **+ New** filter → **Query** → **Queries containing**
3. Enter each keyword above and note results

#### What to Look For:

**Scenario A: Zero Impressions**
```
Query: "junior gold mining"
Impressions: 0
Clicks: 0
```
**Diagnosis**: Technical/indexing problem
**Action**:
- Request indexing via GSC URL Inspection
- Check robots.txt is not blocking
- Verify sitemap submitted

**Scenario B: High Impressions + Low Position (>50)**
```
Query: "junior gold mining"
Impressions: 500+
Average Position: 67
CTR: 0.0%
```
**Diagnosis**: Content/authority deficit (you're ranking but too low to get clicks)
**Action**:
- Need more backlinks with keyword-rich anchor text
- Improve on-page optimization (more instances of keyword)
- Create pillar content targeting this keyword

**Scenario C: High Impressions + Low CTR**
```
Query: "junior gold mining"
Impressions: 1000+
Average Position: 15
CTR: 1.2%
```
**Diagnosis**: Title/meta description not compelling enough
**Action**:
- Optimize meta title (add year, benefits, numbers)
- Improve meta description (add call-to-action)

---

### 3. Index Coverage Check

#### Steps:
1. GSC → **Index** → **Pages**
2. Look at **"Why pages aren't indexed"** section

#### Common Issues:

| Issue | What It Means | How to Fix |
|-------|---------------|------------|
| **Crawled - currently not indexed** | Google saw it but chose not to index | Improve content quality, add more value |
| **Discovered - currently not indexed** | Google found URL but hasn't crawled yet | Wait, or request indexing manually |
| **Alternate page with proper canonical tag** | Another version of the page is indexed | This is usually OK (e.g., mobile/desktop versions) |
| **Duplicate without user-selected canonical** | You have duplicate content | Add canonical tags or consolidate pages |
| **Page with redirect** | Page redirects elsewhere | Ensure redirect chain is clean (301 permanent) |

---

### 4. Mobile Usability Check

#### Steps:
1. GSC → **Experience** → **Page Experience**
2. Check **Mobile** tab
3. Look for **Core Web Vitals** issues

#### Key Metrics:
- **LCP (Largest Contentful Paint)**: Should be < 2.5s
- **FID (First Input Delay)**: Should be < 100ms
- **CLS (Cumulative Layout Shift)**: Should be < 0.1

---

### 5. Sitemap Verification

#### Steps:
1. GSC → **Indexing** → **Sitemaps**
2. Check status of submitted sitemaps

#### Should See:
```
Sitemap: https://juniorgoldminingintelligence.com/sitemap.xml
Status: Success
Discovered URLs: [number]
```

#### If "Couldn't fetch" error:
1. Visit https://juniorgoldminintelligence.com/sitemap.xml directly in browser
2. Verify it loads and contains URLs
3. Check it's not blocked by robots.txt
4. Resubmit sitemap

---

## Phase 1A Results (Already Completed)

✅ **Keyword Rendering Verified**:
- Title tag: `Junior Gold Mining Intelligence - AI-Powered Mining Investment Platform`
- Main H2: `Junior Gold Mining Intelligence`
- Meta keywords: Contains "junior gold mining" multiple times
- Schema: Contains "Junior Gold Mining" entity references
- **No "gold min" vs "gold mining" issue detected**

---

## Summary of Findings

### What's Working:
✅ Canonical URLs implemented
✅ "Mining" keyword rendering correctly in SSR
✅ Schema.org structured data present
✅ Meta tags include target keywords

### What Needs Verification (Manual GSC Check):
⏳ Canonical URL acceptance by Google
⏳ Keyword impression data
⏳ Index coverage status
⏳ Core Web Vitals scores

### Recommended Immediate Actions:
1. Complete the GSC checklist above and record findings
2. If 0 impressions for "junior gold mining", request indexing immediately
3. If canonicals don't match, fix server redirects
4. Submit updated sitemap if needed

---

## Next Step After GSC Diagnostic

Once you complete this checklist, proceed to **Phase 3A: Homepage Metadata Optimization** where we'll implement keyword-first optimization based on the audit recommendations.
