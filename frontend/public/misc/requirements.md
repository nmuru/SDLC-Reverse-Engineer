# Requirements — Next.js Commerce (Shopify Edition)

This document reconstructs the requirements evidenced by the repository. Each requirement is classified as **Verified** (directly stated or strongly established by executable behavior), **Inferred** (implied by multiple implementation artifacts), or **Uncertain** (plausible but not conclusively established). Requirements are derived from the application source, configuration, routing, schema, validation, error handling, and deployment evidence present in the target repository.

The application is a high‑performance, server‑rendered **Next.js (App Router)** e‑commerce storefront template that integrates with the **Shopify Storefront API**. It is not a complete commerce platform; it is a customer‑facing frontend that delegates product, collection, and cart state to a configured Shopify store.

---

## 1. Functional Requirements

### 1.1 Storefront Browsing

| ID | Requirement | Certainty |
|----|-------------|-----------|
| FR‑BROWSE‑1 | The system shall render a public homepage that displays a featured three‑item product grid and a horizontal product carousel drawn from predefined Shopify collections. | Verified — `app/page.tsx`, `components/grid/three-items.tsx`, `components/carousel.tsx` |
| FR‑BROWSE‑2 | The homepage featured grid shall source products from the Shopify collection with handle `hidden-homepage-featured-items`. | Verified — `components/grid/three-items.tsx:53` |
| FR‑BROWSE‑3 | The homepage carousel shall source products from the Shopify collection with handle `hidden-homepage-carousel` and shall render nothing if that collection is empty. | Verified — `components/carousel.tsx:7‑11` |
| FR‑BROWSE‑4 | The system shall expose a public search page that lists products with optional text query, sort selection, and pagination over the first **100** products. | Verified — `app/search/page.tsx`, `lib/shopify/queries/product.ts` (`getProducts`, `first: 100`) |
| FR‑BROWSE‑5 | The system shall expose a public collection (category) page for any Shopify collection handle, rendering the products within that collection with sort support. | Verified — `app/search/[collection]/page.tsx` |
| FR‑BROWSE‑6 | The system shall expose a public product detail page for any Shopify product handle, including gallery, description, price, variant selection, and recommendations. | Verified — `app/product/[handle]/page.tsx` |
| FR‑BROWSE‑7 | The system shall expose a generic content page (`/[page]`) that renders a Shopify online‑store page by handle, including its title, body, and SEO metadata. | Verified — `app/[page]/page.tsx`, `lib/shopify/queries/page.ts` |
| FR‑BROWSE‑8 | The system shall render a **404** (`notFound`) response when a requested product handle, collection handle, or page handle does not resolve in Shopify. | Verified — `notFound()` calls in `app/product/[handle]/page.tsx`, `app/search/[collection]/page.tsx`, `app/[page]/page.tsx` |
| FR‑BROWSE‑9 | The system shall hide any Shopify product carrying the tag `nextjs-frontend-hidden` from listings, and shall mark such products with `noindex, nofollow` robots directives. | Verified — `lib/shopify/index.ts:189‑193` (`reshapeProduct` filter), `HIDDEN_PRODUCT_TAG` constant, `app/product/[handle]/page.tsx:22‑34` |
| FR‑BROWSE‑10 | The system shall hide any Shopify collection whose handle starts with `hidden-` from the public collections filter on the search page. | Verified — `lib/shopify/index.ts:389‑392` (collections filter) |

### 1.2 Search and Discovery

