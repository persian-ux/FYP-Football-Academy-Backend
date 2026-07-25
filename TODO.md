# Issues Found & Fixed

## ✅ Issue 1: CORS Configuration (FIXED)
**Root Cause:** `.env` file was overriding `settings.py` defaults with only port 3000.
**Fix:** Updated `.env` file to include `http://localhost:5173` and `http://127.0.0.1:5173` in both `CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.

## ✅ Issue 2: Payload Field Name Mismatch - Frontend sends camelCase (FIXED)
**Problem:** Frontend sends `confirmPassword` (camelCase) but backend only accepted `confirm_password`, `password_confirm`, or `password2`. Also frontend sends `firstName`/`lastName`/`phoneNumber` which weren't accepted.
**Fix:** Added `confirmPassword`, `firstName`, `lastName`, `phoneNumber` fields to `RegisterSerializer`. Updated `validate()` to check `confirmPassword` and map camelCase names to snake_case. Updated `create()` to pop all extra fields before creating the user.
**Status:** ✅ FIXED

## ✅ Issue 3: No tokens returned on registration (FIXED)
**Problem:** After registration, frontend expects `response.data.tokens` but backend only returns `{id, email, role}`.
**Status:** ✅ Already fixed in a previous session - `RegisterAPIView.post()` returns JWT tokens in the response.

