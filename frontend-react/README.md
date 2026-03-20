# Trippen React dashboard

This directory hosts the modern React + TypeScript dashboard that will replace the vanilla HTML/CSS frontend. It is scaffolded with Vite, React Router, TanStack Query, and a reusable dashboard layout so we can focus on wiring the existing FastAPI endpoints.

## Prerequisites

- Node.js 20+
- The FastAPI backend available at `http://127.0.0.1:8000` (default) or a custom URL of your choice

## Installation

```bash
npm install
```

## Development server

```bash
npm run dev
```

The dev server runs on <http://localhost:5173>. An API proxy is configured for requests starting with `/api`, and you can also change the base URL in the sidebar input inside the UI. For a different default, create a `.env` file and set `VITE_API_BASE_URL`.

## Production build

```bash
npm run build
npm run preview
```

The build step compiles TypeScript, emits static assets, and runs Vite’s production bundle. `npm run preview` serves the build for smoke-testing.

## Project structure

- `src/config/navigation.ts` – single source of truth for sidebar links & descriptions.
- `src/contexts/ApiConfigContext.tsx` – stores the API base URL with localStorage persistence.
- `src/components/layout/*` – dashboard shell, sidebar, and shared controls.
- `src/pages/*` – scaffolding for each workflow (dashboard, trips, new trip, clients, holidays, seed data).
- `src/router.tsx` – React Router configuration with nested routes.

## Next steps

1. Build the typed API client + hooks on top of TanStack Query.
2. Port each vanilla workflow into the new React pages, wiring forms, tables, and actions to the FastAPI endpoints.
3. Add loading/error states, optimistic updates where appropriate, and regression tests.
