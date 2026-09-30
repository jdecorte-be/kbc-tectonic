// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui'
  ],

  devtools: {
    enabled: true
  },

  colorMode: {
    preference: 'dark',
    fallback: 'dark'
  },

  css: ['~/assets/css/main.css'],

  components: [{ path: '~/components', extensions: ['vue'] }],

  runtimeConfig: {
    apiBase: 'http://127.0.0.1:8000'
  },

  compatibilityDate: '2026-06-30',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})
