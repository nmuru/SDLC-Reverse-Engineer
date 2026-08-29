# Technology Architecture

## Overview

NetworkPro is a monorepo web application built with React and Node.js that provides AI‑powered career networking recommendations. The architecture follows a conventional server‑side rendered single‑page application pattern where a single Express server serves both the React frontend and the REST API on the same port.

## Architecture Diagram

```mermaid
flowchart LR
    User["Browser\nUser"]
    
    subgraph Runtime["Node.js Runtime\n(Port 5000)"]
        Express["Express Server\nserver/index.ts"]
        subgraph API["API Routes\nserver/routes.ts"]
            ProfileAPI["Profile API\nPOST /api/profile/upload\nGET /api/profile\nPUT /api/profile"]
            InterestsAPI["Interests API\nGET /api/interests\nPOST /api/interests\nGET /api/interests/suggestions"]
            RecommendationsAPI["Recommendations API\nGET /api/recommendations/networking\nGET /api/recommendations/jobs"]
            SavedItemsAPI["Saved Items API\nGET /api/saved-items\nPOST /api/saved-items\nDELETE /api/saved-items/:id"]
            CareerGoalsAPI["Career Goals API\nGET /api/career-goals\nPOST /api/career-goals"]
        end
        subgraph Frontend["Frontend (Vite Dev Server)"]
            ViteDevServer["Vite Middleware\nserver/vite.ts"]
            ReactApp["React Application\nclient/src/"]
            TanStackQuery["TanStack Query\nState & Caching"]
            localStorage["localStorage\nclient/src/lib/storage.ts"]
        end
        Storage["MemStorage\nserver/storage.ts\n(In-Memory)"]
    end

    User <-->|HTTP/HTML/JSON| Express
    Express -->|multipart/form-data| ProfileAPI
    Express -->|JSON REST API| User
    ReactApp -->|useQuery/useMutation| TanStackQuery
    TanStackQuery -->|fetch()| API
    API -->|Read/Write| Storage
    ReactApp -->|setItem/getItem| localStorage

    style User fill:#e1f5fe,stroke:#0277bd
    style Express fill:#e8f5e9,stroke:#2e7d32
    style Storage fill:#fff3e0,stroke:#ef6c00
    style localStorage fill:#fff3e0,stroke:#ef6c00
```

## Major Runtime Components

### 1. Frontend Application

- **Technology:** React 18, TypeScript, Vite, Tailwind CSS, Radix UI (shadcn/ui)  
- **Location:** `client/src/`  
- **Entry Point:** `client/src/main.tsx` → `client/src/App.tsx`  
- **Responsibility:** Renders the user interface, manages local UI state, and communicates with the backend REST API. The frontend is the sole user‑facing component of the application.  
- **Key evidence:**  
  - `package.json` declares React 18 (`"react": "^18.3.1"`), Vite (`"vite": "^5.4.14"`), Tailwind CSS (`"tailwindcss": "^3.4.14"`).  
  - `client/src/main.tsx` mounts the React application to the `#root` DOM element.  
  - `client/src/App.tsx` wraps the application in `QueryClientProvider` from `@tanstack/react-query`.  
  - `vite.config.ts` specifies `root: path.resolve(__dirname, "client")` and `build.outDir: "dist/public"`.  
  - UI components are sourced from `@radix-ui/react-*` packages.  
- **Runtime context:**  
  - **Development:** Vite dev server runs in middleware mode within the Express process (`server/vite.ts`, `setupVite()`). Vite intercepts requests and serves HMR‑enabled assets during development.  
  - **Production:** Express serves pre‑built static assets from `dist/public` via `serveStatic()`.  
- **Principal inputs:** API responses, file uploads (PDF), user interactions.  
- **Principal outputs:** User interface, API requests.

### 2. API Server

- **Technology:** Node.js, Express.js, TypeScript  
- **Location:** `server/`  
- **Entry Point:** `server/index.ts`  
- **Responsibility:** Serves the REST API for profile management, interests, recommendations, saved items, and career goals. Also serves the compiled frontend in production and the Vite dev server in development.  
- **Key evidence:**  
  - `server/index.ts` creates an Express application, registers routes, and listens on port 5000.  
  - `server/routes.ts` defines all API endpoints using Express router patterns.  
  - `server/vite.ts` provides `setupVite()` for development and `serveStatic()` for production.  
  - The server uses JSON body parsing (`express.json()`) and URL‑encoded parsing (`express.urlencoded()`).  
