# ZenRay Website

Landing page and documentation site built with Astro.

---

## Overview

The website includes:

- **Landing Page** — Product overview with features and use cases
- **Documentation** — SDK guides, API reference, and examples
- **Responsive Design** — Mobile-friendly with glassmorphism UI

Built with:

- [Astro](https://astro.build) — Static site generator
- [Tailwind CSS](https://tailwindcss.com) — Utility-first styling
- [TypeScript](https://typescriptlang.org) — Type safety

---

## Prerequisites

- Node.js 18+ or Bun

---

## Setup

### Install Dependencies

```bash
cd web
npm install
# or
bun install
```

### Run Development Server

```bash
npm run dev
# or
bun run dev
```

Site will be available at `http://localhost:4000`

---

## Build for Production

```bash
npm run build
```

Output is in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

---

## Project Structure

```
web/
├── src/
│   ├── components/
│   │   ├── Nav.astro       # Navigation bar
│   │   └── Footer.astro    # Site footer
│   ├── layouts/
│   │   ├── Layout.astro    # Base layout
│   │   └── DocsLayout.astro # Documentation layout
│   ├── pages/
│   │   ├── index.astro     # Landing page
│   │   └── docs/
│   │       ├── index.astro # Docs home
│   │       ├── sdk.astro   # SDK documentation
│   │       ├── api.astro   # API reference
│   │       └── examples.astro # Example pipelines
│   └── config.ts           # Site configuration
├── tailwind.config.mjs
├── astro.config.mjs
└── package.json
```

---

## Configuration

Edit `src/config.ts` to update site-wide settings:

```typescript
export const config = {
  siteName: "ZenRay",
  siteDescription: "The observability layer for ML pipelines",
  githubUrl: "https://github.com/your-org/zenray",
  dashboardUrl: "https://app.zenray.dev",
  apiUrl: "https://api.zenray.dev",
};
```

---

## Styling

The site uses a custom design system:

- **Colors** — Navy backgrounds with cyan accents
- **Typography** — Inter for body, JetBrains Mono for code
- **Effects** — Glassmorphism, grid backgrounds, subtle animations

Key Tailwind extensions in `tailwind.config.mjs`:

```javascript
colors: {
  navy: { 950: '#09090b', 900: '#18181b' },
  accent: { DEFAULT: '#22d3ee' },
}
```

---

## Adding Documentation

1. Create a new `.astro` file in `src/pages/docs/`
2. Use the `DocsLayout` component
3. Add to the sidebar in `DocsLayout.astro`

Example:

```astro
---
import DocsLayout from "../../layouts/DocsLayout.astro";
---

<DocsLayout 
  title="New Page" 
  description="Page description"
  currentPage="new-page"
>
  <h1>New Page</h1>
  <p>Content goes here...</p>
</DocsLayout>
```

---

## Development

### Format Code

```bash
npm run format
```

### Type Check

```bash
npm run check
```

