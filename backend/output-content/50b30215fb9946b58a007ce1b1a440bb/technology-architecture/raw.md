# Technology Architecture — NetworkPro (repository: CareerPro-v2)

## 1. System Overview

NetworkPro is a career-and-networking web application that accepts a LinkedIn profile PDF upload and presents profile-derived interests plus networking, job, course, and skill recommendations across a four-tab interface.

The implemented system is a **single-service, same-origin full-stack JavaScript application**:

- A **React 18 single-page application** (`client/`) built with Vite, styled with Tailwind CSS and Radix-based shadcn/ui components, using TanStack Query as its data layer.
- A **Node.js/Express 4 HTTP server** (`server/`) exposing a REST API under `/api/*` and hosting the built frontend, listening on port 5000 (`server/index.ts`).
- An **in-memory storage layer** (`server/storage.ts`, `MemStorage`) holding all persistent-ish state in process Maps. Data does not survive a server restart.

Two facts dominate the architecture and must be understood before anything else:

1. **There is no database connection at runtime.** A PostgreSQL schema is fully defined with Drizzle ORM (`shared/schema.ts`) and `drizzle-kit` is configured (`drizzle.config.ts`, dialect `postgresql`, credentials from `DATABASE_URL`), but no runtime code connects to PostgreSQL. Every route reads and writes `MemStorage`. The declared persistence stack is scaffolding for a migration that was never wired in.
2. **All "AI-powered" analysis is simulated in-process.** Recommendation payloads are hard-coded mock generators (`generatePeopleToFollow`, `generateJobOpenings`, `generateCourses`, `generateSkills`, `generateTrendingPosts` in `server/routes.ts`), and PDF "extraction" ignores the uploaded file entirely (`extractTextFromPdf` logs *"Simulating PDF extraction"* and returns canned demo profile text). There is no model provider, NLP service, or LinkedIn API integration anywhere in the codebase. The original brief (`attached_assets/Pasted-Project-Title-NetworkPro-…​.txt`) explicitly deferred LinkedIn OAuth in favor of PDF upload.

Everything runs as one Node process serving both API and client — the deployment shape the code supports is the classic Replit-style single-port application (port 5000 is hard-coded with the comment "It is the only port that is not firewalled").

## 2. Architecture Diagram

```mermaid
flowchart LR
    user(["End user\n(browser)"])

    subgraph browser["Browser — React 18 + TypeScript SPA\n(client/, bundled by Vite)"]
        spa["Tab UI: Home · Interests ·\nNetworking · Jobs\n(Radix / shadcn-ui / Tailwind)"]
        rq["TanStack Query\ndata layer (queryClient.ts)"]
        parser["parsePDF() wrapper\n(lib/pdf-parser.ts)"]
        ls[("localStorage\ntheme key only")]
    end

    subgraph nodeproc["Single Node.js process — Express 4 on :5000\n(server/index.ts)"]
        api["Express app:\nJSON/urlencoded parsing ·\n/api request logging ·\nglobal JSON error handler"]
        routes["REST routes (routes.ts)\n/api/profile · /api/profile/upload\n/api/interests · /api/interests/suggestions\n/api/recommendations/{networking,jobs}\n/api/career-goals · /api/saved-items"]
        multer["multer memoryStorage\nmultipart upload filter:\napplication/pdf ≤ 5 MB"]
        sim["Simulated PDF extraction +\nregex profile parser\n(file contents ignored)"]
        mock["Hard-coded mock\nrecommendation generators"]
        mem[("MemStorage\nin-memory Maps:\nusers · profiles · interests ·\nsavedItems · careerGoals")]
        web["Frontend hosting inside same process:\ndev → Vite middleware + HMR\nprod → express.static(dist/public)"]
    end

    cdn["External image CDNs consumed by <img> tags:\nrandomuser.me portraits · logo.clearbit.com logos ·\nimages.unsplash.com course images"]
    fonts["Google Fonts CDN\n(index.html <link>)"]

    subgraph planned["Declared but INACTIVE (not wired into runtime)"]
        drizzle["Drizzle ORM schema\n(shared/schema.ts) + drizzle-kit\n(drizzle.config.ts, needs DATABASE_URL)\n→ PostgreSQL / Neon driver"]
        auth["passport · passport-local ·\nexpress-session · connect-pg-simple ·\nmemorystore · pdf-parse · ws"]
    end

    user -- "HTTPS (same origin)" --> spa
    spa --> rq
    spa --> parser
    spa -.-> "persists theme" --> ls

    parser -- "POST /api/profile/upload\nmultipart/form-data" --> api
    rq -- "fetch JSON /api/*\nunauthenticated · fixed userId=1" --> api

    api --> routes
    routes --> multer --> sim
    routes --> mock
    routes -- "read/write Maps" --> mem
    api -.-> web

    spa -.-> "loads avatar/logo/course images" --> cdn
    browser -.-> "font stylesheet" --> fonts

    drizzle -.-x "(connection never opened)"
```

