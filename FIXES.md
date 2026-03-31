# Database & Image Fetching Fixes

## Issues Fixed

### 1. ✅ NOT NULL Constraint Error
**Problem**: Database was throwing `NOT NULL constraint failed: Word_Image.image_file` when generating flashcards without images.

**Solution**: 
- Changed default value from `None` to empty string `""`
- Now uses `image_file = ""` as default, populated only if image is successfully fetched
- Created `fix_db_schema.py` to fix existing databases with NOT NULL constraint

### 2. ✅ Wikimedia 403 Forbidden Error
**Problem**: Image downloads were failing with `403 Forbidden` errors.

**Solution**:
- Improved User-Agent header to be more descriptive and compliant
- Added proper error handling with HTTP status code logging
- Try multiple image results (gsrlimit=3) before giving up
- Search with `File:` prefix for better results
- Fall back gracefully when images aren't available

### 3. ✅ Better Error Messages
- Added status icons (✓ ✗) to console output
- More detailed error logging with HTTP status codes
- Graceful fallback when images can't be fetched

## How to Apply Fixes

### If you encounter database errors:

```bash
python fix_db_schema.py
```

This will:
- Check your database schema
- Fix NOT NULL constraint if needed
- Convert any NULL values to empty strings
- Preserve all existing data

### After fixing, restart your app:

```bash
python app.py
```

## What Changed in Code

### app.py Changes:

1. **fetch_wikimedia_image()**: 
   - Better User-Agent
   - Search with `File:` prefix
   - Try multiple results
   - Return None on failure (gracefully)

2. **download_and_save_image()**:
   - Added User-Agent header
   - Better error handling
   - HTTP status code logging

3. **generate_flashcards()**:
   - Changed `image_file = None` to `image_file = ""`
   - Only populate if image fetch succeeds
   - Always provide valid value for database

## Testing

Generate flashcards with:
- ✅ Images enabled - should fetch when available
- ✅ Images disabled - should work without errors
- ✅ Failed image fetch - should continue without crashing

All scenarios now work correctly! 🎉
