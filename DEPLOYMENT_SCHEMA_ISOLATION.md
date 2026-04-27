# Calliope Schema Isolation - Deployment Guide

## Overview

Calliope now supports **safe deployment on shared Heroku Postgres databases** through strict PostgreSQL schema isolation. This prevents table name collisions with other applications sharing the same database.

## Critical Safety Features

### Schema Isolation (PostgreSQL)

- **Local Development (SQLite)**: Tables created in default schema (no isolation needed)
- **Production (PostgreSQL)**: Tables created ONLY in `calliope` schema
  - `calliope.words` (NOT `public.words`)
  - `calliope.config` (NOT `public.config`)

### Safety Guarantees

1. **No Public Schema Access**: Calliope never creates, modifies, or drops tables in `public` schema
2. **Automatic Schema Creation**: The `calliope` schema is created automatically if it doesn't exist
3. **Idempotent Operations**: Safe to run multiple times - no data loss or duplication
4. **Existing Data Protected**: Will not touch existing `public.words`, `public.config`, or any other tables

## Deployment Steps

### 1. Verify Environment Variables

```bash
# On Heroku
heroku config:get DATABASE_URL --app your-app-name

# Locally (for testing)
export DATABASE_URL='postgres://user:pass@host:port/database'
```
postgres://u6v29drppo6nm9:p976d26dd41e0677f94be2b3a3f51e5ab6c0e8eec3b74626b3fbc444a477919c5@c683rl2u9g20vq.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d4cpj3hcf8ednu
export DATABASE_URL='postgres://u6v29drppo6nm9:p976d26dd41e0677f94be2b3a3f51e5ab6c0e8eec3b74626b3fbc444a477919c5@c683rl2u9g20vq.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d4cpj3hcf8ednu'
$env:DATABASE_URL='postgres://u6v29drppo6nm9:p976d26dd41e0677f94be2b3a3f51e5ab6c0e8eec3b74626b3fbc444a477919c5@c683rl2u9g20vq.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d4cpj3hcf8ednu'
### 2. Deploy the Application

```bash
git push heroku main
# or
git push heroku your-branch:main
```

