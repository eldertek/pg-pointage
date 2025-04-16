import { createI18n } from 'vue-i18n'

// Import locale messages
import fr from '@/locales/fr.json'
import en from '@/locales/en.json'

// Get the user's preferred language from localStorage or use French as default
const getLocale = () => {
  const storedLocale = localStorage.getItem('language')
  if (storedLocale && ['fr', 'en'].includes(storedLocale)) {
    return storedLocale
  }
  
  // Check browser language
  const browserLocale = navigator.language.split('-')[0]
  if (['fr', 'en'].includes(browserLocale)) {
    return browserLocale
  }
  
  // Default to French
  return 'fr'
}

// Create i18n instance
const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: getLocale(),
  fallbackLocale: 'fr',
  messages: {
    fr,
    en
  },
  // Enable HTML in translations
  warnHtmlInMessage: 'off',
  // Disable warnings for missing translations in development
  silentTranslationWarn: process.env.NODE_ENV === 'production',
  // Disable fallback warnings
  silentFallbackWarn: true
})

export default i18n
