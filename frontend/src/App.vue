<template>
  <v-app>
    <v-main>
      <router-view />
    </v-main>
    <app-offline-banner v-if="!isOnline" />
    <app-update-notification v-if="updateAvailable" @update="updateApp" />
  </v-app>
</template>

<script>
import { ref, onMounted } from 'vue'
import AppOfflineBanner from '@/components/common/AppOfflineBanner.vue'
import AppUpdateNotification from '@/components/common/AppUpdateNotification.vue'

export default {
  name: 'App',
  components: {
    AppOfflineBanner,
    AppUpdateNotification
  },
  setup() {
    const isOnline = ref(navigator.onLine)
    const updateAvailable = ref(false)

    const updateOnlineStatus = () => {
      isOnline.value = navigator.onLine
    }

    const updateApp = () => {
      window.location.reload()
    }

    onMounted(() => {
      window.addEventListener('online', updateOnlineStatus)
      window.addEventListener('offline', updateOnlineStatus)

      // Écouter les événements du service worker
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          updateAvailable.value = true
        })
      }
    })

    return {
      isOnline,
      updateAvailable,
      updateApp
    }
  }
}
</script>

<style>
/* Styles globaux */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Roboto', sans-serif;
}

.v-application {
  font-family: 'Roboto', sans-serif;
}
</style>