The application will automatically:
1. Detect PostgreSQL database
2. Create `calliope` schema (if it doesn't exist)
3. Create tables in `calliope` schema
4. Seed initial data (if calliope tables are empty)

### 3. Verify Schema Isolation (CRITICAL)

After deployment, verify schema isolation using one of these methods:

#### Method A: API Endpoint

```bash
curl https://your-app-name.herokuapp.com/api/verify-schema
```

Expected response for safe deployment:
```json
{
  "status": "safe",
  "verification": {
    "database_type": "postgresql",
    "status": "ok",
    "safe": true,
    "tables_found": ["calliope.words", "calliope.config"],
    "public_tables_created": [],
    "message": "✓ All tables in 'calliope' schema, public schema untouched"
  },
  "recommendation": "Safe to use - schema isolation verified"
}
```

#### Method B: Standalone Script

```bash
# Set DATABASE_URL if testing locally
export DATABASE_URL='your-heroku-postgres-url'

# Run verification script
python verify_schema_isolation.py
```

Expected output:
```
======================================================================
CALLIOPE SCHEMA ISOLATION VERIFICATION
======================================================================

Database Type: POSTGRESQL
Expected Schema: calliope

✓ Tables Found:
  - calliope.words
  - calliope.config

Status: ✓ OK
Message: ✓ All tables in 'calliope' schema, public schema untouched

======================================================================
✓ SAFE: Schema isolation verified - safe to use in production
======================================================================
```

#### Method C: Direct Database Query

```bash
# Connect to Heroku Postgres
heroku pg:psql --app your-app-name

# Check calliope schema tables
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname = 'calliope';

# Expected output:
#  schemaname | tablename 
# ------------+-----------
#  calliope   | words
#  calliope   | config
```

## Shared Database Compatibility

### Current Setup

If you're using a shared Heroku Postgres database (e.g., `postgresql-elliptical-80317`) that contains:
- `public.words` (from other apps)
- `public.config` (from other apps)
- `euterpe` schema (from euterpe app)

Calliope will:
- Create and use ONLY the `calliope` schema
- Never touch `public.*` tables
- Never touch `euterpe.*` tables
- Coexist safely with all other apps

### Schema Layout

```
PostgreSQL Database: postgresql-elliptical-80317
│
├── public (untouched by calliope)
│   ├── words       ← Other apps' tables (PROTECTED)
│   ├── config      ← Other apps' tables (PROTECTED)
│   └── users       ← Other apps' tables (PROTECTED)
│
├── euterpe (untouched by calliope)
│   ├── songs       ← Euterpe app tables (PROTECTED)
│   └── playlists   ← Euterpe app tables (PROTECTED)
│
└── calliope (calliope's isolated namespace)
    ├── words       ← Calliope's word table
    └── config      ← Calliope's config table
```

## Troubleshooting

### Issue: Tables Created in Public Schema

**Symptoms**: Verification shows tables in `public_tables_created` array

**Solution**:
1. DO NOT USE THIS DEPLOYMENT - it will break other apps
2. Drop the public tables (carefully!):
   ```sql
   DROP TABLE IF EXISTS public.words;  -- Only if created by accident
   DROP TABLE IF EXISTS public.config; -- Only if created by accident
   ```
3. Redeploy the application
4. Run verification again

### Issue: Schema Does Not Exist

**Symptoms**: Error message "Schema 'calliope' does not exist"

**Solution**: The schema should be created automatically. If not:
```bash
heroku pg:psql --app your-app-name
CREATE SCHEMA IF NOT EXISTS calliope;
```

Then restart the app:
```bash
heroku restart --app your-app-name
```

### Issue: SQLAlchemy Cannot Find Tables

**Symptoms**: Errors about missing tables in queries

**Solution**: Check that models have correct schema configuration:
- `backend/models.py` should have `__table_args__ = {"schema": "calliope"}` for PostgreSQL
- Verify `IS_POSTGRESQL` is correctly detected in `backend/models.py`

## Technical Implementation Details

### Model Configuration (`backend/models.py`)

```python
# Automatic schema detection
IS_POSTGRESQL = "postgresql" in DATABASE_URL.lower()
CALLIOPE_SCHEMA = "calliope" if IS_POSTGRESQL else None

class Word(Base):
    __tablename__ = "words"
    
    # ... columns ...
    
    if IS_POSTGRESQL:
        __table_args__ = (
            # ... constraints ...
            {"schema": CALLIOPE_SCHEMA}  # Force schema isolation
        )
```

### Database Initialization (`backend/db.py`)

```python
def init_database():
    # 1. Create schema first (PostgreSQL only)
    ensure_schema_exists()
    
    # 2. Create tables (in calliope schema on PostgreSQL)
    create_tables()
    
    # 3. Seed data if empty (checks only calliope.words)
    # ...
```

### Safety Functions

- `ensure_schema_exists()`: Creates calliope schema (PostgreSQL only, idempotent)
- `verify_schema_isolation()`: Verifies tables are in correct schema
- `/api/verify-schema`: API endpoint for verification

## Migration from Previous Deployments

If you have an existing calliope deployment on Heroku with tables in `public` schema:

### Option 1: Fresh Start (Recommended)

1. Backup existing data:
   ```bash
   python backup_heroku_words.py
   ```

2. Drop old public tables (on new shared database):
   ```bash
   # Not needed if moving to a fresh shared database
   ```

3. Deploy new version with schema isolation

4. Restore data:
   ```bash
   python migrate_to_heroku.py
   ```

### Option 2: Manual Migration

1. Backup data from public schema
2. Create calliope schema
3. Move tables to calliope schema:
   ```sql
   ALTER TABLE public.words SET SCHEMA calliope;
   ALTER TABLE public.config SET SCHEMA calliope;
   ```
4. Deploy new version

## Local Development

Local development with SQLite remains unchanged:
- No schema isolation (SQLite doesn't support schemas)
- Tables created in default namespace
- Same API behavior
- Same functionality

To test PostgreSQL locally:
```bash
# Use local PostgreSQL
export DATABASE_URL='postgresql://localhost/calliope_dev'
python backend/main.py
```

## Security Considerations

1. **Database Credentials**: Never commit `DATABASE_URL` to version control
2. **Schema Permissions**: Calliope only needs access to `calliope` schema
3. **Shared Database**: Other apps cannot access `calliope` schema without explicit permissions
4. **Verification**: Always run verification after deployment

## Support

If you encounter issues with schema isolation:

1. Check verification output
2. Review logs: `heroku logs --tail --app your-app-name`
3. Verify database URL: `heroku config --app your-app-name`
4. Check schema exists: `heroku pg:psql --app your-app-name` → `\dn`
5. Check table locations: `\dt calliope.*` and `\dt public.*`

## Summary Checklist

- [ ] Deploy application to Heroku
- [ ] Run `/api/verify-schema` endpoint
- [ ] Verify output shows `"safe": true`
- [ ] Verify `tables_found` contains `calliope.words` and `calliope.config`
- [ ] Verify `public_tables_created` is empty
- [ ] Test word addition via API
- [ ] Test word retrieval via API
- [ ] Backup data regularly with `backup_heroku_words.py`

**Once all checks pass, your deployment is safe for production use on the shared database.**