| ID | Requirement | Certainty |
|----|-------------|-----------|
| FR‑SEARCH‑1 | The system shall provide a free‑text search input in the navbar (and in the mobile menu) that submits to `/search` with a query parameter `q`. | Verified — `components/layout/navbar/search.tsx` |
| FR‑SEARCH‑2 | The system shall provide a sort selector on the search and collection pages that supports at least: Relevance, Trending (best‑selling), Latest arrivals (created descending), Price ascending, and Price descending. | Verified — `lib/constants.ts` (`sorting` array) |
| FR‑SEARCH‑3 | The system shall provide a collections filter on the search layout that lists all non‑hidden Shopify collections, with a synthetic “All” collection entry representing the unfiltered catalog. | Verified — `components/layout/search/collections.tsx`, `lib/shopify/index.ts:357‑394` |
| FR‑SEARCH‑4 | The system shall support text query in combination with sort; when a query returns zero products, the UI shall display a “no products that match” message. | Verified — `app/search/page.tsx:24‑31` |
| FR‑SEARCH‑5 | Selecting a collection shall clear any active `q` parameter to prevent a query that contradicts the active collection. | Verified — `components/layout/search/filter/item.tsx:17` (`newParams.delete("q")`) |

### 1.3 Product Detail and Variant Selection

| ID | Requirement | Certainty |
|----|-------------|-----------|
| FR‑PDP‑1 | The system shall render up to the first five product images as a gallery with previous/next navigation and a thumbnail strip, and shall persist the active image index in the URL via an `image` query parameter. | Verified — `app/product/[handle]/page.tsx:91‑96`, `components/product/gallery.tsx` |
| FR‑PDP‑2 | The system shall render a variant selector for any product with more than one variant; for products with zero or one options, the selector shall be hidden. | Verified — `components/product/variant-selector.tsx:22‑28` |
| FR‑PDP‑3 | The system shall mark each option value as **Out of Stock** and disable selection when no variant with that exact option combination is available. | Verified — `components/product/variant-selector.tsx:84‑95` |
| FR‑PDP‑4 | The system shall persist the selected variant combination in the URL via lower‑cased option‑name query parameters so that links and refresh preserve the selection. | Verified — `components/product/variant-selector.tsx:42‑46`; `components/cart/add-to-cart.tsx:64‑72` |
| FR‑PDP‑5 | The system shall display the maximum‑variant price on the product description surface and the actual unit price in the cart totals. | Verified — `components/product/product-description.tsx`, `lib/shopify/types.ts` `priceRange.maxVariantPrice` |
| FR‑PDP‑6 | The system shall render a list of up to **N** product recommendations on the product page when the Storefront API returns any. | Verified — `app/product/[handle]/page.tsx:113‑148`; `getProductRecommendations` uses `first: 100` indirectly through the product fragment |
| FR‑PDP‑7 | The system shall expose the product as `schema.org/Product` JSON‑LD on the product page, including availability, price range, and currency. | Verified — `app/product/[handle]/page.tsx:58‑82` |
| FR‑PDP‑8 | The system shall disable the **Add to Cart** button when the product is not available for sale and shall display “Out Of Stock”. | Verified — `components/cart/add-to-cart.tsx:22‑28` |
| FR‑PDP‑9 | The system shall disable the **Add to Cart** button when a product with multiple variants is presented without a complete option selection. | Verified — `components/cart/add-to-cart.tsx:30‑43` |

### 1.4 Cart Management

