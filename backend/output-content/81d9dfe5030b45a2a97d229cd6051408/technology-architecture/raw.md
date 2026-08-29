# Technology Architecture

## 1. Architectural Summary

Next.js Commerce is a headless ecommerce storefront implemented as **a single Next.js application**. The repository contains exactly one deployable unit: an App Router–based React 19 / TypeScript web application that renders the storefront and brokers all commerce data between the shopper's browser and an external Shopify store. There is no independently deployed backend service, background worker, message queue, or application-owned database in this repository.

Durable state is deliberately externalized. Products, collections, content pages, navigation menus, and shopping carts are owned by Shopify and accessed through the **Shopify Storefront GraphQL API** (`POST https://<store-domain>/api/2023-01/graphql.json`, authenticated with a Storefront access token header). The application's own architectural responsibilities are:

- Server rendering and partial prerendering of the storefront (App Router, React Server Components, experimental PPR)
- Cart orchestration on top of Shopify cart primitives via React Server Actions
- Tag-based caching of Shopify responses in the Next.js Data Cache
- Webhook-driven cache invalidation when catalog data changes in Shopify
- SEO surface generation (metadata, sitemap.xml, robots.txt, Open Graph images)
- Optimization and proxying of Shopify CDN imagery

Facts that anchor this architecture, each verifiable in source:

- The repository contains **exactly one outbound HTTP call site**: `shopifyFetch()` in `lib/shopify/index.ts`. Every piece of commerce data flows through it.
- `package.json` declares no database driver, ORM, migration tool, queue client, or authentication framework.
- Exactly one HTTP API endpoint exists: `POST /api/revalidate` (`app/api/revalidate/route.ts`).
- Exactly one `'use server'` module exists: `components/cart/actions.ts`.
- The app pins `next@15.6.0-canary.60` because it depends on experimental rendering and caching features enabled in `next.config.ts`: `ppr`, `inlineCss`, and `useCache`. Cache primitives `unstable_cacheLife` / `unstable_cacheTag` are imported from `next/cache` in `lib/shopify/index.ts`.

## 2. Architecture Diagram

```mermaid
flowchart LR
    subgraph BROWSER['Shopper Browser']
        CC['Client runtime - React 19 hydration<br/>cart modal · variant selector · search · mobile menu<br/>optimistic cart state via useOptimistic']
        CK[('cartId cookie')]
    end

    subgraph APP['Next.js 15 Application - TypeScript · Node.js runtime']
        direction TB
        PAGES['Rendering layer - App Router RSC + Partial Prerendering<br/>routes: / · /search · /search/[collection] · /product/[handle] · /[page]']
        SEO['SEO surface<br/>generateMetadata · sitemap.xml · robots.txt · opengraph-image via next/og']
        SA['Interaction layer - Server Actions (use server)<br/>addItem · removeItem · updateItemQuantity<br/>createCartAndSetCookie · redirectToCheckout']
        WH['Webhook entrypoint<br/>POST /api/revalidate route handler']
        CACHE['Next.js Data Cache<br/>use cache directives · tags: products / collections / cart']
        DAL['Commerce data-access layer - lib/shopify<br/>shopifyFetch() · GraphQL queries/mutations · response reshaping']
        IMG['Image optimization<br/>next/image · AVIF/WebP']
    end

    SFGQL['Shopify Storefront GraphQL API<br/>POST STORE-DOMAIN/api/2023-01/graphql.json']
    SFDATA[('Shopify store - system of record<br/>products · collections · pages · menus · carts')]
    CHECKOUT['Shopify-hosted checkout<br/>cart.checkoutUrl']
    CDN['Shopify CDN<br/>cdn.shopify.com/s/files']

    CC -->|'navigation · RSC payloads · Server Action POSTs'| PAGES
    CC -->|'GET optimized images'| IMG
    CK -.->|'cartId travels with cart requests'| SA
    PAGES -->|'data reads during render'| DAL
    SEO -->|'sitemap + metadata reads'| DAL
    SA -->|'cart reads and mutations'| DAL
    DAL -->|'declares cache tags/lifetimes'| CACHE
    DAL -->|'HTTPS POST · X-Shopify-Storefront-Access-Token'| SFGQL
    SFGQL ---|'fronts'| SFDATA
    SFDATA -.->|'webhooks products/* collections/*<br/>header x-shopify-topic'| WH
    WH -->|'secret check · revalidateTag'| CACHE
    SA -->|'updateTag cart'| CACHE
    SA -->|'redirect cart.checkoutUrl'| CHECKOUT
    IMG -->|'origin fetch'| CDN
```

