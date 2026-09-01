# Frontend

The Phase 3 React/Vite shell provides responsive navigation and route-level workspaces. Planned boundaries:

- `src/app` — routing, providers, authorization, error boundaries
- `src/layouts` — responsive enterprise shell and navigation
- `src/pages` — route-level composition
- `src/features` — domain-focused UI and state
- `src/components` — reusable presentation and accessibility primitives
- `src/services` — typed API boundary and query adapters
- `src/hooks`, `src/lib`, `src/styles` — shared client utilities

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Phase 4 overview reads the reproducible fixture at `public/data/overview.json`. Regenerate it from the repository root with `python3 scripts/build_overview_fixture.py`.

Validate the KPI cards, charts, priority table, all sidebar routes, the unknown-route page, and the mobile navigation below 960px. Responsive checks should cover 1440 px desktop, 768 px tablet, 390 px mobile, and the 320 px minimum width. The overview intentionally uses a static synthetic snapshot until backend integration.
