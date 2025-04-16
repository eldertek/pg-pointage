import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import { createPinia } from "pinia"
import "vuetify/styles"
import * as components from "vuetify/components"
import * as directives from "vuetify/directives"
import { aliases, mdi } from "vuetify/iconsets/mdi"
import { createVuetify } from "vuetify"
import i18n from "./plugins/i18n"

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: "mdi",
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: "light",
    themes: {
      light: {
        colors: {
          primary: "#00346E",
          secondary: "#F78C48",
          background: "#FFFFFF",
          surface: "#FFFFFF",
          "on-primary": "#FFFFFF",
          "on-secondary": "#FFFFFF",
          "on-background": "#00346E",
          "on-surface": "#00346E",
          error: "#F78C48",
          info: "#00346E",
          success: "#00346E",
          warning: "#F78C48",
        },
      },
      dark: {
        colors: {
          primary: "#00346E",
          secondary: "#F78C48",
          background: "#121212",
          surface: "#121212",
          "on-primary": "#FFFFFF",
          "on-secondary": "#FFFFFF",
          "on-background": "#FFFFFF",
          "on-surface": "#FFFFFF",
          error: "#F78C48",
          info: "#00346E",
          success: "#00346E",
          warning: "#F78C48",
        },
      },
    },
  },
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(vuetify)
app.use(i18n)

app.mount("#app")

