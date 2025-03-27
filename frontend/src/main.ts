import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import { Toast, options } from './plugins/toast'
import './assets/styles/toast.css'
import './styles/global.css'

const app = createApp(App)

app.use(router)
app.use(vuetify)
app.use(Toast, options)

app.mount('#app') 