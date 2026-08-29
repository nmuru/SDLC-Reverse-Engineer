# Requirements Specification — NetworkPro (CareerPro-v2)

## 1. Basis and Scope

This specification reconstructs the requirements that the repository indicates the system was designed to satisfy. It draws on three classes of evidence:

1. **Stated product intent** — the original project brief preserved in `attached_assets/Pasted-Project-Title-NetworkPro-Overview-...txt` (project title NetworkPro), which defines scope, features, and constraints.
2. **Documented intent** — `README.md`, including feature descriptions, tech-stack claims, and environment setup instructions.
3. **Implemented behavior** — executable evidence from `server/routes.ts`, `server/storage.ts`, `server/index.ts`, `shared/schema.ts`, and the client under `client/src` (pages, hooks, components).

Each requirement is classified:

| Tag | Meaning |
|---|---|
| **[V]** | Verified — directly enforced by executable behavior or explicitly stated in project documents and consistent with implementation |
| **[I]** | Inferred — strongly implied by multiple implementation artifacts but never explicitly stated |
| **[U]** | Uncertain — plausible interpretation with insufficient evidence to establish confidently |

A central caveat governs this whole specification: the application is an explicitly labeled demo (`vibe coded with replit. One shot created` per README; repeated `For demo` comments in code). Several headline capabilities are therefore **simulated** rather than real. Those simulations are documented below as requirements of the delivered system, not as aspirations of the original brief.

---

## 2. Actors

| Actor | Description | Evidence |
|---|---|---|
| Single demo user | All server-side operations execute against the hard-coded identity `userId = 1`; there is no login flow. A seed user `demo/password` is created in memory at startup. | `server/routes.ts` (comment `For demo, we'll use userId 1` on every route); `server/storage.ts` constructor |
| Anonymous browser visitor | Any visitor of the web UI can perform all actions; no authentication gate exists. | Absence of any auth middleware across all routes |

The original brief anticipated replacing OAuth with PDF upload for now ([U] for whether OAuth was planned later; no further evidence exists in the repository).

---

## 3. Functional Requirements

### 3.1 Profile ingestion (LinkedIn PDF upload)

- **FR-1 [V]** The system must provide a guided upload step on the Home tab that lets the user select a PDF representing their LinkedIn profile via file picker or drag-and-drop, showing selected-file metadata (name, size in MB) before submission. Evidence: `client/src/components/ui/file-uploader.tsx`.
- **FR-2 [V]** The system must instruct users how to obtain the source artifact, i.e. how to export a LinkedIn profile as PDF. Evidence: instruction banner in `file-uploader.tsx` (Go to your LinkedIn profile → More button → Save to PDF).
- **FR-3 [V]** When the user submits a file, the system must upload it to `POST /api/profile/upload` as multipart form data and present an analysis-in-progress state while processing. Evidence: `client/src/lib/pdf-parser.ts` (`parsePDF`), processing view in `client/src/pages/HomeTab.tsx`.
- **FR-4 [V]** The upload handler must reject requests with no attached file (HTTP 400, message `No file uploaded`). Evidence: `server/routes.ts:515-517`.
- **FR-5 [V]** The upload pipeline must enforce, server-side, a maximum file size of 5 MB and a MIME type restriction to `application/pdf`. Non-PDF uploads must be rejected with an error response conveying `Only PDF files are allowed`. Evidence: multer configuration, `server/routes.ts:8-19`; error translation in `server/index.ts:42-48`.
- **FR-6 [V]** The client must independently enforce the 5 MB size limit before upload. File-type checking may be deliberately relaxed for the demo: non-PDF selections trigger a warning toast but are still submitted. Evidence: `validateFile` in `file-uploader.tsx:40-65` (explicit comment: `Return true anyway for the demo`).
- **FR-7 [V]** For this release, the system must simulate profile extraction: regardless of the uploaded file contents, the pipeline must use a fixed sample LinkedIn profile text rather than parsing the actual document. Evidence: `extractTextFromPdf(buffer)` ignores its argument and logs `Simulating PDF extraction`; dependency `pdf-parse` is declared but never imported.
- **FR-8 [V]** Extraction failure must be non-fatal: even if extraction fails, a minimal fallback profile (placeholder name/headline/skills) must be produced so the workflow can continue. Evidence: try/catch fallback in `routes.ts:349-356`.
- **FR-9 [V]** The system must derive structured profile fields (name, headline, location, industry, current company, current job title, skills — capped at 10, education institutions, experience roles) from the extracted text, substituting clearly-labeled placeholder values (e.g. `Company from LinkedIn`) for fields that cannot be located. Evidence: `extractProfileFromText`, `routes.ts:359-442`.
- **FR-10 [V]** Successfully processed profile data must replace the previously stored profile for the current user (create if absent, update if present) and be returned to the client. Evidence: create-or-update logic in `routes.ts:528-545`.
- **FR-11 [V]** The system must offer a bypass that populates the workflow with demonstration data without requiring a real file upload. Evidence: Continue with Demo Data button constructing a dummy file in `file-uploader.tsx:108-111`.
- **FR-12 [V]** On success or failure of upload/update operations, the system must notify the outcome through toast messages. Evidence: mutation callbacks in `client/src/hooks/useLinkedInProfile.ts`.

