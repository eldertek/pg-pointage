import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import 'vuetify/styles'

export default createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#00346E',
          secondary: '#F78C48',
          background: '#FFFFFF',
          surface: '#FFFFFF',
          'on-primary': '#FFFFFF',
          'on-secondary': '#FFFFFF',
          'on-background': '#00346E',
          'on-surface': '#00346E',
          error: '#F78C48',
          info: '#00346E',
          success: '#00346E',
          warning: '#F78C48',
        },
      },
    },
  },
  defaults: {
    VBtn: {
      color: 'primary',
      variant: 'flat',
      style: 'opacity: 1 !important;',
    },
    VIcon: {
      color: 'primary',
      style: 'opacity: 1 !important;',
    },
  },
}) 