Solid arrows are traced in source. Dashed arrows denote asset loading or incidental relationships. The `planned` group is intentionally drawn disconnected: these technologies exist in manifests/configuration but have **no runtime call path** (see §10).

## 3. Runtime Components

### 3.1 Browser Client — React SPA

| Attribute | Value |
|---|---|
| Responsibility | Renders the four-tab workflow (upload profile → pick interests → networking recommendations → jobs/goals), owns session data fetching/mutations, bookmarking interactions |
| Technology | React 18, TypeScript, Vite 5, Tailwind CSS 3, Radix UI primitives via shadcn/ui, TanStack Query 5, framer-motion, lucide/react-icons |
| Location | `client/` (entry `client/index.html` → `client/src/main.tsx` → `client/src/App.tsx`) |
| Inputs | HTML document; same-origin `/api/*` JSON; user file selection |
| Outputs | Fetch requests to `/api/*`; DOM/UI; theme persistence to `localStorage` |
| Evidence | Fully verified — `vite.config.ts` sets `root: client`, alias `@` → `client/src`; dependency manifest and JSX sources agree |
| Certainty | Verified fact |

Navigation is **tab-state based**: `App.tsx` switches `HomeTab / InterestsTab / NetworkingTab / JobsTab` from a `useState<TabType>` value. The `wouter` routing dependency and `pages/not-found.tsx` exist but nothing imports them — no router is active.

### 3.2 Data Layer — TanStack Query

| Attribute | Value |
|---|---|
| Responsibility | Single fetch abstraction for queries and mutations; caches API responses client-side |
| Technology | @tanstack/react-query v5; custom `apiRequest()` / `getQueryFn()` in `client/src/lib/queryClient.ts` |
| Behavior | All calls use relative `/api/...` URLs with `credentials: "include"`; defaults: `retry: false`, `refetchOnWindowFocus: false`, `staleTime: Infinity` (recommendation hooks override to 5 minutes) |
| Evidence | Verified — every data hook (`useLinkedInProfile`, `useInterests`, `useRecommendations`, `useSavedItems`, `useCareerGoals`) routes through it |
| Certainty | Verified fact |

### 3.3 API Server — Express 4

| Attribute | Value |
|---|---|
| Responsibility | Exposes the REST API, handles multipart uploads, generates mock recommendation content, extracts (simulated) profile data, persists to memory, and serves the frontend |
| Technology | Node.js ≥ 20-era, Express 4, multer 1.4 (memory storage), native `http.createServer` |
| Location | `server/index.ts` (bootstrap), `server/routes.ts` (all endpoints + generators), `server/vite.ts` (frontend hosting helpers) |
| Inputs | Same-origin HTTP requests: JSON bodies, one multipart form field `pdf` |
| Outputs | JSON responses (`{ message }` errors via global handler), console-formatted `/api` request log lines, static assets |
| Configuration | None required at runtime; port hard-coded `5000`, host `0.0.0.0`, `reusePort: true`. Only dev/prod behavior differs via `NODE_ENV`/`app.get("env")` |
| Evidence | Verified — startup path is `package.json` scripts `dev` (`tsx server/index.ts`) and `start` (`node dist/index.js`) into the async bootstrap in `server/index.ts` |
| Certainty | Verified fact |