| ID | Requirement | Certainty |
|----|-------------|-----------|
| FR‑CART‑1 | The system shall maintain a single shopping cart per browser session, identified by a `cartId` cookie that is created lazily on the first interaction with the cart UI. | Verified — `components/cart/actions.ts:103‑106` (`createCartAndSetCookie`); `components/cart/modal.tsx:31‑35` |
| FR‑CART‑2 | The system shall add items to the cart by merchandise variant ID and quantity, defaulting the per‑add quantity to **1**. | Verified — `components/cart/actions.ts:15‑29`, `addToCartMutation` |
| FR‑CART‑3 | The system shall support removing an item from the cart by its cart line ID. | Verified — `components/cart/actions.ts:31‑52`, `removeFromCartMutation` |
| FR‑CART‑4 | The system shall support updating the quantity of a cart line; setting the quantity to **0** shall remove the line instead of sending an update. | Verified — `components/cart/actions.ts:54‑96` |
| FR‑CART‑5 | The system shall support adding an item to the cart even when the cart does not yet contain a line for that merchandise (the action will add rather than update). | Verified — `components/cart/actions.ts:86‑89` |
| FR‑CART‑6 | The cart UI shall display line items sorted alphabetically by product title. | Verified — `components/cart/modal.tsx:96‑100` |
| FR‑CART‑7 | The cart UI shall display the per‑line subtotal, the cart subtotal, taxes (zero by default in the optimistic state), and a placeholder indicating that shipping is calculated at checkout. | Verified — `components/cart/modal.tsx:196‑216`; `components/cart/cart-context.tsx:114‑117` |
| FR‑CART‑8 | The cart UI shall provide controls to increase, decrease, and remove each line item, and to close the cart. | Verified — `components/cart/modal.tsx`, `components/cart/edit-item-quantity-button.tsx`, `components/cart/delete-item-button.tsx` |
| FR‑CART‑9 | The cart UI shall open automatically whenever the total quantity increases, and shall provide a manual open affordance from the navbar. | Verified — `components/cart/modal.tsx:36‑48, 51‑54` |
| FR‑CART‑10 | The cart UI shall indicate that the cart is empty with a dedicated empty‑state view when no items are present. | Verified — `components/cart/modal.tsx:85‑91` |
| FR‑CART‑11 | The system shall redirect the user to the Shopify‑hosted checkout URL provided by the Storefront API when the user initiates checkout. | Verified — `components/cart/actions.ts:98‑101` (`redirectToCheckout`); `components/cart/modal.tsx:218‑220` |
| FR‑CART‑12 | The system shall display an error message (“Error adding item to cart”) when an add‑to‑cart server action fails, and shall display “Item not found in cart” when a remove operation cannot locate the requested line. | Verified — `components/cart/actions.ts:20‑21, 27‑28, 47, 50, 67, 93‑95` |
| FR‑CART‑13 | The cart state shall be available to client components through a `CartContext` that provides the current cart and helpers to add or update items optimistically. | Verified — `components/cart/cart-context.tsx` |
| FR‑CART‑14 | The system shall support per‑line variant deep‑linking by carrying non‑default variant options as URL search parameters on the cart line links. | Verified — `components/cart/modal.tsx:102‑117` |

### 1.5 Navigation, Layout, and Content

| ID | Requirement | Certainty |
|----|-------------|-----------|
| FR‑NAV‑1 | The system shall display a site‑wide navbar that includes the brand logo, a menu sourced from the Shopify menu handle `next-js-frontend-header-menu`, a search input, and the cart affordance. | Verified — `components/layout/navbar/index.tsx:13, 31‑58` |
| FR‑NAV‑2 | The system shall display a footer that includes a menu sourced from the Shopify menu handle `next-js-frontend-footer-menu`, site name, and a “Deploy” affordance. | Verified — `components/layout/footer.tsx:15, 42` |
| FR‑NAV‑3 | The system shall provide a mobile menu that opens from a button, supports search, and closes on route change, on resize above the mobile breakpoint, or via an explicit close button. | Verified — `components/layout/navbar/mobile-menu.tsx` |
| FR‑NAV‑4 | The system shall display a one‑time welcome toast on first visit (gated by a `welcome-toast=2` cookie) and shall suppress the toast on viewports shorter than **650 px**. | Verified — `components/welcome-toast.tsx:9‑16` |
| FR‑NAV‑5 | The system shall render a global error boundary that surfaces a generic storefront error message and a “Try Again” action bound to the Next.js error `reset()` API. | Verified — `app/error.tsx` |

### 1.6 SEO and Discoverability