- **Runtime context:** Single Node.js process. Both the API and frontend are served on the same port (5000).  
- **Principal inputs:** HTTP requests, multipart form data (PDF uploads).  
- **Principal outputs:** JSON API responses, static files (production).

### 3. Data Persistence Layer

- **Technology:** In‑memory storage (`MemStorage`), optional PostgreSQL via Drizzle ORM  
- **Location:** `server/storage.ts`  

| Store | Implementation | Location | Entity |
|------|----------------|----------|--------|
| User storage | `Map<number, User>` | `MemStorage.users` | User credentials |
| Profile storage | `Map<number, Profile>` | `MemStorage.profiles` | LinkedIn profile data |
| Interests storage | `Map<number, Interest>` | `MemStorage.interestsList` | User interests and skills |
| Saved items storage | `Map<number, SavedItem>` | `MemStorage.savedItemsList` | Bookmarked items |
| Career goals storage | `Map<number, CareerGoal>` | `MemStorage.careerGoalsList` | Career objectives |
| Client‑side UI state | Browser `localStorage` | `client/src/lib/storage.ts` | Theme, saved items (local) |

- **Active storage (verified):** `MemStorage` class using JavaScript `Map` objects. This is the actively used persistence layer.  
- **Defined but inactive:** Drizzle ORM schema (`shared/schema.ts`) with PostgreSQL configuration (`drizzle.config.ts`) referencing `DATABASE_URL`. No code in `server/storage.ts` initializes a database connection or invokes Drizzle ORM methods.  
- **Key evidence:**  
  - `server/storage.ts` exports `const storage = new MemStorage()` — the singleton instance used by all route handlers.  
  - `MemStorage` is a full in‑memory implementation using `Map<number, T>` for each entity (users, profiles, interests, savedItems, careerGoals).  
  - `shared/schema.ts` defines `pgTable` schemas using Drizzle ORM, but these are only used for type inference (`$inferSelect`, `$inferInsert`).  
  - `drizzle.config.ts` requires `DATABASE_URL` but this configuration is used exclusively for the `db:push` npm script (schema migration tool), not runtime data access.  
- **Persistence classification:** Data stored in `MemStorage` persists only for the lifetime of the Node.js process. Data stored in the browser’s `localStorage` persists across browser sessions but is local to each user’s browser and is not shared with the server.

### 4. Client‑Side State Management

- **Technology:** TanStack Query (React Query), `localStorage`  
- **Location:** `client/src/lib/queryClient.ts`, `client/src/lib/storage.ts`  
- **Responsibility:** Manages server state (API data fetching/caching) and local client preferences.  
- **Key evidence:**  
  - `queryClient` in `client/src/lib/queryClient.ts` is configured with `QueryClientProvider` wrapping the entire application (`App.tsx`).  
  - Custom hooks (`useLinkedInProfile.ts`, `useInterests.ts`, `useRecommendations.ts`, `useSavedItems.ts`, `useCareerGoals.ts`) abstract API access through TanStack Query.  
  - `client/src/lib/storage.ts` provides `localStorage` helpers for UI state (theme preference, locally saved items).  
- **Configuration:** TanStack Query is configured with `staleTime: Infinity` for profile queries, `refetchOnWindowFocus: false`, and `retry: false`.

### 5. Shared Schema Layer

- **Technology:** TypeScript, Drizzle ORM schema definitions, Zod validation schemas  
- **Location:** `shared/schema.ts`  
- **Responsibility:** Defines entity types and database schemas shared between the server and (potentially) the client through path aliases.  
- **Key evidence:**  
  - `tsconfig.json` defines path aliases: `"@shared/*": ["./shared/*"]`.  
  - `vite.config.ts` defines `alias: { "@shared": path.resolve(__dirname, "shared") }`.  
  - `server/storage.ts` imports types from `@shared/schema`.  
  - Schema includes: `users`, `profiles`, `interests`, `savedItems`, `careerGoals`.

## Communication Flows

### User Interaction Flow

1. **Browser request** → Express server on port 5000.  
2. **Development:** Vite middleware intercepts and serves React assets with HMR.  
3. **Production:** Express.static serves pre‑built files from `dist/public`.  
4. **React app loads** → TanStack Query fetches initial data from API endpoints.  
5. **User interacts** → React components trigger TanStack Query mutations or `localStorage` updates.  
6. **API calls** → `fetch()` requests to `/api/*` endpoints.  
7. **Server processes** → Express routes handle requests, interact with `MemStorage`.  
8. **Response** → JSON returned to client, TanStack Query updates cache.

