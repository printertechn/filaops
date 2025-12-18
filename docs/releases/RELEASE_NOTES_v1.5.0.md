# Release Notes - v1.5.0

**Release Date**: December 18, 2025  
**Type**: Community Edition (Self-Hosted)

---

## 🎯 Highlights

- ✅ **Fixed critical Items page initialization error**
- ✅ **Fixed RecordPaymentModal initialization error**
- 📝 **Comprehensive documentation updates**
- 🛡️ **Production build safeguards for SaaS readiness**

---

## 🐛 Bug Fixes

### Frontend
- **Fixed**: Items page "Cannot access 'fetchItems' before initialization" error
- **Fixed**: RecordPaymentModal payment recording error
- **Fixed**: ItemForm, MaterialForm, BOMEditor, RoutingEditor initialization issues
- **Improved**: Development build configuration for better debugging

### Build System
- **Changed**: Frontend now uses development mode builds (unminified) for community edition
- **Added**: Production build safeguards to prevent accidental minified builds
- **Added**: Source maps for easier debugging

---

## 📚 Documentation

### New Documents
- `KNOWN_ISSUES.md` - Transparent issue tracking for community
- `frontend/PRODUCTION_BUILD_BLOCKED.md` - Technical details on build configuration
- `.ai-instructions/NO_PRODUCTION_BUILDS.md` - Guidelines for AI-assisted development

### Updated Documents
- `README.md` - Added build configuration notes
- `CONTRIBUTING.md` - Added development build guidance
- `docs/SAAS_TIERING_PLAN.md` - Added SaaS technical prerequisites
- `PROPRIETARY.md` - Added production deployment requirements

---

## ⚙️ Technical Changes

### Build Configuration
```javascript
// Development mode (default)
npm run build → vite build --mode development

// Production (blocked - requires fixes)
npm run build:prod → exits with error
```

**Why?** The codebase has ~30 components with React hook timing issues that only manifest in minified production builds. Development builds work perfectly and are ideal for self-hosted deployments.

### Bundle Stats
- **Development**: 2.1MB (unminified) + 3.5MB source maps
- **Production**: 980KB (blocked until fixes complete)

---

## ⚠️ Known Issues

Some modal dialogs may show initialization errors on first load. **Workaround**: Refresh the page.

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for complete details and tracking.

---

## 🚀 Deployment Notes

### Docker Compose
No changes required - standard deployment works:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Environment Variables
No new variables required for this release.

### Database Migrations
No migrations in this release.

---

## 📊 What's Next

### v1.6.0 (Planned - Q1 2026)
- Fix all remaining modal initialization issues
- Production build support
- Performance optimizations
- Enhanced error handling

### Community Feedback
We want to hear from you! Report issues or suggest features:
- **GitHub Issues**: https://github.com/Blb3D/filaops/issues
- **GitHub Discussions**: https://github.com/Blb3D/filaops/discussions
- **Discord**: https://discord.gg/FAhxySnRwa

---

## 🙏 Thank You

To everyone testing, reporting issues, and contributing - this release wouldn't be possible without you!

Special thanks to early adopters who've provided valuable feedback.

---

## Upgrade Instructions

### From v1.4.x

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose -f docker-compose.dev.yml build

# Restart services
docker-compose -f docker-compose.dev.yml up -d

# Clear browser cache (important!)
# Use Ctrl+Shift+R or incognito mode
```

No database changes required.

---

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete change history.