### 3.2 Profile management

- **FR-13 [V]** After a profile exists, the Home tab must render an analysis-complete confirmation, the structured profile details, and a prominent continuation action toward the Career Interests step. Evidence: `HomeTab.tsx` post-upload branch.
- **FR-14 [V]** The system must let the user manually edit the profile: name, headline, location, industry, job title, company; add/remove skills; add/remove education entries (institution, degree, years); add/remove experience entries (title, company, duration). Evidence: `client/src/components/ui/profile-editor.tsx` (dialog with add/remove controls).
- **FR-15 [V]** Manual edits must be persisted via `PUT /api/profile` and reflected immediately in the UI. If no profile exists yet, the request must fail with HTTP 404 (`Profile not found`) rather than creating one. Evidence: `useLinkedInProfile.updateMutation`; `server/routes.ts:571-589`.
- **FR-16 [V]** Profile retrieval (`GET /api/profile`) must return HTTP 404 when no profile exists for the user. Evidence: `routes.ts:553-568`.

### 3.3 Career interests

- **FR-17 [V]** The Career Interests tab must request AI-style interest suggestions derived from the stored profile. The endpoint must refuse to generate suggestions when no profile exists (HTTP 404). Evidence: `GET /api/interests/suggestions`, `routes.ts:592-608`. *Qualification:* suggestions are generated from a fixed catalog and do not depend on profile contents (`suggestInterests(profile)` ignores its parameter) — personalization is simulated only [V for behavior, U for intended depth].
- **FR-18 [V]** Suggestions must cover two categories — topics and skills — each pre-seeded with selection states so the user sees sensible defaults. Evidence: `suggestInterests`, `routes.ts:445-509`; rendering in `InterestsTab.tsx`.
- **FR-19 [V]** The user must be able to toggle topic and skill selections individually, add free-text custom interests (Enter key or button), and remove custom interests. Duplicate custom entries must be rejected with feedback. Evidence: `InterestsTab.tsx` handlers.
- **FR-20 [V]** Existing saved interests must be re-applied to the suggestion checkboxes when the tab loads, and custom interests previously saved must be restored as removable chips. Evidence: effects in `InterestsTab.tsx:129-153`.
- **FR-21 [V]** Continuing past the tab must persist the union of selected suggested topics, custom interests, and selected skills as a single interests record (create-or-update keyed to the user) and navigate onward to Networking. Evidence: `handleSaveAndContinue`, `POST /api/interests` upsert at `routes.ts:611-639`.
- **FR-22 [V]** Retrieving interests when none exist must return empty collections instead of an error. Evidence: `routes.ts:642-657`.
- **FR-23 [V]** Live counts of selected topics (including custom interests) and skills must be displayed during editing. Evidence: badges bound to `selectedCount` in `InterestsTab.tsx`.