### Profile Upload Flow

1. User selects PDF file in `FileUploader` component (`client/src/components/ui/file-uploader.tsx`).  
2. `useLinkedInProfile` hook calls `parsePDF()` from `client/src/lib/pdf-parser.ts`.  
3. `parsePDF()` sends `multipart/form-data` POST to `/api/profile/upload`.  
4. Server receives file via `multer` middleware (5 MB limit, PDF‑only filter).  
5. `extractTextFromPdf()` in `server/routes.ts` returns simulated LinkedIn profile text.  
6. `extractProfileFromText()` parses name, headline, skills, education, experience using regex.  
7. Profile stored/updated via `storage.createProfile()` or `storage.updateProfile()`.  
8. Server returns JSON profile data to client.  
9. TanStack Query cache updated with new profile data.

### Recommendation Generation Flow

1. User navigates to Networking or Jobs tab.  
2. `useNetworkingRecommendations` or `useJobRecommendations` hook fires.  
3. GET request to `/api/recommendations/networking` or `/api/recommendations/jobs`.  
4. Server generates mock data using `generatePeopleToFollow()`, `generateJobOpenings()`, etc.  
5. All recommendation generators return hardcoded mock data — no real ML, AI, or profile‑based filtering.  
6. Response cached by TanStack Query with 5‑minute `staleTime`.

## External Systems

### Verified External Dependencies

| External System | Purpose | Evidence |
|----------------|---------|-----------|
| `randomuser.me/api/portraits/` | Avatar images for mock recommendation profiles | `server/routes.ts` lines 29, 35, 41, 47, 54, 71, 77, 83, 89, 95, 114, 124, 134, 144, 154 |
| `logo.clearbit.com/` | Company logos in job recommendations | `server/routes.ts` lines 172, 183, 194, 205, 216 |
| `fonts.googleapis.com` | Inter font for typography | `client/index.html` line 9 |

### Unverified / Declared But Inactive

| Declared System | Stated Purpose | Evidence of Activation |
|----------------|----------------|------------------------|
| PostgreSQL | Persistent data storage | `drizzle.config.ts` requires `DATABASE_URL`, but no runtime DB initialization found in `server/storage.ts` |
| `@neondatabase/serverless` | Neon serverless PostgreSQL driver | Present in `package.json` dependencies, but no imports or usage found in server code |
| `passport` / `passport-local` | User authentication | Present in `package.json` dependencies, but no authentication routes or middleware found in `server/routes.ts` |
| `express-session` / `memorystore` | Session management | Present in `package.json` dependencies, but no `app.use(session())` initialization in `server/index.ts` |
| AI/ML services | Career recommendations | Declared in README ("AI‑powered"), but all recommendation endpoints return hardcoded mock data with no AI integration |

## Environment Configuration

| Variable | Required | Usage | Evidence |
|----------|----------|-------|----------|
| `DATABASE_URL` | Required for `db:push` script only | Drizzle Kit schema migration | `drizzle.config.ts` throws if missing, but not checked at runtime by `server/index.ts` |
| `SESSION_SECRET` | Optional | Session middleware configuration | Referenced in README but not used in server code |
| `NODE_ENV` | Optional | Vite plugin activation, production build detection | `vite.config.ts` and `server/index.ts` check this value |
| `REPL_ID` | Optional | Replit‑specific Vite plugin activation | `vite.config.ts` checks this for `@replit/vite-plugin-cartographer` |

## Deployment Boundaries

- **Verified deployment targets:**  
  - **Vercel:** Frontend/static assets (referenced in README badge and `vercel.app` domain).  
  - **Replit:** Full stack (referenced in README badge, evidenced by `REPL_ID` checks in `vite.config.ts`).  

- **Runtime boundary:** Single Node.js process. The Express server handles both API and static file serving. No containerization (no `Dockerfile` or `docker-compose.yml` present).  

- **Build boundary:**  
  - Frontend build: `vite build` outputs to `dist/public`.  
  - Server build: `esbuild server/index.ts` bundles the Node.js server to `dist/`.  
  - Production start: `NODE_ENV=production node dist/index.js`.

## Technology Stack Summary