### Edge-by-edge evidence

| Relationship | Basis | Certainty |
|---|---|---|
| Browser → Rendering layer | App Router pages/layouts in `app/`; async server components with `Suspense` boundaries | Verified |
| Browser → Server Actions | `components/cart/actions.ts` (`'use server'`) invoked from client forms via `useActionState`, `form action`, `useFormStatus` in `add-to-cart.tsx`, `modal.tsx`, quantity/delete buttons | Verified |
| Rendering/SEO → `lib/shopify` | Direct imports in every page, layout, `sitemap.ts`, and `opengraph-image.tsx` route (e.g., `app/product/[handle]/page.tsx`, `app/[page]/page.tsx`) | Verified |
| `lib/shopify` → Shopify GraphQL | Single `fetch()` POST at `lib/shopify/index.ts`; endpoint assembled from `SHOPIFY_STORE_DOMAIN` + `SHOPIFY_GRAPHQL_API_ENDPOINT` (`lib/constants.ts`, API version `2023-01`); token header `X-Shopify-Storefront-Access-Token` | Verified |
| `lib/shopify` ↔ Data Cache | `'use cache'` / `'use cache: private'` directives with `cacheTag`/`cacheLife` inside the data functions; `revalidateTag` in `revalidate()`; `updateTag` in cart actions | Verified |
| Shopify → `/api/revalidate` | Handler reads `x-shopify-topic` header and validates `secret` query parameter against `SHOPIFY_REVALIDATION_SECRET`; topic list covers `products/*` and `collections/*` events. That production Shopify stores are configured to send these webhooks cannot be proven from the repository alone | Endpoint verified; production wiring unverified |
| Server Action → Shopify checkout | `redirectToCheckout()` executes `redirect(cart.checkoutUrl)`; `checkoutUrl` originates from the Shopify cart object | Verified redirect; Shopify-hosted nature strongly inferred |
| Image optimizer → Shopify CDN | `next.config.ts` `images.remotePatterns` allows `cdn.shopify.com/s/files/**`; formats AVIF/WebP | Verified |

## 3. Runtime Components

| Component | Responsibility | Technology | Location | Certainty |
|---|---|---|---|---|
| Shopper browser runtime | Interactive cart drawer, variant picker, search input, mobile menu, toasts; optimistic cart updates before server confirmation | React 19 client components, `@headlessui/react` Dialog/Transition, `@heroicons/react`, `sonner`, `clsx` | `components/cart/*`, `components/layout/navbar/*`, `welcome-toast.tsx` | Verified |
| Presentation / rendering layer | Server-renders all storefront routes; streams with Suspense; generates per-route metadata and OG images | Next.js App Router (RSC, experimental PPR, `inlineCss`) | `app/layout.tsx`, `app/page.tsx`, `app/search/*`, `app/product/[handle]/*`, `app/[page]/*` | Verified |
| Interaction layer (mutations) | Add/remove/update cart lines, create cart, redirect to checkout | React Server Actions | `components/cart/actions.ts` | Verified |
| Interaction layer (inbound webhook) | Validates Shopify webhook calls and invalidates cache tags | Next.js Route Handler | `app/api/revalidate/route.ts` → `revalidate()` in `lib/shopify/index.ts` | Verified |
| Commerce data-access layer | Sole gateway to Shopify; owns GraphQL documents, token handling, error normalization, and reshaping of Shopify responses into template types | Native `fetch`, GraphQL documents in `queries/`, `mutations/`, `fragments/` | `lib/shopify/*` | Verified |
| Caching layer | Caches Shopify responses by tag with lifetime policies; invalidated by webhook and cart actions | Next.js Data Cache (`use cache`, `cacheTag`, `cacheLife`, `revalidateTag`, `updateTag`) | `lib/shopify/index.ts`, `lib/constants.ts` (`TAGS`) | Verified (backing store is platform-managed) |
| Image optimization | Optimizes and serves remote Shopify media | `next/image` + Next image optimizer | `next.config.ts`, `GridTileImage`, `modal.tsx` usage | Verified |
| SEO surface generators | robots.txt, dynamic sitemap.xml, static/OG image rendering | Next metadata routes, `next/og` `ImageResponse` with vendored `fonts/Inter-Bold.ttf` read via `fs/promises` | `app/robots.ts`, `app/sitemap.ts`, `app/opengraph-image.tsx` and per-route equivalents, `components/opengraph-image.tsx` | Verified |
| External: Shopify Storefront API + store | System of record for catalog, CMS pages, menus, carts | Shopify Storefront GraphQL API (version `2023-01`) | External service | Verified as integration target; store internals external |
| External: Shopify-hosted checkout | Payment and order completion occur outside this app | `checkoutUrl` redirect | External service | Strongly inferred |
| External: Shopify CDN | Origin for product and lifestyle imagery | `cdn.shopify.com` | External service | Verified (image config) |

