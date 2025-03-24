/* eslint-disable no-console */

import { register } from "register-service-worker"

if (import.meta.env.PROD) {
  register(`${import.meta.env.BASE_URL}service-worker.js`, {
    ready() {
      console.log(
        "App is being served from cache by a service worker.\n" + "For more details, visit https://goo.gl/AFskqB",
      )
    },
    registered(registration) {
      console.log("Service worker has been registered.")
    },
    cached(registration) {
      console.log("Content has been cached for offline use.")
    },
    updatefound(registration) {
      console.log("New content is downloading.")
    },
    updated(registration) {
      console.log("New content is available; please refresh.")
      // Émettre un événement pour notifier l'application qu'une mise à jour est disponible
      document.dispatchEvent(new CustomEvent('swUpdated', { detail: registration }))
    },
    offline() {
      console.log("No internet connection found. App is running in offline mode.")
    },
    error(error) {
      console.error("Error during service worker registration:", error)
    },
  })
}

