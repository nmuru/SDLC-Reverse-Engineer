# Future Directions

**Repository:** `vercel/commerce` (Next.js Commerce — Shopify headless storefront)

---

## 1. Executive Synthesis

Next.js Commerce is a mature, narrowly scoped reference storefront: a single Next.js App Router application backed exclusively by the Shopify Storefront API, optimized for performance demonstration on Vercel and designed to be forked by alternative commerce providers. Its current implementation is complete for its stated scope — catalog browsing, search, product detail, cart management, Shopify-hosted checkout redirection, CMS pages, SEO surfaces, and webhook-driven cache revalidation.

The evidence in the repository points to four clusters of credible future work:

1. **Platform stabilization risk.** The entire rendering and caching model rests on a pinned Next.js canary release (`next@15.6.0-canary.60`) and experimental/unstable APIs (`ppr`, `inlineCss`, `useCache` flags; `unstable_cacheLife`, `unstable_cacheTag`, `updateTag`; eight `"use cache"` directives). This is deliberate early-adopter positioning, but it concentrates upgrade and breakage risk in the template that other providers fork.
2. **Verification vacuum.** The only automated check in the repository is Prettier formatting (`"test": "pnpm prettier:check"`). There are no unit, integration, or end-to-end tests and no CI workflow files. Every revenue-relevant flow — cart mutations, variant resolution, revalidation authorization — currently ships without regression protection.
3. **Silent scale ceilings.** All catalog queries fetch `first: 100` records with no cursor pagination, and hidden-product filtering happens after fetching. Catalogs larger than 100 products or collections are silently truncated in search results, collection grids, and even the sitemap.
4. **Security and consistency refinements.** Revalidation authenticates via a URL query-string secret compared with `!==` rather than Shopify HMAC verification; the cart cookie is set without security attributes; cart actions collapse all failures into one generic message; and CMS pages/menus have no revalidation path while products and collections do.

None of these findings invalidate the current design. They define the realistic next steps: make change safe (testing, stabilization), remove silent correctness ceilings (pagination, cart robustness, freshness parity), then invest in structural leverage (provider contract, observability) before considering scope expansion.

---

## 2. Current-State Baseline

The following baseline synthesizes the established findings of the preceding phases and grounds every recommendation below.

| Aspect | Established current state |
|---|---|
| **Purpose** | High-performance, server-rendered Next.js App Router ecommerce storefront demonstrating React Server Components, Server Actions, `Suspense`, and `useOptimistic` against Shopify (`README.md`). |
| **Provider strategy** | Only the Shopify integration is actively maintained; alternative providers fork the repository and replace `lib/shopify` (`README.md`, "Providers"). |
| **Data layer** | Single module `lib/shopify/` wrapping the Shopify Storefront GraphQL API (`2023-01`), with hand-written queries/mutations/fragments and reshape helpers mapping Shopify types to view types. |
| **Rendering & caching** | Experimental PPR (`next.config.ts`: `ppr`, `inlineCss`, `useCache`) with `"use cache"` + `cacheTag`/`cacheLife` profiles (`seconds` for cart, `days` for catalog) and tag-based invalidation via `/api/revalidate`. |
| **Features** | Home grid/carousel, search with sort filters and collection sidebar, product detail (variants, ≤5 gallery images, recommendations, JSON-LD), cart modal with optimistic updates, checkout redirect to Shopify, CMS `[page]` routes, sitemap/robots/OpenGraph images. |
| **Testing** | Formatting check only. No test files, no test runner, no `.github/` workflows, no lint configuration. |
| **Known constraints** | Canary framework pin; hardcoded `first: 100` limits; post-fetch hidden-product filtering; menu URL mapping via string replacement; generic string-error contract in cart actions; `console.*` logging only. |

---

## 3. Explicit Forward-Looking Signals in the Repository

The repository contains **no TODOs, FIXMEs, roadmap files, or changelogs** (a full-tree search returned no matches). Forward-looking intent is expressed structurally:

- **README v1 note:** v1 is archived; the current tree is the App Router rewrite. The major migration the project signaled has already landed; no successor migration is announced.
- **README integrations section:** Orama (upgraded search with typeahead/vector similarity) and React Bricks (visual editing of pages/product/footer content) are documented as out-of-tree enhancement paths — an explicit statement that search richness and visual CMS editing are recognized extension points rather than in-template goals.
- **README provider note:** Vercel partners with providers to bring up parallel templates; the fork-and-swap model is the declared extensibility mechanism.
- **`next.config.ts` experimental flags:** the project intentionally lives at the leading edge of the Next.js platform, which implies an obligation to track those APIs toward stability.

These signals are treated as evidence of intent, not commitments.

---

## 4. Prioritized Future Directions

### 4.1 High Priority

#### FD-1 — Establish an automated verification harness for core flows

- **Current evidence:** `package.json` defines `"test": "pnpm prettier:check"`; a repository-wide search finds no `*.test.*`/`*.spec.*` files, no Vitest/Jest/Playwright configuration, and no `.github/` workflow definitions. Pure logic that is highly testable already exists: the cart reducer and cost math (`components/cart/cart-context.tsx`), environment validation (`lib/utils.ts`), error detection (`lib/type-guards.ts`), and the Shopify reshape layer (`lib/shopify/index.ts`).
- **Limitation:** Cart mutations, variant selection, revalidation authorization, and cache-tag wiring have zero regression protection. Any refactor of `lib/shopify` or the cart reducer is unverifiable except by manual clicking. Provider forks inherit the same vacuum — nothing verifies that a swapped data layer still satisfies the template's expectations.
- **Proposed direction:** Build verification outward from what already exists: (a) unit tests for pure logic (cart cost/reducer math, reshape helpers, `validateEnvironmentVariables`); (b) integration tests for Server Actions (`addItem`, `updateItemQuantity`, `removeItem`) against a stubbed `shopifyFetch`, covering the missing-`cartId` and stale-cart paths; (c) a small end-to-end smoke suite covering browse → add-to-cart → quantity edit → checkout redirect, plus the revalidation webhook's authorized/unauthorized branches. Run the suite (together with the existing `prettier:check`) in CI.
- **Expected benefit:** Makes every subsequent direction in this document safely executable; converts the implicit provider contract into a verifiable conformance suite reusable by forked providers.
- **Prerequisites:** Selection of a test runner is a free engineering decision; the E2E tier requires a seeded Shopify demo store or recorded HTTP fixtures, both consistent with existing practice (the public demo store already serves this role).
- **Priority:** High — addresses the largest gap between business purpose (a trustworthy reference template) and current verification ability.
- **Confidence:** Evidence-backed (the gap is directly observable; the identified behaviors are the ones with the strongest correctness stakes).

#### FD-2 — Track Next.js stabilization and contain unstable-API surface