Notes on component boundaries:

- All runtime callers of `lib/shopify` are server-side modules (server components, server actions, route handlers, metadata/sitemap generators). Client components import only type definitions from `lib/shopify/types`, which are erased at build time. The Storefront access token therefore never enters the browser bundle through this import graph.
- `lib/shopify` is also the documented provider seam: the README instructs alternative commerce providers to fork the template and swap `lib/shopify` while leaving the rest unchanged. The codebase is consistent with that claim — every consumer reaches commerce data exclusively through this module, and its public functions return provider-neutral shapes defined in `lib/shopify/types.ts`.

## 4. Technology Stack and Evidence

Only technologies that materially affect architecture are listed.

| Technology | Version / Form | Architectural role | Evidence | Status |
|---|---|---|---|---|
| Next.js (canary) | `15.6.0-canary.60` | Application framework, routing, SSR/RSC, Server Actions, caching, image optimization, OG image rendering | `package.json`; `next.config.ts` experimental flags `ppr`, `inlineCss`, `useCache`; `unstable_cache*` imports | Verified |
| React / React DOM | `19.0.0` | UI runtime; `useOptimistic`, `useActionState`, Suspense, async server components | `package.json`; `components/cart/cart-context.tsx`; pages throughout `app/` | Verified |
| TypeScript | `5.8.2`, `strict` + `noUncheckedIndexedAccess` | Language for the entire codebase; provider-neutral domain types | `tsconfig.json`, `lib/shopify/types.ts` | Verified |
| Tailwind CSS v4 | Via `@tailwindcss/postcss`; plugins container-queries and typography loaded in `globals.css` | Styling pipeline (build-time PostCSS step) | `postcss.config.mjs`, `globals.css`, devDependencies | Verified |
| pnpm | Lockfile + scripts | Package manager and task runner (`pnpm dev` with Turbopack, `pnpm build`, `pnpm start`) | `pnpm-lock.yaml`, `package.json` scripts, `.vscode/launch.json` | Verified |
| Shopify Storefront GraphQL API | `2023-01` | External commerce backend | `lib/constants.ts`, `lib/shopify/index.ts`, `.env.example` | Verified |
| Geist font package + vendored Inter | `geist@^1.3.1`; `fonts/Inter-Bold.ttf` | Typography; Inter binary is loaded at request time by the OG image generator | `app/layout.tsx`, `components/opengraph-image.tsx` | Verified |
| Headless UI, Heroicons, Sonner, clsx | Latest minors per lockfile range | Cart dialog, icons, toast notifications, class merging | Imports in cart modal, navbar, layout | Verified |
| Prettier (+ Tailwind class-sort plugin) | `3.5.3` | Formatting; also the only automated verification (`test` script runs `prettier:check`) | `package.json` scripts | Verified |