| ID | Requirement | Certainty |
|----|-------------|-----------|
| FR‑SEO‑1 | The system shall provide a `robots.txt` that allows all user agents and advertises the sitemap location. | Verified — `app/robots.ts` |
| FR‑SEO‑2 | The system shall provide a sitemap that includes the homepage, every non‑hidden collection, every product (using its `updatedAt` for `lastModified`), and every Shopify online‑store page. | Verified — `app/sitemap.ts` |
| FR‑SEO‑3 | The system shall generate page‑level Next.js metadata (title, description, OpenGraph) for the home, product, collection, and page routes, falling back from `seo.*` to the product or page title/description. | Verified — `app/layout.tsx`, `app/product/[handle]/page.tsx:13‑48`, `app/search/[collection]/page.tsx:9‑24`, `app/[page]/page.tsx:7‑24` |
| FR‑SEO‑4 | The system shall generate OpenGraph images for product, collection, page, and home routes using a templated component. | Verified — `app/opengraph-image.tsx`, `app/[page]/opengraph-image.tsx`, `app/search/[collection]/opengraph-image.tsx`, `components/opengraph-image.tsx` |
| FR‑SEO‑5 | The system shall respect the Shopify SEO data (title and description) on a product or page when present, and fall back to the entity title/description otherwise. | Verified — same artifacts as FR‑SEO‑3 |

### 1.7 Provider Integration and Caching

| ID | Requirement | Certainty |
|----|-------------|-----------|
| FR‑INTEG‑1 | The system shall expose all commerce data through a `lib/shopify` abstraction that performs GraphQL operations against the Shopify Storefront API. | Verified — `lib/shopify/index.ts` |
| FR‑INTEG‑2 | The system shall allow a deployment to operate without a configured Shopify backend by returning safe empty results (empty arrays, `undefined`, or a synthetic “All” collection) for read paths and by logging a skip message. | Verified — `lib/shopify/index.ts:324‑329, 355‑370, 403‑406, 448‑451` |
| FR‑INTEG‑3 | The system shall issue GraphQL requests with the Storefront access token in the `X-Shopify-Storefront-Access-Token` header. | Verified — `lib/shopify/index.ts:87‑91` |
| FR‑INTEG‑4 | The system shall normalize Shopify “Connection/Edge” responses into flat arrays and shall re‑map Shopify collection handles to the storefront’s `/search/[collection]` paths. | Verified — `removeEdgesAndNodes`, `reshapeCollection` in `lib/shopify/index.ts` |
| FR‑INTEG‑5 | The system shall use Next.js’s `"use cache"` and `cacheTag`/`cacheLife` directives to cache store data, tagged with `collections`, `products`, or `cart`. | Verified — `lib/shopify/index.ts:270‑292, 297‑309, 320‑348, 351‑395, 398‑423, 443‑461, 466‑478, 480‑503` |
| FR‑INTEG‑6 | The system shall provide a webhook endpoint at **POST** `/api/revalidate` that requires a secret (`SHOPIFY_REVALIDATION_SECRET`) and revalidates either the `collections` or `products` cache tag based on the `x-shopify-topic` header. | Verified — `app/api/revalidate/route.ts`, `lib/shopify/index.ts:506‑543` |
| FR‑INTEG‑7 | The revalidation endpoint shall respond with **HTTP 200** for unrecognized Shopify topics, with **HTTP 401** for missing/invalid secrets, and with **HTTP 200** plus a `revalidated` flag for valid cache‑invalidation requests. | Verified — `lib/shopify/index.ts:524‑542` |

---

## 2. Business and Domain Rules

