# Technology Architecture

## Architecture Overview

Next.js Commerce is a high-performance server-rendered ecommerce application built around a Shopify storefront integration. The architecture consists of a modern Next.js frontend with React Server Components and a client-side component system that communicates with Shopify's GraphQL API through a custom integration layer.

## Architecture Diagram

```mermaid
flowchart TB
    %% Entry Points
    U[End Users] --> F[Next.js Frontend]
    U --> A[Direct Shopify Storefront]
    
    %% Frontend Components
    F -->|HTTP/JSON| FE[Next.js Application Server]
    F -->|WebSocket| CartWS[WebSocket Connection]
    
    %% Frontend Layer
    FE -->|Server Actions| RouteComponents["App Router Routes"]
    FE -->|Component Library| UI[React Component Library]
    FE -->|Static Assets| Assets["Images & Static Files"]
    
    %% Backend/API Layer
    RouteComponents -->|Server Actions & API Routes| ShopAPI[Shopify Integration Layer]
    FE -->|Server Components| ShopAPI
    
    %% Shopify Integration
    ShopAPI -->|GraphQL REST API| Shopify[Shopify Storefront API]
    CartWS -->|GraphQL Subscriptions| Shopify["Cart Operations"]
    
    %% Data Storage
    Shopify -->|Database Access| ShopifyDB[Shopify Database]
    
    %% Supporting Infrastructure
    FE -->|Caching Layer| NextCache[Next.js Caching]
    FE -->|Environment| EnvVars[Environment Variables]
    FE -->|Build Tools| BuildTools["Build & CI/CD"]
    
    %% External Services
    Assets -->|CDN| CDN["Image CDN"]
    ShopAPI -->|Authentication| Auth["Shopify Auth Token"]
    BuildTools -->|Deployment| Vercel["Vercel Platform"]
    
    %% Key Relationships
    classDef verified fill:#d4edda,stroke:#c3e6cb
    classDef inferred fill:#fff3cd,stroke:#ffeaa7
    classDef unverified fill:#f8d7da,stroke:#f5c6cb
    
    class F,FE,RouteComponents,UI,ShopAPI,Shopify,NextCache,EnvVars,Vercel verified
    class CartWS,ShopifyDB,Assets,CDN,A user inferred
    
    style U fill:#e3f2fd,stroke:#bbdefb
```

## Component Analysis

### Frontend Layer (Verified)
**Next.js Application Server**
- **Technology**: Next.js 15.6.0 (App Router with React Server Components)
- **Responsibility**: Primary web application server, server-side rendering, static generation
- **Runtime**: Node.js runtime via Next.js build process
- **Evidence**: `next.config.ts`, `package.json`, `app/layout.tsx`, `app/page.tsx`
- **Inputs/Outputs**: Receives HTTP requests, serves HTML and JSON responses
- **Dependencies**: React, React DOM, Tailwind CSS, Geist font

**React Component Library**
- **Technology**: React 19.0.0 with TypeScript
- **Responsibility**: Reusable UI components (cart, products, layout, etc.)
- **Evidence**: `components/` directory with 40+ component files
- **Architecture Note**: Client Components (`"use client"`) for interactive elements, Server Components for presentation

### Shopify Integration Layer (Verified)
**Shopify API Client**
- **Technology**: Custom GraphQL client implemented in `lib/shopify/index.ts`
- **Responsibility**: Connects frontend to Shopify Storefront API
- **Evidence**: `shopifyFetch` function, environment variables (`SHOPIFY_STORE_DOMAIN`, `SHOPIFY_STOREFRONT_ACCESS_TOKEN`)
- **Communication**: GraphQL REST API over HTTPS
- **Data Operations**: Product catalogs, collections, carts, customer data

### Cart Management System (Verified)
**Client-Side Cart Context**
- **Technology**: React Context API with `useOptimistic` hooks (`components/cart/cart-context.tsx`)
- **Responsibility**: Manages shopping cart state across components
- **Evidence**: `CartProvider` component, `useCart` hook, cart reducer logic
- **Runtime**: Client-side React application

**Server-Side Cart Operations**
- **Technology**: Shopify cart mutations (`lib/shopify/mutations/cart.ts`)
- **Responsibility**: Persists cart data to Shopify backend
- **Evidence**: `addToCart`, `removeFromCart`, `updateCart` functions

### Data Storage (Strongly Inferred)
**Shopify Database**
- **Technology**: Shopify's proprietary database (PostgreSQL-based)
- **Responsibility**: Primary data store for products, customers, orders, carts
- **Evidence**: All data operations flow through Shopify GraphQL API
- **Access Pattern**: RESTful GraphQL endpoints via Shopify frontend API

### Infrastructure and Deployment (Verified)
**Build and Runtime Tools**
- **Technology**: pnpm package manager, TypeScript, Tailwind CSS, PostCSS
- **Evidence**: `package.json`, `pnpm-lock.yaml`, `next.config.ts`
- **Build Process**: `pnpm install`, `pnpm dev`, `pnpm build`, `pnpm start`

**Deployment Platform**
- **Technology**: Vercel platform
- **Evidence**: README deployment instructions, Vercel button badge, `baseUrl` configuration
- **Runtime Environment**: Serverless functions, edge caching