Explicitly absent from the architecture (verified absence): databases, ORMs, Redis/cache servers, message queues, authentication providers, analytics SDKs, i18n frameworks, and any second application or service.

## 5. Communication and Data Flows

**F1 — Homepage rendering.** Browser requests `/` → root layout starts `getCart()` without awaiting and passes the promise to `CartProvider` (`app/layout.tsx`) → `ThreeItemGrid` and `Carousel` (async server components) call `getCollectionProducts` for the reserved collections `hidden-homepage-featured-items` and `hidden-homepage-carousel` → `lib/shopify` serves from the Data Cache or fetches Shopify → streamed HTML/RSC payload.

**F2 — Search and collection browsing.** `/search?q=<term>&sort=<slug>` and `/search/[collection]` map sort slugs to Shopify `sortKey`/`reverse` pairs (`lib/constants.ts`) → `getProducts` / `getCollectionProducts` → product grid. The client wrapper `children-wrapper.tsx` re-keys children on the `q` search param so results re-render per query.

**F3 — Add to cart (optimistic).** Submitting the AddToCart form fires two paths concurrently: (a) an immediate optimistic `ADD_ITEM` transition through `useOptimistic` in the cart context, and (b) the `addItem` Server Action, which reads the `cartId` cookie, runs the `cartLinesAdd` mutation against Shopify, then calls `updateTag(TAGS.cart)` so cached cart reads refresh. The server result subsequently reconciles the optimistic state.

**F4 — Cart bootstrap.** When the cart modal detects no cart, its effect invokes `createCartAndSetCookie()`, which runs `cartCreate` against Shopify and sets the `cartId` cookie via `cookies().set()` in the Server Action. The cookie is the only client-side key tying the browser to a Shopify cart.

**F5 — Quantity changes and removal.** Quantity buttons and delete buttons apply optimistic `UPDATE_ITEM` transitions locally while `updateItemQuantity` / `removeItem` Server Actions resolve line IDs from `getCart()` and issue `cartLinesUpdate` / `cartLinesRemove` mutations.

**F6 — Checkout handoff.** The Proceed-to-Checkout form invokes `redirectToCheckout`, which loads the cart and performs `redirect(cart.checkoutUrl)`. The browser leaves the storefront entirely; no order, payment, or customer-account logic exists in this repository. The code comment that old carts become `null` after checkout corroborates that checkout completes in Shopify.

**F7 — Webhook-driven revalidation.** Shopify catalog events arrive at `POST /api/revalidate` with an `x-shopify-topic` header and a `secret` query parameter. `revalidate()` compares the secret to `SHOPIFY_REVALIDATION_SECRET`, maps collection topics to `revalidateTag(TAGS.collections)` and product topics to `revalidateTag(TAGS.products)`, and responds HTTP 200 in all cases (an unauthorized call receives a `401` value in the response body rather than an HTTP error status, matching the inline comment that non-200 responses cause Shopify to retry).

**F8 — Image pipeline.** `<Image>` elements reference `cdn.shopify.com` URLs; the Next image optimizer (enabled by the `remotePatterns` entry) fetches the origin once and serves AVIF/WebP derivatives sized per the `sizes` hints used across grids and galleries.

**F9 — SEO endpoints.** Crawlers receive `robots.txt` (static definition referencing the sitemap), `sitemap.xml` (`force-dynamic`; validates required environment variables, then fetches collections, products, and pages in parallel), and per-route Open Graph images rendered server-side by `next/og` using the vendored Inter font. Product pages additionally emit schema.org Product JSON-LD built from Shopify fields (`app/product/[handle]/page.tsx`).

## 6. State, Caching, and Persistence

Where state lives:

| Kind of state | Location | Mechanism | Certainty |
|---|---|---|---|
| Durable commerce state (catalog, pages, menus, carts) | Shopify store | Storefront GraphQL reads/writes | Verified as integration; store internals external |
| Cart identity | Browser cookie `cartId` | Set by `createCartAndSetCookie` Server Action; read via `cookies()` in `lib/shopify` | Verified |
| Render/data cache | Next.js Data Cache (platform-managed) | `'use cache'` directives with tags and lifetimes | Verified directives; backing store not visible in repo |
| In-flight cart view | Client memory | `useOptimistic` reducer in `cart-context.tsx`, seeded from the server-passed cart promise | Verified |
| Application-owned durable storage | None | No database/ORM/file-write code exists | Verified absence |

