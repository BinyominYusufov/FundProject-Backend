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

# Generate a .env file with a random SECRET_KEY
python manage.py generate_env

# Create the FundOwners permission group (needed for production role setup)
python manage.py setup_platform_roles
```

There is no test suite in this project. Validation is done by running `python manage.py check` and hitting the API manually or via `audit_test.py` (temporary script, not committed).

## Environment Flags (.env)

All behavior is controlled via `.env` (gitignored). The key flags:

| Flag | Dev value | Effect |
|------|-----------|--------|
| `ENABLE_AUTH` | `false` | Removes JWT requirement from all endpoints |
| `DEV_PUBLIC_MODE` | `true` | Falls back to first DB user/org when unauthenticated |
| `AUTO_BOOTSTRAP` | `true` | Auto-creates a dev Organization + User on empty DB |
| `ALLOW_EMPTY_DATABASE` | `true` | Suppresses "entity must exist" errors |
| `MOCK_EXTERNAL_SERVICES` | `true` | Uses `console.EmailBackend` instead of SMTP |
| `REQUIRE_ADMIN_FOR_DELETE` | `true` | Keeps DELETE admin-only even in dev mode |

To restore full production auth: set `ENABLE_AUTH=true`, `DEV_PUBLIC_MODE=false`, `AUTO_BOOTSTRAP=false`.

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

- `ENABLE_AUTH`, `DEV_PUBLIC_MODE`, `AUTO_BOOTSTRAP` — boolean flags
- `get_dev_user(request)` — returns authenticated user, or first DB user, or bootstraps one
- `get_dev_organization(request)` — same pattern for Organization
- `_bootstrap_dev_entities()` — idempotent; creates `Dev Organization` (verified) + `dev_admin` (is_staff) if either is missing
- `check_delete_permission(request)` — enforces admin-only DELETEs when `REQUIRE_ADMIN_FOR_DELETE=true`

`users/apps.py` connects a `post_migrate` signal that calls `_bootstrap_dev_entities()` automatically after migrations.

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
- **`funds/permissions.py`** — `IsVerifiedFundOwner` (checks `organization.verified`)

All permission classes are bypassed in dev mode via `permission_classes = (AllowAny,)` controlled by `ENABLE_AUTH`.

### Serializer Patterns

- `FundCreateSerializer.create()` and `FundOwnerCampaignCreateSerializer.create()` resolve `organization` and `user` from `get_dev_user()`/`get_dev_organization()`, falling back to `_bootstrap_dev_entities()` if the DB is empty.
- `DonationCreateSerializer.create()` resolves the donor user the same way.
- `FundViewSet` disables PUT (returns 405) but exposes PATCH via an explicit `partial_update()` override — DRF's default `partial_update` delegates to `update()`, which would also return 405.
- `FundOwnerCampaignCreateSerializer` returns only `{"name": "..."}` on POST (no `id`); fetch from the list endpoint if you need the created campaign's ID.

### Email

Approval/rejection emails are sent from `myapp/services.py` (`send_approval_email`, `send_rejection_email`). Both raise `EmailDeliveryError` on failure; the views catch this and return HTTP 200 with `"email_sent": false`. With `MOCK_EXTERNAL_SERVICES=true`, `console.EmailBackend` is used and emails print to the terminal.

### File Uploads

`Fund` has two file fields (`cover_image`, `supporting_document`). The create endpoint is multipart-only (`MultiPartParser`, `FormParser`). Validators are in `funds/validators.py`.