Endpoint inventory (all registered in `registerRoutes`, `server/routes.ts`):

| Method & Path | Function |
|---|---|
| `POST /api/profile/upload` | multer single-file `pdf`; simulated extraction; upsert profile for fixed user 1 |
| `GET /api/profile` / `PUT /api/profile` | read / update profile (user 1) |
| `GET /api/interests/suggestions` | fixed suggestion payload; **404 unless a profile exists** |
| `GET /api/interests` / `POST /api/interests` | read / upsert interest selections |
| `GET /api/recommendations/networking` | people-to-follow, people-to-connect, trending posts (static mocks) |
| `GET /api/recommendations/jobs` | job openings, courses, skills (static mocks) |
| `GET /api/career-goals` / `POST /api/career-goals` | read (with hard-coded fallback values) / upsert goals |
| `GET /api/saved-items` (optional `?type=`) / `POST /api/saved-items` / `DELETE /api/saved-items/:id` | bookmark CRUD |

No Zod validation executes on request bodies at runtime: the Drizzle-Zod insert schemas in `shared/schema.ts` are exported but never invoked as parsers; route handlers pass `req.body` straight into storage.

### 3.4 Storage Layer — MemStorage

| Attribute | Value |
|---|---|
| Responsibility | Implements the `IStorage` interface for users, profiles, interests, saved items, career goals |
| Technology | Plain TypeScript class over five `Map`s with hand-incremented integer IDs; seeds a demo user (`demo` / `password`) on construction |
| Location | `server/storage.ts`, singleton export `storage` |
| Persistence | **None** — contents are process-lifetime only and reset on restart |
| Evidence | Verified — `routes.ts` imports `{ storage }` exclusively; no other `IStorage` implementation exists (no Drile/Neon/PG client is instantiated anywhere) |
| Certainty | Verified fact |

### 3.5 Frontend Hosting Inside the Same Process

| Mode | Mechanism | Evidence |
|---|---|---|
| Development | `setupVite()` mounts Vite in middleware mode with HMR over the Express HTTP server and transforms `client/index.html` on each request; gated by `app.get("env") === "development"` | `server/vite.ts` lines 25–71, `server/index.ts` lines 53–57 |
| Production | `serveStatic()` serves `dist/public` and falls back to `index.html` (SPA history fallback); throws if the build output is missing | `server/vite.ts` lines 73–88 |

### 3.6 Inactive Scaffolding (declared, not runtime)

Detailed in §10. Summary: the Drizzle/PostgreSQL persistence stack, the session/auth dependency group, `pdf-parse`, and `ws` are all present in manifests and/or configuration but unreachable from any execution path.

## 4. Communication and Data Flows

All flows below were traced end-to-end in source.

**F1 — Profile upload (the core flow)**
`FileUploader` (HomeTab) → `useLinkedInProfile.uploadMutation` → `parsePDF()` (`client/src/lib/pdf-parser.ts`) sends `FormData` with field `pdf` via relative `POST /api/profile/upload` → multer validates MIME type and 5 MB cap into a memory buffer → `extractTextFromPdf(buffer)` **discards the buffer** and returns canned LinkedIn text → `extractProfileFromText()` applies regexes (name/headline/location/industry/company/title, naive skills/education/experience harvesting) → `storage.getProfile(1)` then create-or-update → JSON profile returned → written into the TanStack Query cache under `['/api/profile']`.

**F2 — Recommendations retrieval**
NetworkingTab/JobsTab mount → `useQuery(['/api/recommendations/networking'|'/jobs'])` → Express returns generated mock collections → cached 5 minutes; RefreshButton triggers `refetch()`. Note these endpoints do **not** consult the stored profile or interests — personalization is nominal.