Cache policy declared in `lib/shopify/index.ts`:

| Function(s) | Directive | Tag(s) | Lifetime |
|---|---|---|---|
| `getCart` | `'use cache: private'` (cookie-scoped) | `cart` | `seconds` |
| `getProduct`, `getProducts`, `getProductRecommendations` | `'use cache'` | `products` | `days` |
| `getCollections`, `getCollection`, `getCollectionProducts`, `getMenu` | `'use cache'` | `collections` (plus `products` for collection-product queries) | `days` |
| `getPage`, `getPages` | none — executed uncached | — | — |

Invalidation paths: Shopify product/collection webhooks invalidate `products` / `collections` tags via the route handler; cart mutations invalidate the `cart` tag via `updateTag` in the Server Actions.

The `cartId` cookie is unauthenticated: possession of the identifier is the only requirement to read or mutate that cart through the storefront. This is the observed design, recorded here without evaluation.

## 7. Configuration Boundaries

Environment contract from `.env.example` plus one additional variable referenced in code:

| Variable | Consumed by | Effect |
|---|---|---|
| `SHOPIFY_STORE_DOMAIN` | `lib/shopify/index.ts` | Builds the GraphQL endpoint (`https://<domain>/api/2023-01/graphql.json`). Unset → degraded mode (below) |
| `SHOPIFY_STOREFRONT_ACCESS_TOKEN` | `lib/shopify/index.ts` | Storefront API credential sent as `X-Shopify-Storefront-Access-Token` |
| `SHOPIFY_REVALIDATION_SECRET` | `revalidate()` in `lib/shopify/index.ts` | Shared secret authorizing webhook-driven cache invalidation |
| `SITE_NAME` | `app/layout.tsx` metadata, navbar, footer, OG images | Brand name |
| `COMPANY_NAME` | `components/layout/footer.tsx` | Copyright attribution (falls back to `SITE_NAME`) |
| `VERCEL_PROJECT_PRODUCTION_URL` | `lib/utils.ts` `baseUrl` | Canonical URL base for metadata, sitemap, robots; falls back to `http://localhost:3000` |

Validation behavior: `validateEnvironmentVariables()` (`lib/utils.ts`) raises an error listing missing `SHOPIFY_STORE_DOMAIN` / `SHOPIFY_STOREFRONT_ACCESS_TOKEN` values and rejects bracketed placeholder domains; it is invoked by the sitemap generator. Individual data functions additionally short-circuit when the endpoint is unconfigured.

Configuration that changes the architecture itself: the `experimental` block in `next.config.ts` (`ppr`, `inlineCss`, `useCache`) enables the partial-prerendering and granular cache-directive model the code is written against; removing it would disable the `'use cache'` code paths. The pinned canary release exists to support these features.

## 8. Security and Trust Boundaries

- **Browser ↔ Next.js server.** Public, unauthenticated storefront. There are no user accounts, sessions, or login flows anywhere in the repository; the only identity artifact is the `cartId` cookie.
- **Next.js server ↔ Shopify.** The Storefront token is a server-side secret. Import analysis confirms all runtime imports of `lib/shopify` originate from server modules; client bundles receive only erased type definitions.
- **Shopify ↔ `/api/revalidate`.** Authorization is a shared-secret comparison (`secret` query parameter vs `SHOPIFY_REVALIDATION_SECRET`) plus an explicit topic allow-list (`products/create|update|delete`, `collections/create|update|delete`). Unrecognized topics return success without invalidation.
- **Payment and customer data.** Checkout, payment capture, and customer records remain in Shopify; the storefront handles no payment instruments. Product/customer PII exposure is limited to what cart operations require.

## 9. Build, Runtime, and Deployment Boundaries

