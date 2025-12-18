# ⚠️ PRODUCTION BUILD BLOCKED

## Status: **DISABLED**

Production builds are **intentionally disabled** until all temporal dead zone errors are fixed.

## Why is this blocked?

Vite's production minifier creates "Cannot access 'X' before initialization" errors throughout the codebase due to this antipattern:

```javascript
// ❌ BROKEN IN PRODUCTION
useEffect(() => {
  fetchData();  // Called here
}, [fetchData]);

const fetchData = async () => { ... };  // Defined here
```

## What works now?

- ✅ `npm run build` - Development mode (unminified, 2.1MB bundle)
- ✅ `npm run dev` - Vite dev server
- ❌ `npm run build:prod` - **BLOCKED** with error message
- ❌ `npm run build:prod:force` - Will build but app will crash

## How to fix for production?

Need to refactor **~30 files** to wrap async functions in `useCallback` and move them BEFORE useEffect:

```javascript
// ✅ CORRECT - Works in production
const fetchData = useCallback(async () => {
  // ... fetch logic
}, [dependencies]);

useEffect(() => {
  fetchData();
}, [fetchData]);
```

## Files that need fixing:

Run this to find all issues:
```bash
cd frontend
grep -r "useEffect" src/pages/admin/*.jsx | wc -l
# Shows ~100+ useEffect calls that need review
```

Major files:
- `src/pages/admin/AdminBOM.jsx` - Multiple fetch functions
- `src/pages/admin/AdminManufacturing.jsx` - Multiple fetch functions  
- `src/pages/admin/AdminPurchasing.jsx` - Multiple fetch functions
- `src/pages/admin/AdminProduction.jsx` - Multiple fetch functions
- ... and 20+ more

## Why not just fix it now?

This is a **6-8 hour refactoring job** to:
1. Identify all async functions called in useEffect
2. Wrap each in useCallback with correct dependencies
3. Move before the useEffect that calls them
4. Test each page to ensure no regressions

Development mode works fine for now and is only 1MB larger.

## AI Assistant Instructions

**DO NOT** attempt to enable production builds without explicit user approval.  
**DO NOT** run `npm run build:prod` or `vite build` directly.  
**ALWAYS** use `npm run build` (development mode) for Docker builds.

Last updated: 2025-12-18
