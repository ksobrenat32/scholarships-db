# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Django web application (Spanish-language) that manages scholarship applications for the Guanajuato Section 37 of the SNTSA (Mexican healthcare workers' union). Workers register, create profiles for their children (becarios), and submit scholarship applications. The application cycle runs annually: applications open in June.

## Commands

```bash
# Development setup (one-shot, resets everything — SQLite, demo mode)
./dev.sh

# Or step-by-step with make
make          # clear -> configure -> run

# Run tests
python manage.py test

# Run a single test case
python manage.py test becas_sntsa.tests.AuthViewsTest

# Custom management commands
python manage.py generate_users                                    # 10 users, 1-5 becarios each
python manage.py generate_users --num_users 50 --max-becarios 10  # custom counts

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

### User lifecycle & access control

The full user journey determines which views are accessible:

1. **Signup** — username must be a valid 18-char CURP (regex-validated in the view). User is created active and logged in.
2. **Create Trabajador profile** — sets email from the form, then **deactivates** the user and sends a verification email. User is logged out. If email fails to send, the Trabajador is deleted and the user must retry.
3. **Email verification** (`activate` view) — sets `user.is_active = True`, logs the user in, redirects to `becas`.
4. **Admin approval** — an admin sets `Trabajador.aprobado = True`, which triggers an approval notification email via `transaction.on_commit()`.
5. **Full access** — only after all three steps (verified + approved) can the user create becarios and solicitudes.

Two custom decorators in [becas_sntsa/views.py](becas_sntsa/views.py) enforce this:
- **`@trabajador_required`**: Redirects authenticated users without a `Trabajador` profile to `create_trabajador`.
- **`@approved_required`**: Shows `espera_verificacion.html` if the worker isn't admin-approved.

The standard view stack is: `@login_required` → `@trabajador_required` → `@approved_required`.

### Models (single-table inheritance for scholarship types)

- **Lookup models**: `Seccion`, `Puesto`, `Jurisdiccion`, `LugarAdscripcion`, `Grado` — reference data loaded from `fixtures/initial_data.json`. Note: `Jurisdiccion` is **not** registered in the admin.
- **`Trabajador`**: Links 1:1 to Django's `User`. Has approval flag (`aprobado`), a `pending_email` field for email-change verification, and file uploads. `save()` detects approval transitions and sends email via `transaction.on_commit()`.
- **`Becario`**: FK to `User` (the worker/parent). Has CURP field with `get_sexo()` and `get_fecha_nacimiento()` that parse the 18-character Mexican CURP ID.
- **`Solicitud`** (base): FK to `Becario`. Status field with a `UniqueConstraint` preventing more than one pending application per scholar. `save()` detects status/notes changes and sends notification email.

**Solicitud status codes** (from `ESTADO_CHOICES`):

| Code | Spanish | English |
|------|---------|---------|
| `R` | Solicitud recibida | Received |
| `E` | Error en documentos, revisar notas | Document error, check notes |
| `P` | En espera de resultados | Awaiting results |
| `T` | Beca otorgada | Scholarship granted |
| `F` | Beca no otorgada | Scholarship not granted |

The three scholarship subtypes:
- `SolicitudAprovechamiento` — academic achievement (primary/secondary/high school), adds `grado`, `promedio`, `boleta`
- `SolicitudExcelencia` — academic excellence (university/postgraduate), adds `grado`, `promedio`, `boleta`, `carrera`
- `SolicitudEspecial` — special cases (disabilities), adds `diagnostico_medico`, `tipo_educacion`, `certificado_medico`, `certificado_escolar`

### Duplicate application check: DB vs app-level

The `UniqueConstraint` on `Solicitud` only blocks duplicate `estado='P'` per becario. However, **each creation view** also manually rejects duplicates when `estado__in=['R', 'P']` — so the app-level check is broader than the DB constraint. This means a becario can only have one active application (R or P) per scholarship type at a time.

### Becario editing restriction

A becario can only be edited if they have **no** solicitudes with estado `R`, `P`, or `T` (see [becas_sntsa/views.py:668-672](becas_sntsa/views.py#L668-L672)). If they have an active or approved application, the user must create a new becario instead.

### Views (function-based with custom decorators)

All views are function-based in `becas_sntsa/views.py`. Beyond the CRUD views, key ones:

- **`download_file`**: Staff users bypass all restrictions. Regular users can only download files belonging to their own workers' tree (trabajador's `talon_pago`, their becarios' `curp_archivo`/`acta_nacimiento`, their solicitudes' `recibo_nomina`/`ine`, and subclass-specific files like `boleta` or `certificado_medico`). Path traversal is prevented via `os.path.realpath`.
- **`editar_usuario`**: If the email changes, the new address is stored in `Trabajador.pending_email` and a confirmation link is sent. The old email remains active until confirmed.
- **`change_password`**: Uses Django's `PasswordChangeForm`. On success, redirects to `signin` (user must re-authenticate).

### Email system

- Dev: console backend when `DEBUG=True` **and** `EMAIL_HOST` is unset; SMTP (SMTP2GO) when configured.
- Production: Gmail SMTP configured via `.env`.
- **Verification flow**: On signup, an activation email is sent. Users can also change their email, which stores the new address in `Trabajador.pending_email` and sends a confirmation link. If email sending fails, the operation is rolled back (Trabajador deleted on creation; `pending_email` cleared on edit).
- **Notification emails**: Templates at `trabajador_aprobado.html` (profile approval) and `estado_solicitud.html` (application status changes). Both are sent via `transaction.on_commit()` to ensure they fire after the DB transaction succeeds. SMTP failures are logged but don't propagate to the user.

### Templates & frontend

All 22 templates extend `base.html` (Bootstrap 5.3.3, DataTables 2.3.2, jQuery 3.7.1). Client-side HTML5 validation on CURP, phone, and grade fields. Language: Spanish (`es-mx`), timezone: `America/Mexico_City`.

### Environment & deployment

- **Config**: `.env` file (see `.env.example`). Key vars: `DEMO`, `DATABASE_TYPE`, `SECRET_KEY`, `URL`, `PORT`, email settings.
- **Demo mode** (`DEMO=True`): Forces SQLite, DEBUG=True, random secret key, auto-creates admin/admin and 10 test users via `generate_users`.
- **Container**: `Dockerfile` (Python 3.13-slim) + `entrypoint.sh` — handles both demo (resets DB, creates test data) and production (runs migrations, starts gunicorn) modes. Published to `ghcr.io/ksobrenat32/scholarships-db`.
- **CI**: GitHub Actions — `test.yml` runs Django tests on push to `main` and on all PRs; `ci.yml` builds and pushes multi-arch container (`linux/amd64`, `linux/arm64`) on push to `main`.
- **Static files**: Whitenoise (`CompressedManifestStaticFilesStorage`) serves static files in both dev and production.

### Testing patterns

Tests live in a single file: [becas_sntsa/tests.py](becas_sntsa/tests.py). Key patterns:

- **Email tests** use `@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')` to capture sent emails in `django.core.mail.outbox`.
- **_on_commit callbacks** require `with self.captureOnCommitCallbacks(execute=True):` when testing `transaction.on_commit()` email sends; without it, the callbacks never execute in tests.
- **File cleanup**: Tests that create file uploads should clean up in `tearDown` (see `DownloadFileViewTest.tearDown`).
- **Minimum Django version**: There's a test enforcing `Django >= 5.2.6`.

### Key patterns

- Usernames must be valid CURPs (validated on signup). Passwords go through Django's default validators.
- File fields: `talon_pago/`, `curp/`, `acta_nacimiento/`, `recibo_nomina/`, `ine/`, `boleta/`, `certificado_medico/`, `certificado_escolar/` — all under `media/`.
- Admin interface: `TrabajadorAdmin` searches by username, filters by approval/assignment/jurisdiction. `SolicitudAdmin` includes a custom `get_trabajador` link back to the worker's admin page. `Jurisdiccion` is NOT registered in admin.
- Custom template tag: `add_class` filter in `templatetags/form_tags.py`.
- CURP validation regex is defined in both `forms.py` (`validar_curp`) and `views.py` (`signup`). They must be kept in sync.