### 3.4 Networking recommendations

- **FR-24 [V]** The Networking tab must present three recommendation categories, each populated with a fixed set of five curated demo entries: People to Follow, People to Connect With, and Trending Posts (with author, position, reaction/comment counts). Evidence: `GET /api/recommendations/networking`, generator functions `generatePeopleToFollow`, `generatePeopleToConnect`, `generateTrendingPosts`; `NetworkingTab.tsx`.
- **FR-25 [V]** Recommendations must be fetchable over HTTP independent of profile/interest state; generation does not consult either. Evidence: no reads of storage in the networking handler.
- **FR-26 [V]** Each recommended person card must support Follow or Connect style primary actions (acknowledged via toast only — no external network integration), Save-for-Later toggling, and Ignore (removing the card from the current view with confirmation toast). Evidence: `RecommendationCard.tsx`, `NetworkingTab.tsx` `handleFollow`/`handleConnect`.
- **FR-27 [V]** The category lists must initially display a subset (3 people per people-list, 2 posts) and expose a Show More control that reveals remaining items incrementally (+3 / +2 respectively) until exhausted. Evidence: visibility counters in `NetworkingTab.tsx`.
- **FR-28 [V]** The user must be able to refresh recommendations manually; refreshing re-invokes retrieval but returns the same static catalog (no new data is synthesized per request). Evidence: `RefreshButton` wiring to `refetch` in `useRecommendations.ts`.
- **[Gap noted under Section 10]** The brief also demanded Experts to Consult; no such category exists in the API, types, or UI.

### 3.5 Jobs and career goals

- **FR-29 [V]** The Jobs tab must allow definition of career goals through constrained choice lists: Desired Role (Product Manager / Senior Product Manager / Director of Product / VP of Product), Industry (Technology / Healthcare / Finance / Education), Location (San Francisco CA / Remote / New York NY / Seattle WA), Salary Range ($120k-150k / $150k-180k / $180k-210k / $210k+). Free-text goals are not supported. Evidence: Select options in `JobsTab.tsx:91-150`.
- **FR-30 [V]** Goals must be persistable as a single record per user (create-or-update) via `POST /api/career-goals`; when none exist, retrieval must return built-in defaults matching those choices. Evidence: `routes.ts:698-749`.
- **FR-31 [V]** Updating goals must refresh the displayed job recommendations afterward. Evidence: `handleUpdateGoals` calls `refreshRecommendations()` after saving.
- **FR-32 [V]** The Jobs tab must present three recommendation groups of five static demo entries: Top Job Openings (with title, company, location, posting age, applicant count, salary range, match percentage), Recommended Courses (provider, rating, review count), and Skills to Develop (demand badge, description, quantified advantage claim such as +35% job opportunities). Evidence: `GET /api/recommendations/jobs`; generators `generateJobOpenings`, `generateCourses`, `generateSkills`; `JobsTab.tsx`.
- **FR-33 [V]** Job cards must support Apply Now (simulated — toast acknowledgment only), Save/Unsave, and Ignore behaviors, with visual match-strength styling (green >= 90%, emerald >= 80%, yellow >= 70%, gray otherwise). Evidence: `JobCard.tsx` `getBadgeColor`.
- **FR-34 [V]** Courses and skill cards must support Save/Unsave and Ignore behaviors. Evidence: `CourseCard.tsx`, `SkillCard.tsx`.
- **[Gap noted under Section 10]** The brief demanded Top 5 Recruiters to Connect With and Connect actions on recruiters; neither appears in API, types, or UI.
- **FR-35 [V]** Job/course/skill lists must use the same incremental Show More pattern (initially 3 visible, +3 per activation). Evidence: counters in `JobsTab.tsx`.

### 3.6 Saved items (Save for Later repository)

