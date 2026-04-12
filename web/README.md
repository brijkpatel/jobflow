# web

Next.js dashboard. User-facing UI for job preferences, application tracking, HITL approval, and interview prep review.

## Run
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
npm run start
```

## Test
```bash
npm run test
npm run test:e2e
```

## Structure
```
src/
  app/           Next.js App Router pages
  components/    Shared UI components
  hooks/         SSE hooks (useApplicationEvents)
  lib/           API client (REST → jobflow-api)
```

## Key pages
| Route | Purpose |
|-------|---------|
| `/dashboard` | Application pipeline overview, status cards |
| `/preferences` | Job search preferences, resume upload |
| `/applications/[id]` | Single application detail + timeline |
| `/applications/[id]/review` | HITL approval — view resume/cover letter, approve or reject |
| `/prep/[id]` | Interview prep pack for a specific application |
| `/profile/optimizer` | ProfileOptimizer recommendations |

## Protocols
- **REST** → `jobflow-api` for all CRUD (preferences, applications, profile)
- **SSE** ← `jobflow-api` `/events` stream for real-time application status updates
- **WebSocket** not used — SSE is sufficient for one-way status push

## HITL flow
1. `jobflow-api` pushes SSE event `hitl.approval_required`
2. UI shows `/applications/[id]/review` with tailored resume + cover letter
3. User clicks Approve or Reject (with optional note)
4. UI POSTs to `jobflow-api /applications/{id}/review`
5. `jobflow-api` webhooks back to `jobflow-application`

## Key rules
- Static export compatible — no server-side secrets
- Auth via `jobflow-api` JWT (stored in httpOnly cookie)
- Multi-tenant: tenant scoped via JWT claim, not URL path