| ID | Rule | Certainty |
|----|------|-----------|
| BR‑1 | The system must be presented as a **Next.js App Router** storefront and must remain a customer‑facing surface; checkout itself is hosted by Shopify. | Verified — `redirectToCheckout` in `components/cart/actions.ts`; README, layout metadata |
| BR‑2 | A product may be hidden from public listing and from indexing by tagging it `nextjs-frontend-hidden`; the system must treat such products as not for sale in listings. | Verified — `reshapeProduct` filter |
| BR‑3 | A collection may be hidden from the storefront navigation by prefixing its handle with `hidden-`; the system must exclude these from the collections filter. | Verified — collections filter in `getCollections` |
| BR‑4 | A product with no available variant combination for the user’s selected options must be presented as disabled and marked out of stock, not silently re‑routed. | Verified — `VariantSelector` disabled/aria‑disabled logic |
| BR‑5 | The system must not assume a default currency; prices are formatted using the currency code returned by Shopify per money value. | Verified — `components/price.tsx:15‑19` (uses `Intl.NumberFormat` with `currencyCode`) |
| BR‑6 | The “All” collection is always available in the collections filter, even when no collections are returned from Shopify, so the search page always has a navigable entry point. | Verified — `getCollections` always prepends an `All` entry |
| BR‑7 | Cart total tax is displayed as **zero** in the optimistic cart and is corrected from the Storefront response when the real cart is fetched. | Verified — `createEmptyCart` and `cartReducer` set `totalTaxAmount` to `0`; `reshapeCart` defaults it when missing |
| BR‑8 | The default sort for the search and collection pages is “Relevance”. | Verified — `defaultSort` in `lib/constants.ts`; used as fallback in `app/search/page.tsx` and `app/search/[collection]/page.tsx` |
| BR‑9 | Search results are limited to the first **100** products returned by the Storefront API. | Verified — `getProductsQuery` `first: 100`; `getCollectionProductsQuery` `first: 100`; `getCollectionsQuery` `first: 100`; `getPagesQuery` `first: 100`; `cartFragment` `lines(first: 100)`; `productFragment` `variants(first: 250)`, `images(first: 20)` |
| BR‑10 | The system treats a Shopify Storefront `cart` of `null` as a non‑cart (e.g., post‑checkout) and surfaces this to the UI as no cart. | Verified — `getCart` returns `undefined` when `res.body.data.cart` is `null` |
| BR‑11 | Adding an item without a selected variant ID is a domain error; the action must reject it and return an error message instead of performing the mutation. | Verified — `addItem` checks `selectedVariantId` |
| BR‑12 | The system treats cookie‑based persistence of the cart identifier as authoritative for a session; there is no concept of guest versus authenticated cart. | Verified — cookie is the only cart identifier; `getCart` falls back to `undefined` when no cookie is present |

---

## 3. Interface Requirements

### 3.1 External HTTP Interface

The application exposes exactly one HTTP endpoint, dedicated to provider integration.

| Method | Path | Purpose | Auth | Inputs | Outputs | Certainty |
|--------|------|---------|------|--------|---------|-----------|
| **POST** | `/api/revalidate` | Cache invalidation triggered by a Shopify webhook | Shared secret in `?secret=` query param matching `SHOPIFY_REVALIDATION_SECRET` | `x-shopify-topic` header (one of `collections/create|delete|update` or `products/create|delete|update`); `secret` query param | `200 {status, revalidated, now}` on cache invalidation; `200 {status}` for other topics; `401 {status}` for invalid secret | Verified — `app/api/revalidate/route.ts`, `lib/shopify/index.ts:506‑543` |

### 3.2 Public Site Routes (UI/SSR)

| Route | Purpose | Source Data | Certainty |
|-------|---------|-------------|-----------|
| `/` | Homepage with featured grid and carousel | Shopify collections `hidden-homepage-featured-items` and `hidden-homepage-carousel` | Verified |
| `/search` | Full‑catalog search and sort | `getProducts({ sortKey, reverse, query })` | Verified |
| `/search/[collection]` | Collection (category) page | `getCollection(handle)`, `getCollectionProducts` | Verified |
| `/product/[handle]` | Product detail | `getProduct(handle)`, `getProductRecommendations(id)` | Verified |
| `/[page]` | Generic Shopify online‑store page | `getPage(handle)` | Verified |
| `/sitemap.xml` | Sitemap | `getCollections`, `getProducts`, `getPages` | Verified |
| `/robots.txt` | Robots | Static | Verified |
| `/opengraph-image` (and per‑route variants) | OpenGraph image generation | `next/og` `ImageResponse` with embedded font | Verified |

### 3.3 GraphQL Interface (Shopify Storefront API)