- **FR-36 [V]** The system must persist bookmarked recommendations with their full payload so they outlive page interactions within the running process: creation via `POST /api/saved-items`, deletion via `DELETE /api/saved-items/:id` (HTTP 404 when identifier unknown), and listing via `GET /api/saved-items` with optional filtering by item type query parameter. Evidence: `routes.ts:752-800`.
- **FR-37 [V]** Bookmarkable content types must be limited to person, job, course, post, and skill; toggling save-state must reflect immediately (bookmark icon fill state, toast feedback) and invalidation must re-sync other views of the collection. Evidence: `SavedItem.itemType` union in `client/src/types/index.ts:123`; hook logic in `hooks/useSavedItems.ts`.
- **FR-38 [V]** Deletion of a saved item must confirm removal only for items actually stored; unknown identifiers must yield an error surfaced to the user. Evidence: `deleteSavedItem` boolean return mapped to 404 at `routes.ts:771-785`.

### 3.7 Workflow navigation and presentation

- **FR-39 [V]** The UI must offer four top-level tabs — Home, Career Interests, Networking, Jobs — reachable by direct click from any tab, with an active-tab indicator; a sequential wizard order (Home → Interests → Networking → Jobs) is offered through forward/back buttons but is not enforced. Evidence: `App.tsx` tab switch; `components/layout/TabNavigation.tsx`.
- **FR-40 [V]** Long-running fetches must display spinners/skeleton-style progress states including explanatory copy, e.g. Analyzing Your Professional Profile during upload and processing. Evidence: loading branches in all four tab pages.
- **FR-41 [V]** All outbound failures (fetch or HTTP non-OK) must surface the failure to the user rather than failing silently. Evidence: `throwIfResNotOk` in `lib/queryClient.ts`; destructive toasts in hooks.
- **FR-42 [V]** The interface must support light and dark themes, user-toggleable from the header, with the choice remembered across sessions in browser local storage under key `networkpro-theme` (default light). Evidence: `lib/theme-provider.tsx`; `main.tsx` provider wiring; Header toggle.

---

## 4. Business and Domain Rules

- **BR-1 [V] Single demo identity:** every operation acts on exactly one implicit user (id 1). There are no multi-user separation requirements in force. Evidence: hard-coded `userId = 1` throughout `routes.ts`.
- **BR-2 [V] One-of-each user records:** the system maintains at most one profile, one interests record, and one career-goals record per user; repeated submissions update in place (upsert-by-user semantics). Evidence: get-then-create-or-update sequences in `routes.ts`; lookup by userId in `MemStorage`.
- **BR-3 [V] Unlimited typed bookmarks:** unlike profiles/interests/goals, saved items accumulate as an append/delete collection with no deduplication requirement at the API level. Evidence: `createSavedItem` always inserts; dedupe is incidental client-side via `isItemSaved` checks.
- **BR-4 [V] Recommendation volume:** each recommendation category delivers exactly five curated entries; pagination reveals them progressively but no mechanism supplies additional content. Evidence: five-element arrays in every generator; slice-based Show More.
- **BR-5 [V] Never-fail extraction and completion defaults:** profile extraction and career-goal retrieval substitute predefined demo defaults in place of absent data, keeping the journey completable even without genuine inputs. Evidence: fallback strings in `extractProfileFromText`; default goal object at `routes.ts:736-741`.
- **BR-6 [V] Skill capping:** extracted skill lists are trimmed to at most ten entries; individual entries must be shorter than 50 characters to qualify. Evidence: filters in `extractProfileFromText`.
- **BR-7 [I] Presentation thresholds for match strength:** percentage-based match scores drive tiered badge coloring (>=90 / >=80 / >=70 bands). Inferred from the deterministic mapping in `JobCard.getBadgeColor`; no requirement document mentions thresholds.
- **BR-8 [U] Seeded credentials:** storage seeds username `demo` password `password`. With no authentication surface exposed, these credentials appear vestigial (perhaps scaffolding for future auth) — purpose cannot be established from the repository.
- **BR-9 [V] Profile-first gating for interests:** interest suggestions require an existing profile; interests and recommendations themselves do not. This encodes the brief's intended sequence (profile -> interests -> networking/jobs) at exactly one boundary.

