# ?? 4-Day Sprint: Quote Portal MVP

**Created:** November 26, 2025
**Goal:** Customer-facing quote portal + landing page + demo video
**Deadline:** End of Thanksgiving weekend

---

## Success Criteria

- [ ] Customer uploads file ? gets instant quote ? accepts ? order created
- [ ] 30-second demo video recorded
- [ ] Landing page collecting email signups
- [ ] Deployed to real URL

---

## Day 1 (Thursday): Quote Portal Frontend

### Morning: Setup + Layout
- [ ] React app scaffold (Vite + Tailwind)
- [ ] Install shadcn/ui components
- [ ] Basic routing (/, /quote, /quote/:id, /confirmation)
- [ ] Layout component (header, footer)

### Afternoon: Quote Request Flow
- [ ] File upload component (drag & drop 3MF)
- [ ] Material selector (PLA, PETG, ABS, ASA, TPU)
- [ ] Quantity input
- [ ] "Get Quote" button ? calls ML Dashboard API
- [ ] Loading state

### Evening: Quote Display
- [ ] Quote result card (price, time, weight, dimensions)
- [ ] Material breakdown display
- [ ] "Accept Quote" / "Request Changes" buttons
- [ ] Store quote ID for retrieval

**Day 1 Deliverable:** Customer can upload ? see quote

---

## Day 2 (Friday): Quote Management + Polish

### Morning: Quote Acceptance Flow
- [ ] Accept quote ? creates sales order in ERP
- [ ] Confirmation page with order number
- [ ] Email capture (guest checkout)
- [ ] Basic form validation

### Afternoon: Quote History (Admin View)
- [ ] Simple dashboard showing incoming quotes
- [ ] Quote status (pending, accepted, rejected)
- [ ] Customer info display
- [ ] Link to production order

### Evening: UI Polish
- [ ] Responsive design (mobile)
- [ ] Error states (API down, file too big, etc.)
- [ ] Success animations
- [ ] Professional styling

**Day 2 Deliverable:** Full quote ? order flow working

---

## Day 3 (Saturday): Landing Page + Deployment

### Morning: Landing Page
- [ ] Hero section: "Instant 3D Print Quotes for Your Business"
- [ ] How it works (3 steps with icons)
- [ ] Feature highlights (ML accuracy, material support)
- [ ] "Join the Beta" email signup form
- [ ] Footer with contact info

### Afternoon: Deployment
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway (or keep local for demo)
- [ ] Custom domain setup (optional)
- [ ] SSL working

### Evening: Integration Testing
- [ ] End-to-end flow testing
- [ ] Fix bugs
- [ ] Mobile testing
- [ ] Seed demo data

**Day 3 Deliverable:** Deployed and working on real URL

---

## Day 4 (Sunday): Demo + Launch

### Morning: Demo Video
- [ ] Screen record full flow (OBS or Loom)
- [ ] Voiceover explaining value prop
- [ ] Keep under 90 seconds
- [ ] Create thumbnail

### Afternoon: Launch Prep
- [ ] Reddit post draft (r/BambuLab, r/3Dprinting)
- [ ] Screenshots for social media
- [ ] Beta signup incentive copy
- [ ] Prepare for feedback/questions

### Evening: LAUNCH ??
- [ ] Post to Reddit
- [ ] Share in Bambu Discord
- [ ] Upload demo to YouTube
- [ ] Monitor signups + feedback
- [ ] Celebrate ??

**Day 4 Deliverable:** Live product, collecting signups

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React + Vite + Tailwind | Fast, familiar |
| UI Components | shadcn/ui | Beautiful, copy-paste |
| File Upload | react-dropzone | Simple, reliable |
| State | useState (keep simple) | MVP, don't overthink |
| Backend | Existing FastAPI (8000 + 8001) | Already done |
| Hosting | Vercel (FE) + Railway (BE) | Free tier, fast |
| Email Signup | ConvertKit free tier | Simple embed |
| Video | Loom or OBS | Quick recording |

---

## Frontend Structure
`
quote-portal/
+-- src/
¦   +-- components/
¦   ¦   +-- ui/              # shadcn components
¦   ¦   +-- FileUpload.jsx
¦   ¦   +-- MaterialSelector.jsx
¦   ¦   +-- QuoteCard.jsx
¦   ¦   +-- QuoteForm.jsx
¦   ¦   +-- Layout.jsx
¦   +-- pages/
¦   ¦   +-- Home.jsx          # Landing page
¦   ¦   +-- GetQuote.jsx      # Upload flow
¦   ¦   +-- QuoteResult.jsx   # Show quote
¦   ¦   +-- Confirmation.jsx  # Order confirmed
¦   +-- api/
¦   ¦   +-- quotes.js         # API calls to backend
¦   +-- App.jsx
¦   +-- main.jsx
+-- public/
¦   +-- logo.svg
+-- index.html
+-- tailwind.config.js
+-- vite.config.js
+-- package.json
`

---

## API Endpoints Needed

### ML Dashboard (port 8001) - Already exists
- POST /api/quotes/generate - Upload file, get quote

### ERP Backend (port 8000) - May need tweaks
- POST /api/v1/quotes - Save quote to DB
- POST /api/v1/quotes/{id}/accept - Accept quote, create order
- GET /api/v1/quotes/{id} - Retrieve quote details

---

## NOT In Scope (Resist Temptation!)

? User authentication (guest checkout fine)
? Payment integration (manual invoicing)
? Full admin dashboard (use DB directly)
? Inventory checking (future)
? Color selection (future)
? Mobile app
? Perfect code

**Mantra: Ship > Perfect**

---

## Risks + Mitigations

| Risk | Mitigation |
|------|------------|
| Backend breaks | It's working now, minimal changes |
| Frontend takes too long | shadcn = pre-built components |
| Deployment issues | Vercel is drag-and-drop |
| Scope creep | This doc IS the scope |
| Burnout | Day 3 evening = forced break |

---

## Commands to Start Day 1
`ash
# Create project
npm create vite@latest quote-portal -- --template react
cd quote-portal

# Install Tailwind
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install dependencies
npm install react-router-dom react-dropzone axios

# Install shadcn/ui
npx shadcn-ui@latest init

# Start dev server
npm run dev
`

---

## Landing Page Copy (Draft)

### Hero
**Headline:** Instant 3D Print Quotes. Powered by AI.

**Subhead:** Upload your file, select material, get accurate pricing in seconds. No back-and-forth emails.

**CTA:** Get Your Quote ?

### How It Works
1. **Upload** - Drag & drop your 3MF or STL file
2. **Configure** - Select material, quantity, quality
3. **Quote** - Get instant pricing with ML-accurate time estimates

### Features
- ? Instant quotes (no waiting for email replies)
- ?? 88.9% time estimation accuracy
- ?? 5 materials (PLA, PETG, ABS, ASA, TPU)
- ??? Production-grade Bambu Lab fleet

### Beta CTA
**Join 50 early customers** getting lifetime pricing. Enter your email below.

---

## Let's Go! ??

Wake up. Coffee. Day 1 starts.