| Operation | Type | Variables | Returned Fragment | Certainty |
|-----------|------|-----------|--------------------|-----------|
| `cartCreate` | Mutation | `lineItems: [CartLineInput!]` | `cart` | Verified |
| `cartLinesAdd` | Mutation | `cartId: ID!`, `lines: [CartLineInput!]!` | `cart` | Verified |
| `cartLinesUpdate` | Mutation | `cartId: ID!`, `lines: [CartLineUpdateInput!]!` | `cart` | Verified |
| `cartLinesRemove` | Mutation | `cartId: ID!`, `lineIds: [ID!]!` | `cart` | Verified |
| `cart(id)` | Query | `cartId: ID!` | `cart` | Verified |
| `product(handle)` | Query | `handle: String!` | `product` | Verified |
| `products(sortKey, reverse, query, first:100)` | Query | optional `sortKey`, `reverse`, `query` | `product` | Verified |
| `productRecommendations(productId)` | Query | `productId: ID!` | `product` | Verified |
| `collection(handle)` | Query | `handle: String!` | `collection` | Verified |
| `collections(first:100, sortKey:TITLE)` | Query | — | `collection` | Verified |
| `collection(handle).products(...)` | Query | `handle`, optional `sortKey`, `reverse` | `product` | Verified |
| `menu(handle)` | Query | `handle: String!` | `items { title, url }` | Verified |
| `pageByHandle(handle)` | Query | `handle: String!` | `page` | Verified |
| `pages(first:100)` | Query | — | `page` | Verified |

All requests use the Storefront API endpoint `SHOPIFY_GRAPHQL_API_ENDPOINT = /api/2023-01/graphql.json` (`lib/constants.ts:51`).

### 3.4 URL and Query Parameter Contracts

| Parameter | Used On | Meaning | Certainty |
|-----------|---------|---------|-----------|
| `q` | `/search` | Free‑text search query passed to the Storefront `products(query: …)` argument | Verified |
| `sort` | `/search`, `/search/[collection]` | One of `null` (Relevance), `trending‑desc`, `latest‑desc`, `price‑asc`, `price‑desc` | Verified |
| `<optionNameLowerCase>` | `/product/[handle]` | Selected variant option values keyed by lower‑cased option name | Verified |
| `image` | `/product/[handle]` | Zero‑based index of the active product image | Verified |

### 3.5 Configuration Interface (Environment Variables)

| Variable | Required | Purpose | Certainty |
|----------|----------|---------|-----------|
| `SHOPIFY_STORE_DOMAIN` | **Yes** (for full functionality) | Shopify store domain, used to build the Storefront endpoint | Verified — `.env.example`, `lib/shopify/index.ts:61‑64` |
| `SHOPIFY_STOREFRONT_ACCESS_TOKEN` | **Yes** (for full functionality) | Token sent in `X-Shopify-Storefront-Access-Token` header | Verified — `.env.example`, `lib/shopify/index.ts:65, 89` |
| `SHOPIFY_REVALIDATION_SECRET` | **Yes** (for revalidation endpoint) | Shared secret for `POST /api/revalidate` | Verified — `.env.example`, `lib/shopify/index.ts:520‑527` |
| `SITE_NAME` | No | Used in the layout title, navbar, and footer | Verified — `.env.example`, `app/layout.tsx`, `components/layout/navbar/index.tsx`, `components/layout/footer.tsx` |
| `COMPANY_NAME` | No | Used in the footer copyright | Verified — `.env.example`, `components/layout/footer.tsx` |
| `VERCEL_PROJECT_PRODUCTION_URL` | No | Used to compute the canonical site URL (`baseUrl`) for absolute URLs and OG images | Verified — `lib/utils.ts:3‑5` |

`lib/utils.ts:validateEnvironmentVariables` enforces that the two Storefront variables are present and that `SHOPIFY_STORE_DOMAIN` does not contain bracket characters.

---

## 4. Data Requirements

### 4.1 Domain Entities

