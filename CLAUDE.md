
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Apply migrations (also auto-bootstraps dev data on first run)
python manage.py migrate

# Run development server
python manage.py runserver


# Django system check (use before running to catch config errors)
python manage.py check

# Generate a .env file with a random SECRET_KEY (optional — a key is auto-generated on first run)
python manage.py generate_env

# Idempotently materialize the dev Organization + admin + fund-owner user
python manage.py bootstrap_dev

# Create the FundOwners permission group (needed for production role setup)
python manage.py setup_platform_roles
```

There is no test suite in this project. Validation is done by running `python manage.py check` and hitting the API manually or via `audit_test.py` (temporary script, not committed).

## Fresh-Clone Bootstrap

A fresh clone with **no `.env` file and an empty database** boots and serves all endpoints. The sequence is:

1. `pip install -r requirements.txt`
2. `python manage.py migrate`
3. `python manage.py runserver`

On step 2, the `post_migrate` signal in `users/apps.py` calls `config.dev_auth._bootstrap_dev_entities()`, which idempotently creates:
- a verified `Organization` named "Dev Organization" **with a complete onboarding profile** (logo, phone, description, country, city, address, and one verification document — see the Fund-Owner Onboarding Gate below). `_ensure_dev_org_profile()` fills these so the fresh-clone "create a fund" flow is not blocked by the onboarding gate.
- an admin `User` named `dev_admin` (is_staff, is_verified)
- a fund-owner `User` named `dev_fund_owner` (in the FundOwners group)

On step 3, `UsersConfig.ready()` re-runs bootstrap as a safety net. Every view/serializer that needs a User or Organization calls `config.dev_auth.ensure_dev_entities()` as a fallback, so even a deleted entity self-heals.

`SECRET_KEY` is auto-generated and cached to `.secret_key` (gitignored) when not set in env.

## Environment Flags (.env optional)

The defaults in `config/settings.py` already enable full autonomous dev mode. Override via `.env` only when needed.

| Flag | Default | Effect |
|------|---------|--------|
| `ENABLE_AUTH` | `false` | Removes JWT requirement from all endpoints |
| `DEV_PUBLIC_MODE` | `true` | Falls back to first DB user/org when unauthenticated |
| `AUTO_BOOTSTRAP` | `true` | Auto-creates dev entities on empty DB. Forced to `true` whenever `ENABLE_AUTH=false`. |
| `ALLOW_EMPTY_DATABASE` | `true` | Semantic flag: empty DB is expected/allowed |
| `MOCK_EXTERNAL_SERVICES` | `true` | Uses `console.EmailBackend` instead of SMTP |
| `REQUIRE_ADMIN_FOR_DELETE` | `true` | Keeps DELETE admin-only even in dev mode |
| `DATABASE_NAME` | `db.sqlite3` | Override the sqlite filename (useful for fresh-DB testing) |
| `SECRET_KEY` | auto | Auto-generated and cached to `.secret_key` if unset |

To restore production auth: set `ENABLE_AUTH=true`, `DEV_PUBLIC_MODE=false`, `AUTO_BOOTSTRAP=false`, `DEBUG=False`, and provide a real `SECRET_KEY`.

## Architecture

### App Layout

The project has 8 Django apps. Model ownership is non-obvious:

- **`users/models.py`** — contains `User`, `Organization`, `Campaign`, and `Donation` models. The `campaigns` and `donations` apps have empty `models.py` files; they only hold views, serializers, and URL routing.
- **`myapp/`** — "Fund owner applications" (people applying to become fund owners). The name is misleading.
- **`applications/`** — "Fund applications" (public applications for funding). Separate from `myapp`.
- **`funds/`** — `Fund` objects (crowdfunding campaigns with files, statuses, and amounts).
- **`fund_owner/`** — Organization profile management; also mounts `FundOwnerCampaignViewSet` and `FundOwnerDonationViewSet` from other apps under `/api/fund-owner/`.

### Central Dev-Mode Utility

`config/dev_auth.py` is the single source of truth for development auth bypass. All views import from here:

- `ENABLE_AUTH`, `DEV_PUBLIC_MODE`, `AUTO_BOOTSTRAP` — boolean flags. `AUTO_BOOTSTRAP` is forced `True` when `ENABLE_AUTH=False`.
- `get_dev_user(request)` — returns authenticated user, or first DB user, or bootstraps one
- `get_dev_organization(request)` — same pattern for Organization
- `_bootstrap_dev_entities()` / `ensure_dev_entities()` — idempotent; creates `Dev Organization` (verified) + `dev_admin` (is_staff) + `dev_fund_owner` (FundOwners group). Never raises; returns `(None, None)` if migrations haven't run yet.
- `check_delete_permission(request)` — enforces admin-only DELETEs when `REQUIRE_ADMIN_FOR_DELETE=true`

`users/apps.py` connects a `post_migrate` signal that calls `_bootstrap_dev_entities()` after migrations, **and** runs the same bootstrap inside `AppConfig.ready()` when `runserver`/`shell`/`test` starts. Views and serializers (funds, campaigns, donations, fund_owner, users, auth_app/change-password) call `ensure_dev_entities()` as a final fallback so the API still works even if a row was manually deleted.

### URL Structure

```
/api/auth/          → auth_app (register, login, logout, token, change-password)
/api/users/         → users (me/, list)
/api/campaigns/     → campaigns (list, detail — read-only public)
/api/donations/     → donations (list, create, detail, campaign/<id>/)
/api/fund-owner/    → fund_owner + campaigns.FundOwnerCampaignViewSet + donations.FundOwnerDonationViewSet
                      (profile/, my-funds/, donations/, list, detail)
