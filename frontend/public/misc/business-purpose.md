# Business Purpose

## Overview

Next.js Commerce is a headless Shopify storefront application that provides a high-performance, server-rendered interface for online retail. The software enables businesses to display products, manage shopping carts, and direct customers to checkout through Shopify's commerce infrastructure.

## Problem Statement

Online retailers using Shopify as their commerce backend require customizable storefronts that offer better performance, SEO optimization, and developer control than Shopify's native theme system provided. This application solves that problem by implementing a Next.js-based frontend that communicates with Shopify exclusively through its Storefront API, separating the presentation layer from the commerce engine.

## Target Users

### Primary Users

**Online Shoppers**: End customers who browse products, view details, add items to cart, and proceed to checkout. The interface is designed for consumer-facing retail interactions with emphasis on visual product presentation and streamlined purchasing flow.

### Secondary Users

**Ecommerce Operators**: Businesses running Shopify stores who need a modern, performant storefront. These operators manage their product catalog, pricing, inventory, and order processing through Shopify's admin interface while relying on this application for customer-facing presentation.

**Frontend Developers**: Developers who deploy and customize this template for specific Shopify stores. The codebase supports swapping the Shopify integration with alternative commerce providers while maintaining the same presentation layer.

## Core Domain Entities

The application models several interconnected retail concepts:

**Product**: The central entity representing items available for purchase. Products contain titles, descriptions, images, pricing information, and configurable options (such as size or color) that generate product variants.

**Collection**: Logical groupings of products organized for browsing. Collections enable category-based navigation and product filtering, supporting sorting by relevance, trending status, creation date, and price.

**Cart**: A session-persistent shopping basket that tracks selected items, quantities, selected variant options, and calculated totals. The cart maintains state across page navigations and synchronizes with Shopify's cart API.

**Page**: Static content pages managed through Shopify's CMS, rendered as standalone routes for policy pages, about sections, or other informational content.

**Menu**: Navigation structures defining header links to collections and pages, dynamically sourced from Shopify's menu configuration.

## Principal Workflows

### Product Discovery and Browsing

Customers arrive at the storefront and encounter a featured products grid on the homepage. From here, they navigate through collection pages organized by category. Each collection page displays products with filtering and sorting capabilities, allowing customers to order by relevance, popularity, newest arrivals, or price range.

The browsing experience relies on server-side rendering with Next.js React Server Components, enabling fast initial page loads and search engine indexing of product content. Collections and products are cached with configurable expiration, and the application responds to Shopify webhooks to invalidate cached data when store content changes.

### Product Detail Exploration

When a customer selects a product, they reach a dedicated product page displaying multiple images, variant selectors, pricing, and product descriptions. The variant selector allows selection of product options (such as size and color), dynamically updating available options based on Shopify's inventory data. Related product recommendations appear at the bottom of the page.

### Shopping Cart Management

Customers add products to their cart with immediate visual feedback. The cart persists across sessions through browser cookies containing the Shopify cart identifier. Customers can view their cart in a slide-out modal, adjust item quantities, remove items, and proceed to checkout. The checkout process delegates to Shopify's hosted checkout flow, where payment processing and order fulfillment occur.

Cart state management employs React optimistic updates, providing responsive UI feedback while synchronizing with Shopify's cart API. Server Actions handle cart mutations, ensuring secure communication with the commerce backend.

### Static Content Delivery

The application serves Shopify-managed CMS pages as standalone routes, supporting policy pages, informational content, and other static text content that integrates with the storefront's visual design.

## Business Outcomes

The application delivers several outcomes for its users:

**Performance**: Server-rendered product pages and collections provide fast load times and strong SEO characteristics. Next.js caching mechanisms reduce backend load and improve response times for repeat visitors.

**Customizability**: The separation of frontend and commerce backend allows retailers to implement custom designs and interactions without modifying Shopify's core platform. Developers can swap the commerce provider entirely while maintaining the same presentation layer.

**Scalability**: Deployed on Vercel's edge infrastructure, the storefront scales automatically to handle traffic spikes without infrastructure management overhead.

**Checkout Integration**: By delegating checkout to Shopify, the application leverages Shopify's mature payment processing, fraud detection, shipping calculation, and order management capabilities without reimplementing sensitive commerce operations.

## Implementation Evidence

The business purpose is established through several concrete implementation artifacts:

| Evidence | Location | Purpose |
|----------|----------|---------|
| GraphQL Integration | `lib/shopify/index.ts` | Comprehensive Shopify Storefront API client handling cart operations, product queries, collection retrieval, and page fetching. All commerce operations flow through this integration layer. |
| Domain Models | `lib/shopify/types.ts` | Type definitions for Cart, Product, ProductVariant, Collection, Menu, and Page establishing the core retail entities. |
| Cart Persistence | `components/cart/cart-context.tsx` | Cart state management with cookie-based cart identifiers demonstrating session-persistent shopping functionality. |
| Checkout Delegation | `components/cart/actions.ts` | The `redirectToCheckout` function delegates to Shopify's hosted checkout, confirming payment processing occurs on Shopify's infrastructure. |
| Revalidation Webhooks | `app/api/revalidate/route.ts` | The revalidation endpoint responds to Shopify product and collection update webhooks, keeping cached content synchronized with the commerce backend. |
| Environment Configuration | `.env.example` | Required variables for `SHOPIFY_STORE_DOMAIN`, `SHOPIFY_STOREFRONT_ACCESS_TOKEN`, and `SHOPIFY_REVALIDATION_SECRET` document the Shopify integration requirements. |

## Multi-Provider Architecture

The README explicitly identifies this repository as one of several provider implementations, with Shopify receiving active maintenance. Alternative providers documented include BigCommerce, Ecwid, Geins, Medusa, Saleor, Shopware, Swell, and others. This architecture confirms that the application is designed as a provider-agnostic ecommerce frontend template, with Shopify as the primary maintained implementation.

## Documented Limitations

**Checkout Not Implemented**: The application does not implement its own checkout flow. All payment processing, shipping calculation, tax calculation, and order management delegates to Shopify's hosted checkout experience. Customers leave the application to complete purchases.

**Commerce Provider Required**: The application requires a configured Shopify store with Storefront API access. Without the Shopify backend, the application displays empty collections and non-functional cart operations.

**No Inventory Management**: The application reads but does not write product catalog data. All inventory, pricing, and product information management occurs in Shopify's admin interface.

**No Order Management**: Customer order history, tracking, and returns are handled entirely by Shopify. The storefront has no order management interface.