| Entity | Source | Required Fields (UI‑consumed) | Certainty |
|--------|--------|------------------------------|-----------|
| **Product** | Storefront API | `id`, `handle`, `title`, `description`, `descriptionHtml`, `availableForSale`, `options[]`, `priceRange.{minVariantPrice,maxVariantPrice}.{amount,currencyCode}`, `variants[]` with `{id, title, availableForSale, selectedOptions[], price.{amount,currencyCode}}`, `featuredImage` (and `images[]` first 20), `seo.{title,description}`, `tags[]`, `updatedAt` | Verified — `lib/shopify/types.ts`, `fragments/product.ts` |
| **Collection** | Storefront API | `handle`, `title`, `description`, `seo.{title,description}`, `updatedAt`; a derived `path: /search/<handle>` is added by `reshapeCollection` | Verified — `types.ts`, `index.ts:143‑153` |
| **Cart** | Storefront API | `id`, `checkoutUrl`, `cost.{subtotalAmount,totalAmount,totalTaxAmount}`, `lines[]` (max 100) of `CartItem`, `totalQuantity` | Verified — `types.ts:98‑108`, `fragments/cart.ts` |
| **CartItem** | Derived from Cart | `id`, `quantity`, `cost.totalAmount.{amount,currencyCode}`, `merchandise.{id,title,selectedOptions[],product.{id,handle,title,featuredImage}}` | Verified — `types.ts:22‑37` |
| **Menu** | Storefront API | `{ title, path }` produced by reshaping `menu(handle).items`; the path is derived by replacing the Shopify host and `/collections`, `/pages` segments | Verified — `index.ts:415‑422` |
| **Page** | Storefront API | `id`, `title`, `handle`, `body`, `bodySummary`, `seo?`, `createdAt`, `updatedAt` | Verified — `types.ts:60‑69` |
| **Image** | Storefront API | `url`, `altText`, `width`, `height` | Verified — `types.ts:43‑48` |
| **Money** | Storefront API | `amount` (decimal string), `currencyCode` | Verified — `types.ts:55‑58` |

### 4.2 Persistence and Caching

| Requirement | Certainty |
|-------------|-----------|
| The system shall not maintain its own product, collection, page, or menu database; all such data is read on demand from Shopify and cached in Next.js’s per‑request / global cache. | Verified — only data layer in `lib/shopify` is the Storefront fetch; no DB drivers are present in dependencies |
| The system shall persist only the cart identifier in a browser cookie (`cartId`); cart contents live in Shopify. | Verified — `components/cart/actions.ts:105` (`cookies().set("cartId", ...)`) |
| The cart state used in UI rendering is delivered through React Server Components as a Promise (`getCart()` returning a `Promise<Cart | undefined>`) consumed via React’s `use()` in a client‑context provider. | Verified — `app/layout.tsx:31‑36`, `components/cart/cart-context.tsx:213` |
| The system shall tag cached Storefront data with `collections`, `products`, or `cart` and shall bind lifetimes of **days** for catalog data and **seconds** for cart data. | Verified — `cacheTag`/`cacheLife` in `lib/shopify/index.ts` |
| The system shall allow a configured Shopify webhook to invalidate the `products` or `collections` cache tag on demand. | Verified — revalidation endpoint |
| The system shall not retain cart contents across sessions beyond what Shopify itself retains; only the cookie is application‑managed. | Verified — only the `cartId` cookie is set |
| The cart’s `totalTaxAmount` is required to be a present value for rendering; the application defaults it to `0.0` in the same currency as the cart’s `totalAmount` if Shopify omits it. | Verified — `reshapeCart` in `lib/shopify/index.ts:129‑141` |

### 4.3 Input Validation