/api/funds/         → funds (CRUD via DefaultRouter — PUT disabled, use PATCH)
/api/fund-applications/ → myapp (list/create, <id>/review/)
/api/applications/  → applications (submit/ only)
/admin/users/       → users.AdminUserViewSet (verify, block, unblock, donations actions)
/admin/campaigns/   → campaigns.AdminCampaignViewSet (list, destroy)
/admin/donations/   → donations.AdminDonationViewSet (list with search)
/admin/applications/ → applications.AdminFundApplicationViewSet (list, retrieve, approve, reject)
/swagger/ or /api/swagger/ → Swagger UI
```

### Permission System

Two roles on `User.role`: `admin` and `fund_owner`.

- **`myapp/permissions.py`** — canonical permission classes: `IsAdminRole`, `IsFundOwner`, `IsFundOwnerWithOrganization`, `IsAdminOrFundOwner`, `IsOwnerOfObject`, `ReadOnly`
- **`users/permissions.py`** — re-exports from `myapp.permissions` plus `IsAuthenticatedActiveUser`, `IsFundOwnerOrAdmin`, `fund_owner_scoped_organization_id()`
- **`funds/permissions.py`** — `IsVerifiedFundOwner` (checks `organization.verified`); `OrganizationProfileComplete` (the onboarding gate, see below)

All permission classes are bypassed in dev mode via `permission_classes = (AllowAny,)` controlled by `ENABLE_AUTH`. **Exception:** `FundViewSet` keeps `JWTAuthentication` + `IsAuthenticatedActiveUser` + `FundAccessPermission` + `OrganizationProfileComplete` regardless of `ENABLE_AUTH` — fund management is never un-gated. Dev mode still works because the bootstrapped Dev Organization is given a complete profile.

### Fund-Owner Onboarding Gate

A fund owner **must complete the organization profile before creating or managing funds**. This is enforced by `OrganizationProfileComplete` in `funds/permissions.py`, applied to `FundViewSet` (blocks `POST` and any write/PATCH; SAFE/read methods stay open). Staff and non-fund-owner roles pass through (auth/role rejection is left to the other permission classes).

Profile state lives on the `Organization` model (`users/models.py`):
- New fields: `logo` (ImageField), `phone_number`, `description`, `country`, `city`, `address`. `name` already existed.
- `OrganizationDocument` (related name `documents`) — verification documents; **at least one** is required.
- `Organization.missing_profile_fields` → list of empty required field keys (order: `PROFILE_FIELDS`). `Organization.is_profile_complete` → `not missing_profile_fields`.

API contract for the frontend onboarding flow:
- `GET /api/fund-owner/profile/` (`OrganizationPublicSerializer`) returns the profile fields plus `documents`, `verified`, `profile_complete`, `missing_fields`, `can_create_fund` (= profile complete), `can_publish_fund` (= profile complete **and** `verified`). The frontend uses these to redirect to Settings → Organization Profile, hide "Create Fund", and show the onboarding banner.
- `PATCH /api/fund-owner/profile/` (`OrganizationWriteSerializer`, **multipart**) edits the text fields + `logo`, and accepts a write-only `documents` list of files (each appended as a new `OrganizationDocument`; existing ones kept). The view has `MultiPartParser`/`FormParser`/`JSONParser`.

Verification interaction (`Organization.verified`): a profile-complete but **unverified** org may only create **draft** funds — `FundCreateSerializer.create()` sets `status=DRAFT` when `not organization.verified`, else `PENDING`. Publishing/activating remains staff-only (fund owners are already restricted to `draft`/`paused` in `FundPartialUpdateSerializer.validate_status`). `is_blocked` users are rejected at login (`auth_app/serializers.py`) and by `get_active_user()` on every gated endpoint.

> This repo is the **backend**. The UI requirements in the spec (dark-theme profile page, drag & drop area, redirect, banner) are frontend concerns built against the contract above.

### Serializer Patterns

- `FundCreateSerializer.create()` and `FundOwnerCampaignCreateSerializer.create()` resolve `organization` and `user` from `get_dev_user()`/`get_dev_organization()`, falling back to `_bootstrap_dev_entities()` if the DB is empty.
- `DonationCreateSerializer.create()` resolves the donor user the same way.
- `FundViewSet` disables PUT (returns 405) but exposes PATCH via an explicit `partial_update()` override — DRF's default `partial_update` delegates to `update()`, which would also return 405.
- `FundOwnerCampaignCreateSerializer` returns only `{"name": "..."}` on POST (no `id`); fetch from the list endpoint if you need the created campaign's ID.
- `FundCreateSerializer.create()` sets fund `status` by org verification: `DRAFT` if `not organization.verified`, else `PENDING`. The fallback auto-created org is now `verified=False` (was `True`) so it cannot bypass verification.
- `OrganizationWriteSerializer.update()` pops `documents` and bulk-creates `OrganizationDocument` rows; an explicit `logo: null` is ignored (PATCH keeps the existing logo unless a new file is sent).

### Email

Approval/rejection emails are sent from `myapp/services.py` (`send_approval_email`, `send_rejection_email`). Both raise `EmailDeliveryError` on failure; the views catch this and return HTTP 200 with `"email_sent": false`. With `MOCK_EXTERNAL_SERVICES=true`, `console.EmailBackend` is used and emails print to the terminal.

### File Uploads

`Fund` has two file fields (`cover_image`, `supporting_document`). The create endpoint is multipart-only (`MultiPartParser`, `FormParser`). Validators are in `funds/validators.py`.