---

## 5. Interface Requirements

### 5.1 HTTP API contract [V]

All routes are unauthenticated and speak JSON except the multipart upload.

| Method & Path | Input | Success output | Failure behavior |
|---|---|---|---|
| POST `/api/profile/upload` | Multipart field `pdf` (PDF, <= 5 MB) | Full profile object | 400 no file; error response on rejection/failure |
| GET `/api/profile` | – | Profile object | 404 `Profile not found` |
| PUT `/api/profile` | JSON body (profile fields) | Updated profile | 404 when absent |
| GET `/api/interests/suggestions` | – | `{ suggestedTopics[], suggestedSkills[] }` incl. preselection flags | 404 without profile |
| POST `/api/interests` | JSON `{ topics[], skills[] }` | Stored interests record | 500-class error responses |
| GET `/api/interests` | – | `{ topics[], skills[] }` | Empty arrays when absent |
| GET `/api/recommendations/networking` | – | `{ peopleToFollow, peopleToConnect, trendingPosts }` (5 each) | Error response on failure |
| GET `/api/recommendations/jobs` | – | `{ jobOpenings, recommendedCourses, skillsToDevelop }` (5 each) | Error response on failure |
| POST `/api/career-goals` | JSON goal fields | Stored goals record | Error response on failure |
| GET `/api/career-goals` | – | Goals record or fixed defaults | Error response on failure |
| POST `/api/saved-items` | JSON `{ itemType, itemId, itemData }` | Created record | Error response on failure |
| GET `/api/saved-items?type=` | Optional type filter | Array of records | Error response on failure |
| DELETE `/api/saved-items/:id` | Numeric path id | `{ success: true }` | 404 when unknown |

Cross-cutting interface requirements:

- **INT-1 [V]** Every API interaction must carry cookies (`credentials: include` on both mutations and queries), anticipating cookie-based sessions. No server component currently issues or consumes a session cookie — readiness only, not an active contract [I].
- **INT-2 [V]** Non-OK responses must raise client-side errors embedding the numeric status and response body text. Evidence: `throwIfResNotOk`.
- **INT-3 [V]** Update/goal/interest request bodies are accepted as opaque JSON merged directly onto stored records; no runtime schema validation occurs despite Zod insert schemas being defined in `shared/schema.ts`. This is a deliberate contract permissiveness (or an omission) — see Section 10.
- **INT-4 [V]** All API traffic must be logged with method, path, status, duration, and a truncated (80-char) snapshot of the JSON response. Evidence: middleware in `server/index.ts:9-37`.
- **INT-5 [V]** In development the SPA must be served through Vite with HMR (all unmatched paths returning transformed `index.html`); in production a built static bundle must be served with index.html fallback for client-side routes. Evidence: `server/vite.ts`.

### 5.2 Browser/UI interfaces [V]

- Document title/description: NetworkPro - Career Networking App framing the product externally (`client/index.html`).
- Upload widget accepts `.pdf` files only via the picker filter, communicates the 5 MB cap in copy, and supports drag-and-drop affordances (visual active state).
- Toast notifications constitute the mandatory feedback channel for all mutating actions.

### 5.3 Internal module interface [V]

Shared TypeScript types in `shared/schema.ts` (database-shaped) and `client/src/types/index.ts` (domain-shaped) define the vocabulary exchanged between client and server (profiles, interests, saved items with typed payload `itemData`, career goals, recommendation envelopes). Drizzle-Zod insert schemas exist for validation potential but are unused at runtime boundaries (see INT-3).

---

## 6. Data Requirements

Entities the system must represent (**[V]** for structure — declared identically in the Drizzle schema and mirrored in-memory):

