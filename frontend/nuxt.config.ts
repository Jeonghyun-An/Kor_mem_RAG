import { defineNuxtConfig } from "nuxt/config";

export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: ["@nuxtjs/tailwindcss"],

  typescript: {
    strict: false,
    typeCheck: false,
    shim: false,
    tsConfig: {
      compilerOptions: { strict: false, skipLibCheck: true },
    },
  },

  imports: { autoImport: true },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8001/api",
    },
  },

  app: {
    head: {
      title: "코리안메모리 AI 검색",
      htmlAttrs: { lang: "ko" },
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
      ],
      link: [
        {
          rel: "preconnect",
          href: "https://cdn.jsdelivr.net",
        },
        {
          rel: "stylesheet",
          href: "https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css",
        },
      ],
    },
  },

  // Library_AI_land와 동일한 CSS 로드 순서
  css: [
    "~/assets/css/reset.css",
    "~/assets/css/common.css",
    "~/assets/css/layout.css",
    "~/assets/css/main.css",
  ],

  compatibilityDate: "2026-01-21",

  vite: {
    server: {
      hmr: { clientPort: 3000 },
    },
  },
});