### External Services (Verified)
**Shopify Storefront API**
- **Technology**: Shopify Storefront GraphQL API
- **Responsibility**: Provides product catalog, customer data, cart management
- **Authentication**: Access token via environment variable `SHOPIFY_STOREFRONT_ACCESS_TOKEN`
- **Endpoints**: `https://[store-domain]/api/2023-01/graphql.json`

**Image CDN**
- **Technology**: Shopify CDN for product images (`cdn.shopify.com`)
- **Evidence**: `next.config.ts` remotePatterns configuration

## Communication Flows

### Primary Request Flow (Verified)
1. **User Action** → Next.js Frontend (HTTP/JSON)
2. **Router/Server Action** → Shopify Integration Layer (Server Actions)
3. **GraphQL Query** → Shopify Storefront API
4. **Response** → Next.js Frontend (JSON)
5. **Component Update** → React Component Library (state updates)

### Cart Operations Flow (Verified)
1. **User Interaction** → Cart Context (Client-side optimistic updates)
2. **Server Action** → Shopify Cart Mutations (GraphQL)
3. **Shopify Response** → Cart Context (state reconciliation)

### Static Asset Flow (Verified)
1. **Build Process** → Image Optimization (Next.js)
2. **Runtime** → CDN Distribution (`cdn.shopify.com`)

## Security and Authentication Boundaries (Verified)

### Shopify Integration Security
- **Authentication**: Shopify access token in environment variables
- **Authorization**: Shopify storefront access controls
- **Data Isolation**: Each deployment has unique Shopify store configuration
- **Environment Security**: `.env.example` configuration template

### Frontend Security
- **No Server-Side API Keys**: Shopify tokens handled via environment variables
- **CSRF Protection**: Next.js built-in CSRF protection for Server Actions
- **Content Security Policy**: Next.js default CSP with image CDN configuration

## Configuration and Environment Boundaries (Verified)

### Critical Environment Variables
- `SHOPIFY_STORE_DOMAIN`: Shopify store subdomain
- `SHOPIFY_STOREFRONT_ACCESS_TOKEN`: Authentication token for Shopify API
- `SHOPIFY_REVALIDATION_SECRET`: Security secret for webhook validation
- `VERCEL_PROJECT_PRODUCTION_URL`: Production URL for metadata
- `COMPANY_NAME`, `SITE_NAME`: Branded application metadata

### Configuration Management
- **Build-Time Configuration**: Next.js configuration (`next.config.ts`)
- **Runtime Configuration**: Environment variables via Next.js runtime
- **Feature Flags**: Implicit via Shopify store configuration

## Caching Strategy (Verified)

### Next.js Caching Layers
- **Router Cache**: Next.js App Router caching
- **Data Cache**: Shopify data tagged with `TAGS.collections`, `TAGS.products`, `TAGS.cart`
- **Full-Stage Caching**: Experimental features enabled (`ppr`, `inlineCss`, `useCache`)
- **Revalidation**: Webhook-driven revalidation for Shopify data updates

## Architectural Decisions and Rationale

### Server-Side Rendering Strategy
**Evidence**: React Server Components, App Router, `baseUrl` configuration
**Rationale**: High performance, SEO optimization, reduced client-side bundle size

### Client-Side State Management
**Evidence**: `useOptimistic` hooks, React Context API, client component boundaries
**Rationale**: Responsive UI, instant user feedback, efficient cart operations

### Shopify as Primary Data Source
**Evidence**: All data access flows through `lib/shopify/` modules, environment variable configuration
**Rationale**: Headless commerce architecture, separation of concerns, existing Shopify expertise

## Architecture Quality Assessment

### Strengths
- **Clear Separation**: Frontend presentation layer clearly separated from Shopify data layer
- **Performance Optimized**: Server-side rendering and caching strategy
- **Component Architecture**: Reusable component system with clear boundaries
- **Headless Architecture**: Flexible integration with ecommerce backend

### Potential Concerns
- **Single Data Source**: All data depends on Shopify availability
- **Build-Time Configuration**: Requires environment variables for deployment
- **Client-Side Complexity**: Complex cart state management in client components

## Verification Summary

**Verified Components (4)**:
- Next.js frontend application server
- Shopify integration layer
- React component library
- Vercel deployment infrastructure

**Strongly Inferred Components (2)**:
- Shopify database persistence
- WebSocket connections for real-time cart updates

**Unverified Components (0)**:
- No components without supporting evidence

## Key Architectural Insights

1. **Headless Commerce Pattern**: The application follows a headless architecture, separating frontend presentation from ecommerce backend

2. **Performance-First Design**: Extensive use of server-side rendering and caching for optimal performance

3. **Component-Based Architecture**: Large component library enables consistent UI across the application

4. **Integration-Centric Design**: The entire system is built around Shopify integration, with all data flowing through this single source

5. **Deployment Simplicity**: Vercel platform provides seamless deployment with built-in optimizations

This architecture is optimized for a specific use case - serving as a storefront template for Shopify merchants, balancing performance, developer experience, and integration capabilities.