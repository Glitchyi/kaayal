# Kaayal Component Inventory

All components are server-rendered HTML. Shared tokens/styles: `app/ui.py` (single source — do not duplicate CSS elsewhere).

## Primitives (`app/ui.py`)
| Name | API | Notes |
| --- | --- | --- |
| `page(title, body, description)` | full HTML shell | includes fonts, CSS, skip-link, theme-color |
| `esc(s)` | HTML-escape helper | mandatory on all dynamic output |
| `status_badge(status)` | badge HTML | pending/confirmed/verified/unverified/blocked/cancelled |
| `brand_header(tagline)` | Kaayal wordmark header | use on public-facing pages |

## CSS classes
`.card` (sand-spine container) · `.badge`/`.ok`/`.wait`/`.bad` · `.muted` `.small` · `.rule` · `.ml` (Malayalam text) · `button.secondary` `button.danger` · `.skip` · `.btn`

## Surfaces
| Route | File | Purpose |
| --- | --- | --- |
| `GET /` | `app/site.py` | Landing — verified boats + call-to-action |
| `GET /portal/{token}` | `app/portal.py` | Operator dashboard: boats table, add-boat form, request cards |
| `POST /portal/{token}/boats` | `app/portal.py` | Create boat (form) |
| `POST /portal/{token}/requests/{id}/confirm|block` | `app/portal.py` | Request lifecycle |
| `GET /admin?t=` | `app/admin.py` | Owner admin: operators, boats, all requests |
| `POST /admin/operators` | `app/admin.py` | Create operator → one-time portal URL |

## Data displays
- Tables: hairline `--line` borders, teal lowercase-ish header row, no zebra striping.
- Request card: `REQ-####` id + boat + status badge; contact revealed only post-confirm.
- Forms: labeled inputs (`<label for>`), `autocomplete=off`, placeholders show examples ending `…`.

## Missing / future components
- Lagoon Glass voice UI (state machine: idle/connecting/listening/processing/speaking/interrupted/error/disconnected)
- Photo display for boats (awaiting real assets)
- Empty-state illustrations (decide: text-only vs. contour-line motif)
- Toast/notice component (currently none — redirects only)
