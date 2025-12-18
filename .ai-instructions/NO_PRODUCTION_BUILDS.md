# ⚠️ CRITICAL PRODUCTION BUILD WARNING

## For AI Assistants and Developers

**DO NOT** enable production builds (`vite build` without `--mode development`) without explicit user approval.

### Current Build Configuration

- ✅ **Default**: `npm run build` → Development mode (unminified, 2.1MB)
- ❌ **Blocked**: `npm run build:prod` → Exits with error
- ⚠️  **Force**: `npm run build:prod:force` → Builds but app crashes

### Why Production Builds Are Disabled

The entire codebase has async functions defined **after** the `useEffect` hooks that call them:

```javascript
// This pattern exists in ~30 files
useEffect(() => {
  fetchData();  // ❌ Called here
}, [fetchData]);

const fetchData = async () => { ... };  // ❌ Defined here - TOO LATE
```

Vite's production minifier reorders code, creating "Cannot access before initialization" errors.

### What Needs to Happen Before Production

1. Refactor ~30 page components to use `useCallback` properly
2. Move all fetch functions BEFORE the useEffect that calls them
3. Estimated effort: **6-8 hours**

### Files Modified to Prevent Production Builds

1. `frontend/package.json` - `build:prod` command exits with error
2. `frontend/Dockerfile` - Comments warn about development mode
3. `frontend/vite.config.js` - Minify only in production mode
4. `frontend/PRODUCTION_BUILD_BLOCKED.md` - Detailed documentation

### AI Assistant Instructions

When asked about builds or deployments:
- Always use `npm run build` (development mode)
- Never suggest `vite build` directly
- Never modify `package.json` to re-enable production builds
- If asked about production optimization, refer to PRODUCTION_BUILD_BLOCKED.md

### Current Bundle Stats

- Development: 2.1MB (unminified) + 3.5MB source maps
- Production (blocked): Would be ~980KB but crashes immediately
- Performance: Development mode is acceptable for current usage

Last updated: 2025-12-18
