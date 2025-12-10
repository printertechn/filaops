# Repository Organization

This document explains the repository structure for new contributors and collaborators.

## 📁 Directory Structure

```
filaops/
├── backend/              # FastAPI backend application
│   ├── app/             # Application code
│   ├── migrations/      # Alembic database migrations
│   ├── tests/           # Backend tests
│   └── scripts/         # Backend-specific scripts
├── frontend/            # React frontend application
├── docs/                # All documentation (see below)
├── scripts/             # Utility scripts
│   ├── github/         # GitHub management scripts
│   ├── database/       # Database setup/migration SQL
│   └── tools/          # Utility Python scripts
├── README.md            # Main project README
├── CONTRIBUTING.md      # Contribution guidelines
├── INSTALL.md           # Installation guide
└── docker-compose.yml   # Docker deployment config
```

## 📚 Documentation Organization

### Root Level (User-Facing)
Essential documentation that users and contributors need first:
- `README.md` - Project overview and quick start
- `INSTALL.md` - Installation guide
- `GETTING_STARTED.md` - Development setup
- `CONTRIBUTING.md` - How to contribute
- `FAQ.md` - Frequently asked questions
- `TROUBLESHOOTING.md` - Common issues and solutions
- `HOW_IT_WORKS.md` - System overview
- `CHANGELOG.md` - Version history
- `RELEASE_NOTES.md` - Release announcements
- `SECURITY.md` - Security policy
- `LICENSE` - Project license

### `docs/` Directory

#### `docs/architecture/`
Technical architecture and design documents:
- System architecture overviews
- Database schemas
- API documentation
- Integration patterns

#### `docs/planning/`
Roadmaps, release plans, and future features:
- Product roadmap
- Release planning documents
- Phase and sprint plans
- Feature implementation plans

#### `docs/development/`
For developers working on the codebase:
- Testing guides
- Debug documentation
- Integration guides
- Development workflows
- Technical reviews and analyses

#### `docs/history/`
Project progress and milestones:
- Phase completion summaries
- Progress reports
- Migration completion docs
- Historical status updates

#### `docs/sessions/`
Context and handoff documents:
- AI context files
- Session handoffs
- Infrastructure notes

## 🔧 Scripts Organization

### `scripts/github/`
GitHub issue and release management:
- Creating and updating issues
- Release management
- Repository maintenance

### `scripts/database/`
Database setup and migration SQL scripts:
- Initial database setup
- Migration scripts
- Data synchronization

### `scripts/tools/`
Utility Python scripts:
- Data import/export
- Analysis tools
- Development helpers

## 🎯 Finding What You Need

**New to the project?**
1. Start with `README.md`
2. Read `GETTING_STARTED.md` for development setup
3. Check `CONTRIBUTING.md` for contribution guidelines

**Looking for architecture info?**
- See `docs/architecture/`

**Working on a feature?**
- Check `docs/planning/` for roadmaps
- Review `docs/development/` for guides

**Setting up the database?**
- Check `scripts/database/` for SQL scripts
- See `docs/README_SEEDING.md` for seeding data

## 📝 Notes

- Keep root directory clean - only essential user-facing docs
- Organize new documentation in appropriate `docs/` subdirectories
- Update this file if you add new major organizational changes

