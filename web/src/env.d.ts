/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_SITE_URL: string;
  readonly PUBLIC_DASHBOARD_URL: string;
  readonly PUBLIC_API_URL: string;
  readonly PUBLIC_GITHUB_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