- **Process model:** one Node.js process group running the compiled Next.js server (`pnpm build` → `pnpm start`); development uses `next dev --turbopack`. Debug configurations for client, server, and full-stack debugging live in `.vscode/launch.json`.
- **Rendering boundary:** server components, Server Actions, route handlers, and metadata generators execute on the server; `'use client'` modules execute in the browser. The split is explicit per file.
- **Deployment evidence:** the README ships a one-click Vercel deploy button, instructs `vercel link` / `vercel env pull` for local development, recommends Vercel Environment Variables, and the code consumes `VERCEL_PROJECT_PRODUCTION_URL`. The footer links to the Vercel template gallery. No Dockerfile, compose file, Kubernetes manifests, Terraform, or `vercel.json` exists in the repository, and there is no CI/CD configuration.
- **Classification:** Vercel is the *intended* deployment target — strongly inferred from multiple consistent artifacts. Nothing in the code binds the app to Vercel; it remains a portable Node server application, and any Node host could run `next build && next start`. No specific production topology (regions, CDN edges, cache backing services) can be established from the repository.

## 10. Documented Architecture vs Implemented Architecture

| README claim | Implementation finding |
|---|---|
| High-performance server-rendered App Router commerce app using RSC, Server Actions, Suspense, `useOptimistic` | All four confirmed in code (async server components, `'use server'` module, Suspense wrappers, optimistic cart reducer) |
| Alternative providers can swap `lib/shopify` and keep the rest of the template | Consistent with the implementation: `lib/shopify` is the sole commerce gateway with provider-neutral output types; all consumers depend only on it |
| Shopify is the actively maintained provider; BigCommerce, Ecwid, Medusa, Saleor, Wix, etc. offer forks; Orama and React Bricks offer integrations | These are external repositories. None of that code exists here; no multi-provider abstraction layer is implemented beyond the single-module seam |
| Demo at `demo.vercel.store`; Vercel/Shopify integration guide | External references only; they do not constitute in-repo infrastructure |

No material contradictions were found between the README and the implementation.

## 11. Behavior Without Shopify Configuration

The data layer degrades gracefully when `SHOPIFY_STORE_DOMAIN` is absent: `getMenu` returns an empty array, `getCollections` synthesizes a single 'All' collection, `getCollectionProducts` returns an empty list, and `getProduct` returns `undefined` (producing `notFound()` responses), each logging a skip message instead of calling Shopify. The storefront therefore renders an empty-but-functional shell without credentials. Cart operations and the revalidation secret path have no equivalent degradation and would fail if invoked in this state.

## 12. Evidence Classification Summary

**Verified (directly evidenced):** single-application topology; the lone `fetch` gateway and its endpoint/auth construction; the complete route and Server Action inventory; cache directives, tags, and lifetimes; cookie-based cart identity; webhook handler logic including the always-200 response policy; image remote-pattern configuration; environment variable contract and validation; degraded no-credentials mode; pnpm/Turbopack/Tailwind v4/TypeScript toolchain; canary Next pinning tied to experimental features.

**Strongly inferred (multiple consistent artifacts, no single proof):** Vercel as the intended production platform; Shopify as the persistent system of record whose carts survive across sessions and whose checkout completes off-storefront; Shopify as the sender of the webhooks the revalidation endpoint is designed to accept.

**Unverified / apparently absent:** production webhook configuration; CI/CD pipelines; any containerized or self-hosted deployment topology; any second runtime unit; the Orama/React Bricks/provider integrations described in the README (external projects, not present in this codebase).

## 13. Unknowns and Limits of the Evidence

- Whether real deployments wire Shopify webhooks to `/api/revalidate` cannot be established from the repository; the receiving endpoint, topic mapping, and secret variable are present and internally consistent.
- The Data Cache backing store (memory, Redis, platform-managed) is abstracted by Next.js and is not visible in this codebase.
- Operational characteristics such as traffic handling, scaling, and cache hit rates are deployment properties with no in-repo evidence.
- The Shopify Storefront API version is pinned to `2023-01` in `lib/constants.ts`; consequences of that pin over time are outside the scope of this phase.