**F3 — Interest suggestions and saving**
InterestsTab → `GET /api/interests/suggestions` (requires a stored profile, else 404 surfaced as empty suggestions) followed by `POST /api/interests` upserting topic/skill selections for user 1.

**F4 — Career goals**
JobsTab form → `GET`/`POST /api/career-goals`; GET returns hard-coded defaults when nothing stored.

**F5 — Bookmarking**
Card components (`job-card`, `course-card`, `post-card`, `recommendation-card`, `skill-card`) → `useSavedItems` → `POST/DELETE/GET /api/saved-items` with cache invalidation on success. This is why bookmarks and profiles vanish whenever the server restarts.

**F6 — Frontend delivery**
Development: browser loads Vite-transformed SPA + HMR websocket managed by Vite's own middleware (this is framework infrastructure, not application WebSocket usage). Production: static bundle from `dist/public` served by Express.

**F7 — Third-party asset loads (browser-side only)**
Avatars come from `randomuser.me`, company logos from `logo.clearbit.com`, course thumbnails from `images.unsplash.com` (all URLs embedded in the mock data of `server/routes.ts`), fonts from Google Fonts CDN (`client/index.html`). No server-side outbound calls occur to any third party; nothing authenticates to these services.

Directionality summary: client → server is request/response JSON (+ one multipart upload); server → client is JSON/static files; client → internet is passive image/font retrieval. **No bidirectional, queued, or asynchronous messaging infrastructure exists.**

## 5. Data Stores and State Ownership

| Store | What lives there | Lifetime | Owner | Status |
|---|---|---|---|---|
| `MemStorage` Maps (server process) | Demo user, extracted profile (user 1), interests, saved items, career goals | Until process exit | Express routes via `storage` singleton | Verified, sole active store |
| TanStack Query cache (browser tab) | Latest profile payload, recommendation sets, suggestions, saved-item list | Page session | Client hooks | Verified |
| `localStorage` (browser) | Theme only — key `networkpro-theme` via `ThemeProvider` (`main.tsx`) | Indefinite, per-browser | `theme-provider.tsx` | Verified |
| Filesystem (server) | Nothing at runtime — uploads stay in multer memory buffers; only build artifacts (`dist/`) touch disk | — | — | Verified absence |
| PostgreSQL | Tables `profiles`, `interests`, `saved_items`, `career_goals`, `users` per `shared/schema.ts` | Would be durable | Never connected | **Inactive scaffold** |

A residual `client/src/lib/storage.ts` implements a parallel localStorage persistence scheme with `networkpro-profile` / `-interests` / `-saved-items` / `-career-goals` keys, but **nothing imports this module** — it is dead code superseded by the server API hooks.

## 6. External Systems

| System | Role | Connection | Certainty |
|---|---|---|---|
| randomuser.me, logo.clearbit.com, images.unsplash.com | Placeholder imagery for mocked entities | Browser `<img>` fetches of hard-coded URLs | Verified (URLs in `server/routes.ts`) |
| Google Fonts CDN | UI typography (`Inter`) | `<link>` in `client/index.html` | Verified |
| Model/LLM provider | None. "AI" features are local mocks | — | Verified absence |
| LinkedIn API / OAuth | None. Brief explicitly substituted PDF upload for OAuth "for now" | — | Verified absence |
| Neon PostgreSQL | Intended DB provider (driver installed) | No connection string handling in app code | Declared only |

Per the anti-assumption discipline: no email, payment, storage-bucket, analytics, or telemetry integration exists in the repository.

## 7. Authentication, Authorization, and Trust Boundaries