| Requirement | Certainty |
|-------------|-----------|
| The system shall validate that the `SHOPIFY_STORE_DOMAIN` environment variable does not contain `[` or `]` characters before allowing startup of a sitemap or other Storefront‑dependent flows. | Verified — `validateEnvironmentVariables` in `lib/utils.ts:42‑50` |
| The system shall ensure `SHOPIFY_STORE_DOMAIN` is prefixed with `https://` before building the Storefront endpoint. | Verified — `ensureStartsWith` in `lib/shopify/index.ts:61‑64` |
| The system shall treat a missing `cartId` cookie as “no cart” rather than a request error. | Verified — `getCart` returns `undefined` when cookie is missing |
| The system shall not issue a Storefront request for a cart update/add/remove if the cart ID is not present (it instead returns an error). | Verified — cart actions require an existing cart cookie to look up the cart; `addToCart` etc. read `cartId` from cookies and pass to mutations |

---

## 5. Security Requirements

| ID | Requirement | Certainty |
|----|-------------|-----------|
| SEC‑1 | The system shall authenticate inbound cache‑invalidation requests to `POST /api/revalidate` using a shared secret passed as the `secret` query parameter, validated against the `SHOPIFY_REVALIDATION_SECRET` environment variable. Requests without a valid secret shall be rejected with **HTTP 401**. | Verified — `lib/shopify/index.ts:519‑527` |
| SEC‑2 | The system shall use the Storefront API access token only in the `X-Shopify-Storefront-Access-Token` request header and shall not expose it to the browser beyond what is needed to render server‑rendered output. | Verified — token is read from `process.env` server‑side and sent in headers (`lib/shopify/index.ts:65, 89`) |
| SEC‑3 | The system shall treat Storefront errors returned in the GraphQL `errors` array as exceptions, and shall surface a normalized error to the caller. | Verified — `lib/shopify/index.ts:100‑122` |
| SEC‑4 | The system shall use **HTTPS** for service‑to‑service calls to Shopify, with the `https://` prefix enforced by `ensureStartsWith`. | Verified — `lib/shopify/index.ts:61‑64` |
| SEC‑5 | The system shall use Next.js’s `next/image` for product imagery and shall restrict remote image sources to `cdn.shopify.com` under `/s/files/**` to prevent arbitrary third‑party image loading. | Verified — `next.config.ts:7‑15` |
| SEC‑6 | The system shall serve OpenGraph images from a local `ImageResponse` generator that loads a bundled font, not from arbitrary user‑controlled URLs. | Verified — `components/opengraph-image.tsx` |
| SEC‑7 | The system shall not collect, store, or transmit any user credentials; the only user‑identifying artifact is a `cartId` cookie and a UI‑only `welcome‑toast` cookie. | Verified — no authentication library present; cookies set are limited to those two |
| SEC‑8 | The system shall persist a non‑sensitive “welcome‑toast” cookie for up to **one year** to suppress duplicate welcome messages. | Verified — `components/welcome-toast.tsx:15` |
| SEC‑9 | The system shall guard image rendering with `next/image` to avoid arbitrary remote loading even where URLs are user‑controlled (e.g., product image URLs from Shopify). | Verified — `GridTileImage`, `Gallery`, product page, and cart modal all use `next/image` |
| SEC‑10 | The application documentation explicitly warns developers **not** to commit the `.env` file because it contains secrets that can control the Shopify store. | Verified — `README.md:50‑51` |

---

## 6. Non‑Functional Requirements

| ID | Requirement | Certainty |
|----|-------------|-----------|
| NFR‑PERF‑1 | The system shall cache store catalog data with a lifetime of **days** so that homepage, search, and collection pages do not re‑query Shopify on every request. | Verified — `cacheLife("days")` on collection/product/menu queries |
| NFR‑PERF‑2 | The system shall cache the active cart with a lifetime of **seconds** so that cart state remains relatively fresh while still benefiting from short‑term caching. | Verified — `cacheLife("seconds")` in `getCart` |
| NFR‑PERF‑3 | The system shall enable Next.js **Partial Prerendering** (`ppr: true`) and the `useCache` experimental flag, indicating an intent to mix static and dynamic rendering for performance. | Verified — `next.config.ts:2‑6` |
| NFR‑PERF‑4 | The system shall inline critical CSS in development/build to reduce render … *(the source analysis ends abruptly here; the statement is preserved as‑is)* | Verified – statement appears in source analysis |

---