| Entity | Required fields | Optional/defaulted fields | Constraints & lifecycle |
|---|---|---|---|
| `users` | `username` (unique in schema), `password` | – | Serial id; seed row created at startup |
| `profiles` | `userId`, `name` | headline, location, industry, currentJobTitle, currentCompany, summary, avatarUrl | `experience`, `education`, `skills`, `certifications` are JSON collections defaulted empty; `createdAt` timestamp; lookups by userId |
| `interests` | `userId` | `topics`, `skills` JSON arrays defaulted empty; `createdAt` | One per user (lookup by userId) |
| `savedItems` | `userId`, `itemType`, `itemId`, `itemData` (JSON) | – | Multi-row collection; optional filtering by type; deletion by id |
| `careerGoals` | `userId` | desiredRole, industry, location, salaryRange; `createdAt` | One per user (lookup by userId) |

- **DAT-1 [V]** Each user-owned datum must carry `createdAt` set automatically at insertion time.
- **DAT-2 [V]** Identifiers are monotonically increasing integers assigned at insertion.
- **DAT-3 [V — with material qualification]** Persistence target ambiguity: PostgreSQL tables are fully declared (`shared/schema.ts`) and `drizzle.config.ts` mandates `DATABASE_URL` for migration workflows, yet the runtime storage engine is an in-process Map-based store (`MemStorage`) with no database connection anywhere in server code; `@neondatabase/serverless` is installed but unimported. Consequently: structure requirements above are authoritative, durability requirements are **not** satisfied by the running system (data resets on restart). See Section 10.
- **DAT-4 [I]** Validation schemas (`insertProfileSchema`, etc.) indicate an intended requirement that insert payloads conform to entity shapes; enforcement is presently absent (INT-3), so treat validation as designed-but-dormant.
- **DAT-5 [V]** Recommendation payloads are considered volatile reference data — cacheable for short periods (5-minute staleness window client-side) and safe to discard, since regeneration is stateless.
- **DAT-6 [V]** User-authored selections (interests, goals, bookmarks, edited profile) must remain available for the lifetime of the server process without expiration or retention limits.
- **DAT-7 [U]** Dead alternative persistence path: `client/src/lib/storage.ts` implements localStorage-based storage under `networkpro-*` keys (profile, interests, saved items, career goals, dark mode) duplicating the server contract — no component imports it. Whether it represents a fallback requirement abandoned mid-development cannot be established from the repository.

---

## 7. Security Requirements (Evidenced)

The security posture that can actually be attributed to this repository is narrow. Listed here as observed constraints and explicit absences (not as claimed guarantees):

- **SEC-1 [V]** Upload protection: server-enforced 5 MB maximum and strict `application/pdf` MIME check constrain abuse of the sole file-input channel. Evidence: multer config.
- **SEC-2 [V]** JSON-body parsing bounded to well-formed request entities via express json/urlencoded middleware; oversized-request limits rely on framework defaults (no custom limits configured) [I for exactness].
- **SEC-3 [Absent — documented as fact]** No authentication, authorization, role separation, CSRF protection, rate limiting, or transport-layer configuration exists in code. All endpoints are publicly callable, and because identity is hard-coded, any caller effectively operates (and can overwrite or delete) the single demo user's data. Dependencies suggesting intended auth (`passport`, `passport-local`, `express-session`, `connect-pg-simple`) are installed but entirely unwired. Treating authentication as a satisfied requirement would contradict the evidence; it is instead an identified open area.
- **SEC-4 [V]** Sensitive-data handling: no secrets are consumed at runtime (README lists `DATABASE_URL` and `SESSION_SECRET` env variables, but neither is read by the server; `DATABASE_URL` is required only by the drizzle-kit migration tool). Uploaded files are held in memory transiently and discarded — nothing stores file bytes beyond the request lifecycle.
- **SEC-5 [U]** Unvalidated writes: profile-update, interest, goal, and saved-item payloads are merged verbatim, meaning arbitrary fields injected by a client would be retained. Whether sanitization was deemed unnecessary for the demo or deferred is unknowable from the repository.

---

## 8. Non-Functional Requirements

Conservatively reconstructed quality attributes supported by implementation evidence:

