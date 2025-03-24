import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import { createPinia } from "pinia"
import "./registerServiceWorker"
import "vuetify/styles"
import * as components from "vuetify/components"
import * as directives from "vuetify/directives"
import { aliases, mdi } from "vuetify/iconsets/mdi"
import { createVuetify } from "vuetify"

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
          error: "#F78C48",
          warning: "#F78C48",
          info: "#00346E",
          success: "#F78C48",
          background: "#FFFFFF",
          surface: "#FFFFFF",
        },
      },
      dark: {
        colors: {
          primary: "#00346E",
          secondary: "#F78C48",
          error: "#F78C48",
          warning: "#F78C48",
          info: "#00346E",
          success: "#F78C48",
          background: "#FFFFFF",
          surface: "#FFFFFF",
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

app.mount("#app")

