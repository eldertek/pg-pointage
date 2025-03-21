/* eslint-disable no-console */

import { register } from "register-service-worker"

if (process.env.NODE_ENV === "production") {
  register(`${process.env.BASE_URL}service-worker.js`, {
    ready() {
      console.log(
        "App is being served from cache by a service worker.\n" + "For more details, visit https://goo.gl/AFskqB",
      )
    },
    registered() {
      console.log("Service worker has been registered.")
    },
    cached() {
      console.log("Content has been cached for offline use.")
    },
    updatefound() {
      console.log("New content is downloading.")
    },
    updated() {
      console.log("New content is available; please refresh.")
      // Afficher une notification pour informer l'utilisateur qu'une mise à jour est disponible
      const notification = document.createElement("div")
      notification.className = "update-notification"
      notification.innerHTML = `
        <div class="update-notification-content">
          <p>Une nouvelle version est disponible !</p>
          <button id="update-button">Mettre à jour</button>
        </div>
      `
      document.body.appendChild(notification)

      document.getElementById("update-button").addEventListener("click", () => {
        window.location.reload()
      })
    },
    offline() {
      console.log("No internet connection found. App is running in offline mode.")
    },
    error(error) {
      console.error("Error during service worker registration:", error)
    },
  })
}

