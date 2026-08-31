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

Open `http://localhost:5173`. Validate all sidebar routes, the active state, the unknown-route page, and the mobile navigation below 960px. Phase 4 will replace the Overview placeholder with synthetic operational data.