| Layer | Technology | Evidence |
|-------|-------------|----------|
| UI Framework | React 18 | `package.json`: `"react": "^18.3.1"` |
| Language | TypeScript 5.6 | `package.json`: `"typescript": "5.6.3"` |
| Build Tool | Vite 5 | `package.json`: `"vite": "^5.4.14"` |
| Styling | Tailwind CSS 3 | `package.json`: `"tailwindcss": "^3.4.14"` |
| UI Components | Radix UI + shadcn/ui | `package.json`: `@radix-ui/react-*` packages |
| HTTP Client | TanStack Query 5 | `package.json`: `"@tanstack/react-query": "^5.60.5"` |
| Routing | Wouter | `package.json`: `"wouter": "^3.3.5"` (present but not actively used in source) |
| Server Framework | Express 4 | `package.json`: `"express": "^4.21.2"` |
| Server Runtime | Node.js | `package.json` scripts use `node` and `tsx` |
| ORM | Drizzle ORM | `package.json`: `"drizzle-orm": "^0.39.1"`, `drizzle.config.ts` |
| Validation | Zod | `package.json`: `"zod": "^3.23.8"`, used in schema generation |
| File Upload | Multer | `package.json`: `"multer": "^1.4.5-lts.2"`, `server/routes.ts` |
| PDF Processing | pdf‑parse | `package.json`: `"pdf-parse": "^1.1.1"` (present but not imported/used in `routes.ts`) |
| Database | PostgreSQL (configured, inactive) | `drizzle.config.ts` dialect `"postgresql"` |

## Architecture Classification

| Element | Classification | Evidence |
|---------|----------------|----------|
| Express server as sole backend | **Verified** | `server/index.ts` is the only server entry point |
| React SPA as sole frontend | **Verified** | `client/src/App.tsx` is the only frontend entry point |
| Single‑port architecture | **Verified** | `server/index.ts` listens on port 5000 for both API and static files |
| MemStorage as active persistence | **Verified** | `server/storage.ts` exports `new MemStorage()` used by all routes |
| PostgreSQL as active persistence | **Unverified** | Schema exists but no DB connection initialized at runtime |
| Neon serverless database | **Unverified** | Package declared but no imports found |
| Passport authentication | **Unverified** | Package declared but no auth routes or middleware found |
| Express session management | **Unverified** | Package declared but no `session()` middleware initialized |
| AI/ML recommendation engine | **Unverified** | All recommendation endpoints return hardcoded mock data |
| PDF parsing from uploaded file | **Unverified** | `pdf-parse` package present; `extractTextFromPdf()` returns mock text, not actual PDF content |
| Vercel deployment | **Verified (documentation)** | README badge links to `career-pro-v2.vercel.app` |
| Replit deployment | **Verified (documentation + config)** | README badge, `REPL_ID` check in `vite.config.ts` |
| Docker containerization | **Not present** | No Dockerfile or docker‑compose files found |

## Key Architectural Observations

- **In‑memory only persistence:** All user data (profiles, interests, saved items, career goals) stored in `MemStorage` is lost when the Node.js process restarts. No database connection is established or queried at runtime despite Drizzle ORM and PostgreSQL configuration being present.  

- **Mock recommendation data:** The networking and job recommendation endpoints (`/api/recommendations/networking`, `/api/recommendations/jobs`) return hardcoded mock data. The uploaded profile has no influence on the recommendations returned, contradicting the README’s claim of “AI‑powered” recommendations.  

- **Simulated PDF processing:** The `extractTextFromPdf()` function in `server/routes.ts` returns a hardcoded mock LinkedIn profile regardless of the actual uploaded PDF content. The `pdf-parse` package is listed as a dependency but is not imported or used anywhere in the codebase.  

- **Single‑user assumption:** All API endpoints hardcode `userId = 1`, treating every request as belonging to the same demo user. No multi‑user isolation or authentication mechanism exists.  

- **Dual `localStorage` usage:** The application stores data in two separate `localStorage` namespaces — one managed by `client/src/lib/storage.ts` (client‑side saved items, theme preference) and one by `server/storage.ts` (server‑side `MemStorage` with a fixed demo user). These represent two independent data stores with no synchronization.  

- **Decentralized state management:** Profile data flows through the server `MemStorage` (server‑side), while UI preferences and local saved items flow through the browser’s `localStorage` (client‑side). The theme preference is also stored in `localStorage` via the theme provider.