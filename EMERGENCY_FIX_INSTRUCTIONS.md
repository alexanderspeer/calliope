# Emergency Fix: Tables in Both Schemas

## Problem

Tables were created in **BOTH** `public` and `calliope` schemas:
- calliope.words ✓ (correct)
- calliope.config ✓ (correct)
- public.words ✗ (collision risk!)
- public.config ✗ (collision risk!)

This happened because schema isolation didn't activate properly during deployment.

## Fix Steps (Run These Commands)

### Step 1: Set DATABASE_URL (PowerShell)

```powershell
$env:DATABASE_URL='postgres://u6v29drppo6nm9:p976d26dd41e0677f94be2b3a3f51e5ab6c0e8eec3b74626b3fbc444a477919c5@c683rl2u9g20vq.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d4cpj3hcf8ednu'
```

### Step 2: Diagnose Schema Detection

```powershell
python diagnose_schema_detection.py
```

**Expected Output:**
```
[OK] SCHEMA DETECTION WORKING CORRECTLY
Models are configured to use calliope schema.
```

**If it shows error:** The models aren't detecting PostgreSQL correctly. Check that DATABASE_URL is set.

### Step 3: Clean Up Public Tables

```powershell
python cleanup_public_tables.py
```

This will:
1. Show you what tables exist in each schema
2. Ask for confirmation
3. Drop public.words and public.config
4. Keep all your data safe in calliope.* schema

**Important:** Type `YES` (all caps) when asked to confirm.

### Step 4: Restart Your Heroku App

```powershell
heroku restart --app your-app-name
```

### Step 5: Verify Schema Isolation

```bash
curl https://your-app-name.herokuapp.com/api/verify-schema
```

**Expected Result:**
```json
{
  "status": "safe",
  "verification": {
    "safe": true,
    "tables_found": ["calliope.words", "calliope.config"],
    "public_tables_created": [],
    "message": "All tables in 'calliope' schema, public schema untouched"
  }
}
```

## Why Did This Happen?

The tables in `public` were likely created from a previous deployment before schema isolation was added. The new code is working correctly (creating tables in `calliope`), but the old tables in `public` need to be manually removed.

## What the Cleanup Does

- ✓ Removes public.words (the collision)
- ✓ Removes public.config (the collision)
- ✓ Keeps all data in calliope.words
- ✓ Keeps all data in calliope.config
- ✓ Makes schema isolation work correctly
- ✓ Prevents breaking other apps on the shared database

## After Cleanup

Your app will:
- Only use `calliope.*` tables
- Never touch `public.*` tables
- Run safely on the shared database
- Not collide with other apps

## If You Need Help

Run the diagnostic to see what's wrong:
```powershell
python diagnose_schema_detection.py
```

Check table locations directly:
```powershell
heroku pg:psql --app your-app-name
# Then run:
\dt calliope.*
\dt public.*
```

## Quick Command Sequence

```powershell
# 1. Set database URL
$env:DATABASE_URL='postgres://u6v29drppo6nm9:p976d26dd41e0677f94be2b3a3f51e5ab6c0e8eec3b74626b3fbc444a477919c5@c683rl2u9g20vq.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d4cpj3hcf8ednu'

# 2. Run cleanup (will ask for confirmation)
python cleanup_public_tables.py

# 3. Restart Heroku app
heroku restart --app calliope-your-app-name

# 4. Verify
curl https://calliope-your-app-name.herokuapp.com/api/verify-schema
```

## Safety Notes

- ✓ Your data is safe in calliope.words
- ✓ Cleanup only removes public tables
- ✓ No data loss will occur
- ✓ Operation is reversible (but not needed)

##  Summary

**Current State:** Tables in both schemas (unsafe)
**After Cleanup:** Tables only in calliope schema (safe)
**Result:** App runs safely on shared database
