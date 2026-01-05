// ZenRay Web Configuration
// URLs are loaded from environment variables at build time

export const config = {
  // Site
  siteName: "ZenRay",
  siteUrl: import.meta.env.PUBLIC_SITE_URL || "https://zenray.live",
  siteDescription: "Observability for ML/LLM pipelines. Debug candidate drop-off, track decision context, and understand why your pipeline behaves the way it does.",
  siteTagline: "Debug ML pipelines with clarity",
  
  // SEO
  seo: {
    title: "ZenRay - Observability for ML/LLM Pipelines",
    description: "Debug candidate drop-off, track decision context, and understand why your ML pipeline behaves the way it does. Minimal code changes, maximum visibility.",
    keywords: [
      "ML observability",
      "LLM debugging",
      "RAG pipeline",
      "machine learning",
      "AI debugging",
      "candidate tracking",
      "pipeline tracing",
      "ML monitoring",
    ],
    ogImage: "/og-image.svg",
    twitterHandle: "@zenray_dev",
  },
  
  // Links - loaded from env
  githubUrl: import.meta.env.PUBLIC_GITHUB_URL || "https://github.com/DeepakSilaych/ZenRay",
  dashboardUrl: import.meta.env.PUBLIC_DASHBOARD_URL || "http://localhost:4002",
  docsUrl: "/docs",
  
  // API
  apiUrl: import.meta.env.PUBLIC_API_URL || "http://localhost:4003",
} as const;
