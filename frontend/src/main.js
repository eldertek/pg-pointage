import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import { createPinia } from "pinia"
import "./registerServiceWorker"
import "vuetify/styles"
import { createVuetify } from "vuetify"
import * as components from "vuetify/components"
import * as directives from "vuetify/directives"
import { aliases, mdi } from "vuetify/iconsets/mdi"

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
          primary: "#4CAF50",
          secondary: "#8BC34A",
          accent: "#03A9F4",
          error: "#F44336",
          warning: "#FF9800",
          info: "#2196F3",
          success: "#4CAF50",
        },
      },
      dark: {
        colors: {
          primary: "#4CAF50",
          secondary: "#8BC34A",
          accent: "#03A9F4",
          error: "#F44336",
          warning: "#FF9800",
          info: "#2196F3",
          success: "#4CAF50",
        },
      },
    },
  },
})

const pinia = createPinia()
const app = createApp(App)

app.use(router)
app.use(pinia)
app.use(vuetify)

app.mount("#app")