- **There is no authentication or authorization implementation.** `passport`, `passport-local`, and `express-session` are declared dependencies but never imported; no login route, session middleware, or cookie issuance exists. The API trusts everything.
- Identity is stubbed: every route operates on hard-coded `userId = 1` with comments "For demo, we'll use userId 1". The seeded demo user record is never consulted by request handling.
- Trust boundary #1 — **browser ↔ Express**: plain same-origin HTTP/JSON; CORS is not configured (not needed given same-origin hosting); `credentials: "include"` on fetches is vestigial absent sessions.
- Trust boundary #2 — **upload surface**: the only externally supplied binary input is the PDF multipart field, constrained by multer `fileFilter` (MIME must be `application/pdf`) and `limits.fileSize = 5 MB`; because the buffer is never parsed, this surface is unusually inert.
- No secrets are committed; `README.md` documents `DATABASE_URL` and `SESSION_SECRET` env vars, but only `DATABASE_URL` is ever read — by the `drizzle-kit` CLI config, not the app. `SESSION_SECRET` has no consumer in code.

## 8. Configuration Boundaries

| Setting | Read by | Effect |
|---|---|---|
| `NODE_ENV` | `server/index.ts` (via `app.get("env")`), npm `start` script | Selects Vite-dev-middleware vs static hosting — the only switch that changes runtime topology |
| `REPL_ID` | `vite.config.ts` | Enables the Replit Cartographer dev plugin alongside the runtime-error overlay and theme-json plugin — evidence the app was authored on Replit (README: "Vibe coded with replit") |
| `DATABASE_URL` | `drizzle.config.ts` only | Required for the `npm run db:push` schema-push toolchain; throws if unset. **Unused by the running app** |
| Port / host | Hard-coded in `server/index.ts` (5000, `0.0.0.0`, `reusePort`) | Single-port serving of API + UI |
| Feature flags | None exist |

Configuration does not currently select providers or alter the architecture beyond the dev/prod frontend-serving branch; conceptually the DB layer is designed to become environment-bound via `DATABASE_URL` once wired.

## 9. Build, Runtime, and Deployment Boundaries

**Build pipeline (package.json scripts)**
- `dev` → `tsx server/index.ts`: TSX runs the Express server directly with Vite middleware attached (developer loop).
- `build` → `vite build` (client bundle → `dist/public`) **&&** `esbuild server/index.ts --platform=node --packages=external --bundle --format=esm --outdir=dist` (server bundle → `dist/index.js`).
- `start` → `NODE_ENV=production node dist/index.js`: one Node process hosting static client + API.
- `check` → `tsc` (type safety across `client/src`, `shared`, `server` per `tsconfig.json` path aliases `@/*`, `@shared/*`).
- `db:push` → `drizzle-kit push` (would materialize `shared/schema.ts` into PostgreSQL; no `migrations/` directory is committed, indicating it was never run against a live database — unknown whether a database was ever provisioned).

**Deployment topology evidenced by the repository**: a single long-running Node service bound to port 5000 — the Replit apps model. Replit-flavored dev plugins and the firewall comment support this origin. `theme.json` + `@replit/vite-plugin-shadcn-theme-json` feed design tokens into the Tailwind build.

**Deployment claims not backed by artifacts**: the README carries a Vercel badge (`career-pro-v2.vercel.app`) and states "Currently does not have any backend - vercel deployed frontend." The repo contains **no** `vercel.json`, no serverless functions, no `.replit` file, no Dockerfile, no Kubernetes/CI manifests, and no `Docker`-related scripts. Two readings are consistent with the code: (a) the backend *exists in the repo* but was simply never deployed to Vercel (so API-dependent features fail on that static hosting, matching the README caveat), or (b) some hosting configuration lives outside this repository. Either way, any production topology beyond "run `npm run build && npm start` on a Node host" is **unverified**. A stray `project.tar.gz` source snapshot sits at the repo root; it is packaging residue, not a deployment unit.

## 10. Declared-but-Inactive Technology (classification: apparently unused)

Each item below is traceable to manifests/config but has **zero import sites** in application code:

| Dependency | Declared purpose (implied) | Actual status |
|---|---|---|
| `drizzle-orm`, `@neondatabase/serverless`, `connect-pg-simple` | PostgreSQL/Neon persistence + session store | Schema definitions only (`shared/schema.ts`); no DB client instantiated, no queries executed |
| `passport`, `passport-local`, `express-session`, `memorystore` | Local-auth with session cookies | Not imported; no auth flow of any kind |
| `pdf-parse` | Server-side real PDF text extraction | Not imported; replaced by `extractTextFromPdf` simulation |
| `ws` (+ optional `bufferutil`) | WebSocket transport | Not imported; dev HMR is handled internally by Vite |
| `wouter` | Client routing | Not imported; navigation is tab state |
| `react-pdf` | PDF rendering | Imported only by `components/ui/pdf-viewer.tsx`, which itself is imported nowhere (transitively unused) |
| `client/src/lib/storage.ts` helpers | localStorage persistence for profile/items | Dead code — no importer |
| `ProfileEditor` component | Manual profile editing dialog | Defined in `profile-editor.tsx`, never mounted |

These represent an unfinished migration toward durable persistence and real authentication, and placeholder boundaries for genuine PDF processing — valuable signal about *intended* direction, misleading if counted as *current* architecture.

## 11. Architecture Classification Summary

| Element | Classification |
|---|---|
| React/Vite SPA with four tabs, shadcn/ui, TanStack Query over relative `/api` fetches | Verified |
| Express 4 single process on :5000 serving API + frontend; dev Vite middleware / prod static | Verified |
| Full REST endpoint inventory incl. multer-gated PDF upload | Verified |
| MemStorage in-memory Maps as the only active store; reset-on-restart semantics | Verified |
| Mock recommendation generators; simulated PDF extraction ignoring file contents | Verified |
| Theme persistence via browser localStorage | Verified |
| Third-party image/font CDNs consumed by the browser | Verified |
| Migration intent toward Drizzle-managed PostgreSQL (Neon driver) once `DATABASE_URL` is provided | Strongly inferred (schema + kit config + README env docs, but zero runtime wiring) |
| README's "no backend on Vercel" describing deployment state rather than missing code | Reasonable inference reconciling README vs. implemented server |
| Any live production deployment topology (Vercel and/or Replit) | Unverified — no deployment artifacts in repo |
| Whether a PostgreSQL database was ever provisioned/pushed | Unknown (no migrations directory committed) |
| Session/auth, real PDF parsing, WebSocket features | Apparently unused scaffolding |

## 12. Documented vs Implemented Reconciliation

| Claim (README / brief) | Implementation reality | Resolution |
|---|---|---|
| Tech stack: "Database: PostgreSQL with Drizzle ORM" | Drizzle schema + kit config present; runtime storage is in-memory Maps | Documentation describes the target platform, not current behavior; treat PostgreSQL as planned |
| "Currently does not have any backend — vercel deployed frontend" | A complete Express backend ships in `server/` and is the only store of user state | Statement is accurate only for the Vercel static deployment context, not the repository |
| "AI-powered recommendations / AI-driven career mapping" (also HomeTab copy) | Deterministic hard-coded generators; simulated extraction | UI marketing language overstates the mechanism |
| Persistence of saved recommendations (brief: "persistent storage") | Saved items live in volatile memory server-side; localStorage alternative is dead code | Requirement unmet in implementation |
| Naming: repo `CareerPro-v2`, product `NetworkPro`, package name `rest-express` | Consistent app branding in UI/meta tags as NetworkPro | Cosmetic lineage from the Replit `rest-express` template |

## 13. Architectural Unknowns

- No statement in the repository establishes where, or whether, this exact stack is currently hosted; both the Vercel badge target and any Replit instance are outside repository evidence.
- No test suite, CI pipeline, health endpoint, or observability instrumentation exists — runtime verification beyond code reading is not possible from the repo alone.
- The single-user (`userId = 1`) model means multi-user behavior is architecturally undefined until identity and durable storage are introduced.
- Whether the Drizzle schema has ever been applied to a real database (and with which provider) cannot be determined from committed artifacts.