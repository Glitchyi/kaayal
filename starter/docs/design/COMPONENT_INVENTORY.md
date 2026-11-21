# Kaayal Component Inventory

All components are server-rendered HTML. Shared tokens/styles: `app/ui.py` (single source — do not duplicate CSS elsewhere).

## Primitives (`app/ui.py`)
| Name | API | Notes |
| --- | --- | --- |
| `page(title, body, description, nav, footer, body_class, motion)` | full HTML shell | fonts, CSS, skip-link, theme-color; `motion=False` on admin/portal (no entrance animation on work surfaces) |
| `esc(s)` | HTML-escape helper | mandatory on all dynamic output |
| `status_badge(status)` | badge HTML | pending/confirmed/verified/unverified/blocked/cancelled; underscores render as spaces (`no_answer` → "no answer") |
| `brand_header(tagline)` | Kaayal wordmark header | use on public-facing pages |

## CSS classes
`.card` (sand-spine container) · `.badge`/`.ok`/`.wait`/`.bad` · `.muted` `.small` · `.rule` · `.ml` (Malayalam text) · `button.secondary` `button.danger` · `.skip` · `.btn` · `.kick` (italic Fraunces section marker) · `.ask` (tel: question rows on the landing page) · `.notice` `.error-box` · `.tablewrap` (horizontal scroll; tables keep a 42rem min-width and `td.actions` is sticky on ≤700px) · `.sectionnav` (admin jump bar; `.n.hot` sand count = work waiting, doubles as the triage ledger) · `details.disclose` (collapsible sand-spine form, open when the list is empty) · `.req`/`.req-actions` (portal request card: one note field, Confirm/Decline/Block via `formaction`) · `.card.quiet` (handled items, hairline spine) · `.facts` (privacy label/answer grid, stacks ≤700px) · `.copyrow` (one-time link + progressive Copy button) · `.sr-only`

## Surfaces
| Route | File | Purpose |
| --- | --- | --- |
| `GET /` | `app/site.py` | Landing — verified boats + call-to-action |
| `GET /portal/{token}` | `app/portal.py` | Operator page: reachability, requests waiting for an answer (first), boats table, collapsible add-boat form, earlier requests |
| `POST /portal/{token}/boats` | `app/portal.py` | Create boat (form) |
| `POST /portal/{token}/requests/{id}/confirm|block` | `app/portal.py` | Request lifecycle |
| `GET /admin?t=` | `app/admin.py` | Owner admin: jump bar with to-do counts, operators, boats, requests (boat names, unassigned badge), callbacks (plain-language reasons, IST times), demo data; post-action notice renders inside the section the redirect lands on |
| `POST /admin/operators` | `app/admin.py` | Create operator → one-time portal URL |

## Data displays
- Tables: hairline `--line` borders, teal lowercase-ish header row, no zebra striping.
- Request card: `REQ-####` id + boat + status badge; contact revealed only post-confirm.
- Forms: labeled inputs (`<label for>`), `autocomplete=off`, placeholders show examples ending `…`.

## Missing / future components
- Lagoon Glass voice UI (state machine: idle/connecting/listening/processing/speaking/interrupted/error/disconnected)
- Photo display for boats (awaiting real assets)
- Empty-state illustrations (decide: text-only vs. contour-line motif)