- **NFR-1 [V] Observability (basic):** all `/api/*` requests must emit console log lines with timing and truncated response snapshots — sufficient for interactive debugging in a single-node demo. No metrics/tracing/alerting infrastructure exists.
- **NFR-2 [V] Perceived responsiveness:** multi-step asynchronous flows must display immediate progress feedback (spinner panels, pulsing progress bars with copy such as This may take a few moments) instead of blocking silently. Applied uniformly to upload, suggestion-loading, and recommendation-fetching paths.
- **NFR-3 [V] Resilience against extraction/handler failure:** processing errors must degrade to informative responses/toasts and never crash the server. The global error handler converts thrown errors into JSON with status/message while surfacing the exception in logs (`index.ts:42-48`), and extraction specifically catches-and-falls-back (FR-8).
- **NFR-4 [V] Deterministic client caching policy:** user-owned data must be treated as stale only after explicit mutation (staleTime Infinity, refetchOnWindowFocus off, retries disabled), while recommendations gain a 5-minute freshness window. Evidence: `queryClient.ts` defaults; per-hook staleTime overrides. The pragmatic implication: the app assumes a single-user session whose truth changes only through its own actions.
- **NFR-5 [V] Maintainability mechanisms:** end-to-end TypeScript strict mode across client/server/shared (`tsconfig.json`), a single shared type/module system with path aliases (`@/`, `@shared/`), and a type-check script (`npm run check`) constitute the maintained-quality tooling. There are no linters/tests configured.
- **NFR-6 [I] Accessibility/atmosphere basics:** dark-mode support, keyboard-usable custom interest entry (Enter submits), sr-only labels on icon-only buttons, responsive layouts with breakpoint-aware grids and icon-collapsed tab labels on small screens. Sourced from consistent Tailwind patterns across components; depth of accessibility compliance is unverifiable.
- **NFR-7 [Explicitly unsupported]** No numerical performance targets (latency, throughput, availability) can be attributed to this repository. The 5 MB upload cap is the only quantified resource constraint.
- **NFR-8 [V] Portability/scale assumptions:** a single fixed port (5000) bound to `0.0.0.0` with reusePort and combined API+static serving implies a single-process deployment model without horizontal scaling provisions (`server/index.ts:59-69`).

---

## 9. Operational and Deployment Requirements

- **OPS-1 [V]** Runtime lifecycle commands: `npm run dev` (tsx-executed server with Vite middleware), `npm run build` (Vite client bundle to `dist/public` + esbuild server bundle, packages externalized), `npm start` (`NODE_ENV=production node dist/index.js`), `npm run db:push` (drizzle-kit migration push gated on `DATABASE_URL`), `npm run check` (type-check). Evidence: `package.json` scripts.
- **OPS-2 [V]** Environment-variable expectations per README: `DATABASE_URL` and `SESSION_SECRET`. Implementation reality: neither variable affects the running application today; only `db:push` fails without `DATABASE_URL` (`drizzle.config.ts` throws). Documentation and implementation diverge here (Section 10).
- **OPS-3 [V]** Serving modes: development couples Vite dev-server middleware (with runtime-error overlay plugin and Replit-specific plugins when `REPL_ID` is set) behind Express; production serves the compiled static bundle with SPA fallback. Source-of-truth decision logic in `server/index.ts:53-57` and `vite.config.ts`.
- **OPS-4 [I]** Replit heritage: mandatory port 5000 (commented as the only non-firewalled port), the `REPL_ID` conditional plugin, and the drizzle push flow indicate operation primarily within a Replit workspace; nothing else in the repo prescribes deployment topology.
- **OPS-5 [U]** External hosting claims: README carries a Vercel deploy badge/link and asserts a Vercel-deployed frontend. The repository contains no `vercel.json` or equivalent hosting manifest; how a deployment reconciles the README's both-has-backend/no-backend contradiction is not resolvable from repository contents.
- **OPS-6 [V]** Startup must not depend on external services: no database connections, outbound APIs, or background workers are initialized at boot; the only startup side effect is seeding the demo user in memory.
- **OPS-7 [Verified absence]** No health-check endpoint, scheduled jobs, worker processes, containerization, or CI pipeline exists in the repository.

