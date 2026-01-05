// ZenRay Dashboard Configuration
// URLs are loaded from environment variables

export const config = {
  // API - use relative path for proxy, or direct URL if VITE_SERVER_URL is set
  apiUrl: import.meta.env.VITE_SERVER_URL || '/api',
  
  // Site
  siteName: "ZenRay",
  siteUrl: import.meta.env.VITE_SITE_URL || "https://zenray.live",
  
  // Links
  githubUrl: import.meta.env.VITE_GITHUB_URL || "https://github.com/DeepakSilaych/ZenRay",
  docsUrl: import.meta.env.VITE_DOCS_URL || "https://zenray.live/docs",
} as const;