- **Current evidence:** `package.json` pins `next@15.6.0-canary.60`. `next.config.ts` enables `experimental.ppr`, `experimental.inlineCss`, and `experimental.useCache`. `lib/shopify/index.ts` imports `unstable_cacheLife`/`unstable_cacheTag` and uses eight `"use cache"` directives (including the private-profile form `"use cache: private"` for `getCart`); `components/cart/actions.ts` imports `updateTag`.
- **Limitation:** The template's defining features depend on APIs explicitly named `unstable_*`/`experimental`, on a canary compiler, and on cache-semantics profiles (`"days"`, `"seconds"`) that may be renamed or respecified before stabilization. For a template consumed by thousands of forks, each upstream rename becomes a fleet-wide breaking event, and the canary pin blocks casual dependency refreshes.
- **Proposed direction:** Define an explicit upgrade policy: monitor Next.js release channels for stabilization of PPR, `use cache`, and the cache-tag/profile APIs; confine unstable imports to the few modules that already centralize them (`lib/shopify/index.ts`, `components/cart/actions.ts`, `next.config.ts`) so future renames remain localized; migrate off the canary pin once the enabled feature set is available in a stable release, keeping a documented mapping between experimental flags and their stable successors.
- **Expected benefit:** Reduces upgrade friction for the template and every downstream fork; preserves the project's early-adopter value proposition while bounding its blast radius.
- **Prerequisites:** Upstream availability of stable equivalents (outside this repository's control); FD-1's regression suite to make the migration verifiable.
- **Priority:** High — the constraint touches every file in the app and is the dominant maintenance risk evidenced in the tree.
- **Confidence:** Evidence-backed (facts are direct; the containment policy is the natural response).

#### FD-3 — Cursor pagination and honest large-catalog behavior

- **Current evidence:** `getProductsQuery` and `getCollectionProductsQuery` request `products(first: 100)` / `collection.products(first: 100)` with no `pageInfo` or cursor fields (`lib/shopify/queries/product.ts`, `lib/shopify/queries/collection.ts`); `getCollectionsQuery` similarly caps at `first: 100`. The search page renders the full array with no pagination controls (`app/search/page.tsx`). Hidden products are filtered *after* fetching in `reshapeProduct` (tag `nextjs-frontend-hidden`), so effective result counts can fall further below 100. The sitemap reuses the same capped queries (`app/sitemap.ts`).
- **Limitation:** Stores with more than 100 products silently lose visibility for everything past the cap — in search, in collections, and in the generated sitemap (an SEO defect, not merely a UX one). Post-fetch filtering makes the truncation nondeterministic from the operator's point of view.
- **Proposed direction:** Extend queries with `pageInfo { hasNextPage endCursor }` and thread cursor parameters through `getProducts`/`getCollectionProducts`; add pagination controls (or incremental loading) to the search/collection grids; filter hidden products in the GraphQL query where the Storefront API supports it, or compensate in page sizing; paginate `sitemap.ts` output.
- **Expected benefit:** Removes a silent correctness ceiling on the template's core browsing loop and keeps the SEO surface complete for real stores.
- **Prerequisites:** None beyond FD-1 for safe verification; UI work should preserve the current PPR/streaming behavior of the search route.
- **Priority:** High — directly contradicts the template's fitness for real stores, which its own README promotes.
- **Confidence:** Evidence-backed.

### 4.2 Medium Priority

#### FD-4 — Harden webhook authentication (HMAC over shared-secret-in-URL)

- **Current evidence:** `revalidate()` in `lib/shopify/index.ts` reads `secret` from the request query string and compares it with `!==` against `SHOPIFY_REVALIDATION_SECRET`; the handler deliberately always answers HTTP 200 with the status encoded in the body (documented in-code as preventing Shopify retry storms). Handled topics are limited to `collections/*` and `products/*`.
- **Limitation:** Secrets embedded in URLs leak through proxy/access logs and are visible to any intermediary; plain string comparison is not constant-time. Shopify natively signs webhooks (`X-Shopify-Hmac-Sha256` over the raw body), which the implementation does not use.
- **Proposed direction:** Verify the HMAC signature of each webhook against the configured signing secret using a timing-safe comparison, retaining the always-200 response semantics; treat the query-string secret as a legacy fallback during migration.
- **Expected benefit:** Aligns trust in the one unauthenticated-write endpoint of the application with the platform's intended mechanism; eliminates secret leakage via URLs.
- **Prerequisites:** Store configuration change (webhook signing secret); FD-1 tests covering the authorized/unauthorized/forged-signature branches.
- **Priority:** Medium — the endpoint can only trigger cache invalidation (low blast radius), but it is the sole trust boundary the application owns.
- **Confidence:** Facts evidence-backed; the direction is strongly justified.

#### FD-5 — Cart flow robustness and typed error surfacing

- **Current evidence:** Cart operations read `(await cookies()).get("cartId")?.value!` with non-null assertions (`addToCart`, `removeFromCart`, `updateCart`); `createCartAndSetCookie` writes the `cartId` cookie with no `httpOnly`/`secure`/`sameSite`/expiry attributes; `redirectToCheckout` executes `redirect(cart!.checkoutUrl)`, throwing if the cart is gone; all Server Action failures collapse to the literal strings `"Error adding item to cart"` / `"Error updating item quantity"`; the optimistic client computes money as floating-point `Number(price) * quantity` and falls back to `currencyCode: "USD"` (`cart-context.tsx`).
- **Limitation:** An expired or missing `cartId` (carts become `null` after checkout, per the in-code comment) produces opaque generic errors instead of transparent cart recreation; the race between first-page render and first add-to-cart is unhandled; error messages are not distinguishable (sold out vs. network vs. invalid variant), limiting both UX and diagnosability.
- **Proposed direction:** Make cart-id absence/staleness a first-class state — detect it in the data layer and recreate the cart atomically before mutation; set explicit secure cookie attributes; replace string errors with a typed result union so the UI can surface actionable messages via the existing Sonner toaster; move money arithmetic to integer-minor-unit or decimal-string computation shared by client and server.
- **Expected benefit:** Removes the most likely real-user failure paths in the purchase funnel and improves diagnosability of Shopify-side rejections.
- **Prerequisites:** FD-1 (action-level tests make the refactor safe).
- **Priority:** Medium — core-flow reliability, moderate severity, low architectural risk.
- **Confidence:** Facts evidence-backed; direction strongly justified.

#### FD-6 — Content-freshness parity for pages and menus

- **Current evidence:** `revalidate()` handles only product and collection topics; `getPage`/`getPages` carry no `"use cache"` directives while `getMenu` is cached with `cacheLife("days")` tagged `TAGS.collections` (`lib/shopify/index.ts`). No webhook path invalidates page or menu content.
- **Limitation:** Product and collection edits propagate near-instantly, but CMS page edits and navigation changes follow a different, partly undefined freshness regime (menu content can lag by days; page behavior rides default framework semantics). This asymmetry is undocumented and surprising for store operators.
- **Proposed direction:** Give pages and menus explicit cache tags/lifetimes and register the corresponding Shopify webhook topics (e.g., `pages/*`, menu-bearing resource events) in the revalidation handler, or consciously document the chosen freshness model.
- **Expected benefit:** Uniform, explainable staleness bounds across all Shopify-sourced content.
- **Prerequisites:** Confirmation of which Shopify topics fire for the resources involved; FD-1 coverage for the new branches.
- **Priority:** Medium. **Confidence:** Evidence-backed (asymmetry is directly observable; ideal fix depends on external webhook behavior).

#### FD-7 — Extract and document the provider contract

- **Current evidence:** The README declares the extensibility mechanism as replacing `lib/shopify` "while leaving the rest of the template mostly unchanged." However, the domain types (`Cart`, `Product`, `Collection`, `Page`, `Menu`) are intermixed with Shopify-specific types in `lib/shopify/types.ts`, and every page/component imports directly from `lib/shopify`. Required behavioral conventions (path rewriting such as `/collections/*` → `/search/*` in `getMenu`, the `nextjs-frontend-hidden` tag semantics, the `TAGS` cache-tag vocabulary that `components/cart/actions.ts` also depends on) exist only inside the Shopify implementation.
- **Limitation:** The abstraction boundary is positional rather than declared. A provider author must reverse-engineer the export surface, type shapes, tagging vocabulary, and reshape conventions from the Shopify code — and has no conformance test to validate against (see FD-1).
- **Proposed direction:** Lift the domain types, the data-layer function signatures, the cache-tag vocabulary, and the behavioral contract (path conventions, hidden-item semantics, revalidation responsibilities) into a provider-neutral module with written documentation; leave `lib/shopify` as the reference implementation of that interface.
- **Expected benefit:** Lowers the cost and raises the fidelity of the eleven+ community provider ports the README links; creates the seam that any future multi-provider work would require.
- **Prerequisites:** FD-1, so the extracted contract is enforceable mechanically.
- **Priority:** Medium — high leverage for the template's ecosystem role, low urgency for the running demo.
- **Confidence:** Strongly justified (fork-swappability is explicit project intent; the undeclared contract is directly observable).

#### FD-8 — Operational observability

- **Current evidence:** All diagnostics are `console.log`/`console.error` calls inside request paths (`lib/shopify/index.ts`, `components/cart/actions.ts`); `app/error.tsx` renders a generic retry screen with no reporting hook; no telemetry, tracing, or analytics configuration exists anywhere in the tree.
- **Limitation:** Shopify API degradation, repeated revalidation-auth failures, and cart-action failures are indistinguishable in production from silence; the template offers fork adopters no instrumentation seam.
- **Proposed direction:** Centralize error/diagnostic emission behind a small internal logger used by `shopifyFetch` and the revalidation/cart paths, and expose a defined hook where an error-reporting service can attach; instrument the revalidation endpoint's rejection counters.
- **Expected benefit:** Turns silent failures into observable signals without coupling the template to a specific vendor.
- **Prerequisites:** None. **Priority:** Medium. **Confidence:** Gap evidence-backed; solution shape deliberately vendor-neutral.

#### FD-9 — Managed currency of the Shopify API version and dependencies

- **Current evidence:** `SHOPIFY_GRAPHQL_API_ENDPOINT = "/api/2023-01/graphql.json"` is hardcoded in `lib/constants.ts`; `react`/`react-dom` are pinned exactly (`19.0.0`); Next.js is pinned to a canary (FD-2).
- **Limitation:** Shopify sunsets Storefront API versions on a published quarterly schedule; a hardcoded version guarantees eventual hard breakage that no repository process currently watches. Exact pins elsewhere amplify drift.
- **Proposed direction:** Schedule periodic Storefront API version review (the queries here use long-stable primitives, so upgrades are expected to be low-churn); consider making the version suffix configurable via environment alongside `SHOPIFY_STORE_DOMAIN`; adopt a routine dependency-refresh cadence once FD-1 provides a safety net.
- **Expected benefit:** Converts an inevitable outage-class event into a routine maintenance task.
- **Prerequisites:** FD-1. **Priority:** Medium (time-bounded by Shopify's sunset calendar rather than severity). **Confidence:** Evidence-backed.

### 4.3 Longer-Term and Exploratory Directions

These directions depend on scale, product scope, or requirements that the repository does not establish. They are recorded because the architecture creates a natural seam for them — they are **not** presented as needed today.

#### FD-10 — Richer in-template search (exploratory)
The README itself designates search richness as an integration path (Orama adds typeahead and vector similarity out of tree), and the built-in search is a single query parameter passed to Shopify (`app/search/page.tsx`, `getProductsQuery`). If the template later aims to demonstrate more of the platform interactively (client-side streaming, partial prerendering under rapid input), deeper first-party search would exercise those capabilities. Until then, the integration ecosystem remains the intended home for this work.

#### FD-11 — Storefront capability expansion: customer accounts, localization, wishlists (exploratory)
The codebase contains no authentication, customer-account, order-history, wishlist, or locale-routing code, and no textual signal of intent to add them. Such capabilities are common asks for production storefronts and would build naturally on the existing Server Action + optimistic-state patterns, but committing them would exceed the template's demonstrated scope (a performance-focused showcase with Shopify-owned checkout). They belong on a product-decision agenda, not an engineering backlog derived from this repository.

#### FD-12 — Runtime-selectable providers (exploratory, contingent on FD-7)
The declared model is one maintained provider plus forks. If FD-7 produces a declared contract, a configuration-selected provider registry (several implementations coexisting behind `lib/shopify`'s signatures) becomes technically straightforward. The repository provides no requirement for this; it is recorded only as the logical continuation of the contract-extraction work.

---

## 5. Phased Evolution Narrative

The dependency structure of the directions above suggests a sequence:

```mermaid
flowchart TD
    subgraph Phase1[Phase 1 — Make change safe]
        FD1[FD-1 Test harness + CI]
        FD2[FD-2 Stabilization tracking<br/>and unstable-API containment]
    end
    subgraph Phase2[Phase 2 — Correctness and resilience]
        FD3[FD-3 Pagination /<br/>large-catalog honesty]
        FD5[FD-5 Cart robustness +<br/>typed errors]
        FD4[FD-4 Webhook HMAC hardening]
        FD6[FD-6 Content-freshness parity]
        FD9[FD-9 API-version and<br/>dependency currency]
    end
    subgraph Phase3[Phase 3 — Structural leverage]
        FD7[FD-7 Declared provider contract]
        FD8[FD-8 Observability seam]
    end
    subgraph Phase4[Phase 4 — Scale/scope-contingent]
        FD10[FD-10 Richer search]
        FD11[FD-11 Accounts / localization]<br/>product decision required]
        FD12[FD-12 Runtime-selectable providers]
    end
    FD1 --> FD3
    FD1 --> FD5
    FD1 --> FD2
    FD1 --> FD4
    FD1 --> FD9
    FD2 --> FD9
    FD1 --> FD7
    FD7 -.-> FD12
    FD8 -.-> FD10
```

- **Phase 1 (FD-1, FD-2)** comes first because every other item modifies code that currently has no regression safety net, and because FD-2's eventual canary-to-stable migration is itself the kind of change that demands one.
- **Phase 2 (FD-3, FD-4, FD-5, FD-6, FD-9)** removes silent correctness ceilings and hardens the two flows where the application acts on trust boundaries or money: catalog visibility and cart/webhook handling.
- **Phase 3 (FD-7, FD-8)** invests in the seams — the declared provider interface and the observability hook — that raise the value of everything already shipped, particularly for downstream forks.
- **Phase 4 (FD-10–FD-12)** activates only if product decisions expand scope; each has a prepared landing spot but no evidentiary mandate today.

---

## 6. Directions Considered and Deliberately Not Recommended

Consistent with the evidence discipline applied above, the following commonly suggested moves find no support in this repository:

- **Adding a database or persistent backend.** The application is correctly stateless; cart state is owned by Shopify and referenced by a cookie. No workload or data-ownership evidence motivates server-side persistence.
- **Splitting into services or queues.** All operations are short request/response GraphQL calls with tag-based caching; no synchronous bottleneck, queueing need, or long-running job exists in the traced execution paths.
- **Replacing the fork-based provider model with a plugin system immediately.** The README commits to the fork model; FD-7 improves life within that model, while FD-12 remains explicitly conditional.
- **Rewriting state management or styling.** The `useOptimistic` cart context and Tailwind 4 setup are coherent, current, and consistent with the template's demonstrative purpose; no evidence indicates they constrain required behavior.
- **Broad security retrofits beyond FD-4/FD-5.** The application exposes one write endpoint (the revalidation webhook) and delegates all sensitive operations (payment, account, inventory) to Shopify-hosted surfaces; the evidenced hardening targets are the ones enumerated.

---

## 7. Confidence Summary and Limitations

- **Evidence-backed:** FD-1, FD-2, FD-3 (direct observation of manifests, configs, and query definitions); the factual bases of FD-4 through FD-6 and FD-8, FD-9.
- **Strongly justified:** The directions themselves for FD-4, FD-5, FD-6 (multiple converging findings; the repository does not propose them), and FD-7 (explicit fork-swappability intent meets an undeclared contract).
- **Exploratory:** FD-10, FD-11, FD-12 — labeled as such and dependent on decisions outside this repository.
- **Unknowns affecting precision:** Actual production traffic levels, catalog sizes of adopting stores, Shopify webhook behavior for page/menu resources, and the timeline on which Next.js stabilizes the experimental feature set are not determinable from the repository; priorities that depend on them (notably FD-3's urgency and FD-6's fix shape) are calibrated accordingly.