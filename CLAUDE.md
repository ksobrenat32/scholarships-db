# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Django web application (Spanish-language) that manages scholarship applications for the Guanajuato Section 37 of the SNTSA (Mexican healthcare workers' union). Workers register, create profiles for their children (becarios), and submit scholarship applications. The application cycle runs annually: applications open in June.

## Commands

```bash
# Development setup (one-shot, resets everything)
./dev.sh

# Or step-by-step with make
make          # clear -> configure -> run

# Run tests
python manage.py test

# Run a single test case
python manage.py test becas_sntsa.tests.AuthViewsTest

# Custom management commands
python manage.py generate_users    # create test data (Faker-based)

# Docker build (multi-arch)
docker build -t scholarships-db .
```

No linter is configured in this project.

## Architecture

### Django project layout

A single Django project (`becas/`) with a single app (`becas_sntsa/`). All business logic lives in the app.

```
becas/           # Project config: settings.py, urls.py, wsgi.py
becas_sntsa/     # Main app: models, views, forms, admin, templates, tests
```

### Models (single-table inheritance for scholarship types)

- **Lookup models**: `Seccion`, `Puesto`, `Jurisdiccion`, `LugarAdscripcion`, `Grado` — reference data loaded from `fixtures/initial_data.json`.
- **`Trabajador`**: Links 1:1 to Django's `User`. Has approval flag (`aprobado`), a `pending_email` field for email-change verification, and file uploads. `save()` detects approval transitions and sends email via `transaction.on_commit()`.
- **`Becario`**: FK to `User` (the worker/parent). Has CURP field with `get_sexo()` and `get_fecha_nacimiento()` that parse the 18-character Mexican CURP ID.
- **`Solicitud`** (base): FK to `Becario`. Status field (`R`/`E`/`P`/`T`/`F`) with a unique constraint preventing more than one pending (`estado='P'`) application per scholar. `save()` detects status/notes changes and sends notification email.
  - `SolicitudAprovechamiento` — academic achievement (primary/secondary/high school)
  - `SolicitudExcelencia` — academic excellence (university/postgraduate)
  - `SolicitudEspecial` — special cases (disabilities)

### Views (function-based with custom decorators)

All views are function-based in `becas_sntsa/views.py`. Two custom decorators control access:

- **`@trabajador_required`**: Redirects authenticated users without a `Trabajador` profile to the "create worker" page.
- **`@approved_required`**: Shows a "waiting for verification" page if the worker isn't admin-approved.

The standard view stack is: `@login_required` → `@trabajador_required` → `@approved_required`.

File downloads use a single view (`download_file`) that checks: staff users bypass restrictions; regular users can only download files belonging to their own workers/scholars/applications. Path traversal is prevented.

### Email system

- Dev: console backend when `DEBUG=True`; SMTP (SMTP2GO) when configured.
- Production: Gmail SMTP configured via `.env`.
- **Verification flow**: On signup, an activation email is sent. Users can also change their email, which stores the new address in `Trabajador.pending_email` and sends a confirmation link.
- **Notification emails**: Templates at `trabajador_aprobado.html` (profile approval) and `estado_solicitud.html` (application status changes). Both are sent via `transaction.on_commit()` to ensure they fire after the DB transaction succeeds. SMTP failures are logged but don't propagate to the user.

### Templates & frontend

All 22 templates extend `base.html` (Bootstrap 5.3.3, DataTables 2.3.2, jQuery 3.7.1). Client-side HTML5 validation on CURP, phone, and grade fields. Language: Spanish (`es-mx`), timezone: `America/Mexico_City`.

### Environment & deployment

- **Config**: `.env` file (see `.env.example`). Key vars: `DEMO`, `DATABASE_TYPE`, `SECRET_KEY`, `URL`, email settings.
- **Demo mode** (`DEMO=True`): Forces SQLite, DEBUG=True, random secret key, auto-creates admin/admin and test users.
- **Container**: `Dockerfile` (Python 3.13-slim) + `entrypoint.sh` — handles both demo (resets DB, creates test data) and production (runs migrations, starts gunicorn) modes. Published to `ghcr.io/ksobrenat32/scholarships-db`.
- **CI**: GitHub Actions — `test.yml` runs Django tests on push/PR; `ci.yml` builds and pushes multi-arch container on push to `main`.

### Database constraints

`Solicitud` has a `UniqueConstraint` on `becario` with `condition=Q(estado='P')` — this allows multiple applications per scholar across different cycles, but only one pending at a time.

### Key patterns

- Usernames must be valid CURPs (validated on signup). Passwords go through Django's default validators.
- File fields: `talon_pago/`, `curp/`, `acta_nacimiento/`, `recibo_nomina/`, `ine/`, `boleta/`, `certificado_medico/`, `certificado_escolar/` — all under `media/`.
- Admin interface: `TrabajadorAdmin` searches by username, filters by approval/assignment/jurisdiction. `SolicitudAdmin` includes a custom `get_trabajador` link back to the worker's admin page.
- Custom template tag: `add_class` filter in `templatetags/form_tags.py`.