---

## 10. Stated vs Implemented: Discrepancies and Open Areas

The following matrix contrasts the original brief and README claims with the delivered system. These discrepancies are part of the reconstructed requirements picture, not editorial notes for future work.

| # | Stated requirement (source) | Delivered behavior (evidence) | Assessment |
|---|---|---|---|
| D-1 | Extract real details from uploaded LinkedIn PDFs (brief §Overview, Core Features) | Extraction simulated; sample text used regardless of input (`extractTextFromPdf`) | Simulated capability; FR-7 documents the operating rule |
| D-2 | AI-powered suggestions/recommendations personalized to profile, interests, goals (brief §2, §3, §4) | Fixed catalogs returned unconditionally; suggestion handler merely gates on profile existence | Personalization unimplemented; volume guarantees honored |
| D-3 | Top 5 Recruiters to Connect With (brief §4) and Experts to Consult (brief §3) | Absent from API, shared types, and UI | Not implemented categories |
| D-4 | Persistent storage of preferences, recommendations, ignored suggestions (brief General UI, §Refreshing & Storing) | Server persistence is in-memory only (resets on restart); localStorage duplicate unused; schema declares Postgres | Partially satisfied within process lifetime only |
| D-5 | README tech stack: Node.js/Express backend with PostgreSQL+Drizzle | Express backend exists; PostgreSQL declared but disconnected; Neo4j-like Neon driver unused | README stack overstated relative to runtime |
| D-6 | README simultaneously claims backend presence and states Currently does not have any backend - vercel deployed frontend | Both cannot hold; runtime is an integrated Express+Serving process on port 5000 | Self-contradictory README; server-side evidence dominates |
| D-7 | Load More fetches the next five recommendations (brief §3) | Show More paginates over already-fetched static data; refresh regenerates identical content | Presentation-only interpretation |
| D-8 | Apply / Connect actions (brief §4) | Acknowledged via toasts; no external LinkedIn/job-board integration exists | Simulated outcomes |
| D-9 | Enforced wizard sequencing implied by four-step journey | Tabs freely navigable; order encouraged not required | Looser-than-brief navigation freedom |
| D-10 | Zod insert schemas defined (shared/schema.ts) imply validated writes | Handlers trust `req.body` wholesale | Dormant validation |
| D-11 | Interest suggestions influence subsequent tabs (brief §2) | No downstream consumer reads stored interests; recommendation endpoints ignore them | Chain unimplemented beyond storage |

Additional verified characteristics not attributable to stated intent: demo-skip upload bypass (FR-11), relaxed client file-type check (FR-6), seeded demo credentials (BR-8), API response logging (INT-4), unused dead modules (`pages/not-found.tsx`, router scaffolding never wired, localStorage helper module).

## 11. Unknowns

- The origin timeline and whether any phases were consciously de-scoped versus unfinished cannot be established from commit history within the provided analysis scope.
- Whether a real LLM/NLP pipeline was planned behind the simulated functions is plausible given copy such as Our AI is processing your LinkedIn data and code comments noting what a real implementation would use, but no configuration, prompt assets, or integration stubs exist — classified **[U]**.
- Intended authentication UX (the seed user suggests some form of accounts) leaves the target behavior undocumented — **[U]**.
- Exact deployment environment(s) in actual use (Replit, Vercel, self-hosted) beyond README claims — **[U]**.

**Summary:** the repository evidences a coherent, single-user demo system whose genuine requirements center on: constrained PDF ingestion with simulated extraction; editable structured profile capture; interests/goals declaration with constrained vocabularies; fixed five-item recommendation catalogs across networking and jobs domains; typed bookmarking with ignore/save affordances; progressive disclosure with refresh; theme persistence; informative feedback on every async action; and a simple observability baseline — all operating without authentication or durable storage, in deliberate demo trade-offs consistently acknowledged inside the code itself.