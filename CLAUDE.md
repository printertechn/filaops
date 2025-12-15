# FilaOps - Claude Code Instructions

## ⚠️ CRITICAL - Development vs Production Environments

**NEVER use `docker-compose.yml` directly - it targets PRODUCTION with real business data!**

### Always Use Development Environment

```bash
# CORRECT - Development (safe)
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml exec backend <command>

# WRONG - This hits PRODUCTION!
docker-compose build  # ❌ NO!
docker-compose up     # ❌ NO!
```

### Environment Summary

| Environment | Compose File | Frontend | Backend | DB Port |
|-------------|--------------|----------|---------|---------|
| **DEV** (use this) | `docker-compose.dev.yml` | :5174 | :8001 | :1434 |
| **PROD** (business data) | `docker-compose.yml` | :5173 | :8000 | :1433 |

### Why This Matters

- Production contains the owner's actual business data (customers, orders, inventory)
- Development has separate Docker volumes (`filaops-dev-*`)
- Code changes should be tested on DEV before touching PROD

---

## Project Overview
FilaOps is an ERP system for 3D printing businesses built with:
- **Backend**: Python/FastAPI with SQLAlchemy (SQL Server compatible)
- **Frontend**: React with Vite, Tailwind CSS
- **Deployment**: Docker Compose

## Development Workflow

### Before Pushing Code
**IMPORTANT: Always follow this checklist before `git push`:**

1. **Run backend tests**
   ```bash
   cd backend && python -m pytest tests/ -v
   ```

2. **Run linting**
   ```bash
   cd backend && ruff check .
   ```

3. **List files for CodeRabbit review**
   ```bash
   git diff --name-only HEAD~1  # or appropriate range
   ```

4. **Wait for CodeRabbit review** (if PR is open)
   - Address any CodeRabbit findings before merging
   - Common issues: SQL Server compatibility, type hints, error handling

### SQL Server Compatibility
- Use `== True` not `.is_(True)` for boolean comparisons (SQL Server generates invalid `IS 1`)
- Add `# noqa: E712` comment to suppress linting warnings
- Example:
  ```python
  .filter(Model.active == True)  # noqa: E712 - SQL Server requires == True
  ```

### Commit Message Format
```
type: Short description

Longer description if needed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### Issue Workflow
- Reference issues in commits: `Fixes #123` or `Relates to #123`
- Add comments to issues with implementation details
- Close issues only after testing confirms the fix

## Code Style

### Backend (Python)
- Use type hints for function parameters and returns
- Use Pydantic models for request/response validation
- Follow existing patterns in `app/services/` for business logic

### Frontend (React)
- Use dark theme styling (bg-gray-900, text-white, border-gray-700)
- Use Tailwind CSS classes consistently
- Fetch from `${API_URL}/api/v1/...`

## Testing Checklist

### For New Features
1. Unit tests in `backend/tests/`
2. API endpoint testing via curl or frontend
3. Docker container rebuild if dependencies changed
4. UI workflow testing with screenshots (for documentation)

### For Bug Fixes
1. Verify the issue is reproducible
2. Implement fix
3. Test fix resolves the issue
4. Check for regressions
