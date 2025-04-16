<template>
  <v-banner v-if="isReallyOffline" color="warning" class="offline-banner">
    <v-banner-text>
      <v-icon class="mr-2">mdi-wifi-off</v-icon>
      Vous êtes actuellement hors ligne. Certaines fonctionnalités peuvent être limitées.
    </v-banner-text>
  </v-banner>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

export default {
  name: 'AppOfflineBanner',
  setup() {
    const isReallyOffline = ref(false)
    const pingInterval = ref(null)
    // Use the API service for connectivity check
    const lastCheckTime = ref(new Date().toISOString())
    const lastCheckResult = ref('Not checked yet')

    // Check if we can reach the server
    const checkServerConnection = async () => {
      console.log('[AppOfflineBanner] Starting connection check at', new Date().toLocaleTimeString())
      console.log('[AppOfflineBanner] Current navigator.onLine status:', navigator.onLine)
      console.log('[AppOfflineBanner] Current isReallyOffline value:', isReallyOffline.value)

      // Même si le navigateur indique que nous sommes hors ligne, essayons quand même
      // de contacter le serveur pour vérifier la connexion réelle
      if (!navigator.onLine) {
        console.log('[AppOfflineBanner] Browser reports offline, but we will check server anyway')
        // Ne pas retourner ici, continuer avec la vérification du serveur
      }

      // Try up to 3 times with a short delay between attempts
      let attempts = 0
      const maxAttempts = 3

      console.log('[AppOfflineBanner] Will try up to', maxAttempts, 'connection attempts')

      while (attempts < maxAttempts) {
        try {
          attempts++
          console.log(`[AppOfflineBanner] Connection attempt ${attempts}/${maxAttempts} using API service`)

          // Try to fetch from the server with a timeout
          const controller = new AbortController()
          const timeoutId = setTimeout(() => {
            console.log('[AppOfflineBanner] Request timeout after 5 seconds')
            controller.abort()
          }, 5000) // 5 second timeout

          console.log('[AppOfflineBanner] Sending API request...')
          const startTime = performance.now()

          // Use the API instance instead of direct fetch
          const response = await api.get('/users/profile/', {
            headers: { 'Accept': 'application/json' },
            signal: controller.signal
          })

          const endTime = performance.now()
          const requestTime = Math.round(endTime - startTime)

          clearTimeout(timeoutId)
          console.log(`[AppOfflineBanner] Received response in ${requestTime}ms with status:`, response.status)

          // If we get a successful response, we're online
          if (response.status >= 200 && response.status < 300) {
            if (isReallyOffline.value) {
              console.log('[AppOfflineBanner] Connection restored (200 OK)')
            }
            isReallyOffline.value = false
            lastCheckResult.value = `Online (200 OK) in ${requestTime}ms`
            lastCheckTime.value = new Date().toISOString()
            return // Success, exit the function
          }

          // If response is not OK but it's a 401 Unauthorized, we're still online
          // just not authenticated, which is fine for connectivity check
          if (response.status === 401 || response.status === 403) {
            if (isReallyOffline.value) {
              console.log('[AppOfflineBanner] Connection restored (401 response)')
            }
            isReallyOffline.value = false
            lastCheckResult.value = `Online (401 Unauthorized) in ${requestTime}ms`
            lastCheckTime.value = new Date().toISOString()
            return
          }

          console.log(`[AppOfflineBanner] Server returned unexpected status ${response.status}`)
          lastCheckResult.value = `Unexpected status: ${response.status}`

          // For other error status codes, increment attempts and try again
          if (attempts < maxAttempts) {
            console.log('[AppOfflineBanner] Will retry after 1 second delay')
            await new Promise(resolve => setTimeout(resolve, 1000))
          }

        } catch (error) {
          console.log(`[AppOfflineBanner] Connection check attempt ${attempts}/${maxAttempts} failed:`, error)
          // Handle Axios error format which is different from fetch
          const errorName = error.name || 'NetworkError'
          const errorMessage = error.message || 'Connection failed'
          lastCheckResult.value = `Error: ${errorName} - ${errorMessage}`

          // Wait a bit before retrying
          if (attempts < maxAttempts) {
            console.log('[AppOfflineBanner] Will retry after 1 second delay')
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        }
      }

      // If we've exhausted all attempts, we're offline
      if (!isReallyOffline.value) {
        console.log('[AppOfflineBanner] Connection lost after multiple failed attempts')
      }
      console.log('[AppOfflineBanner] Setting offline state after', maxAttempts, 'failed attempts')
      isReallyOffline.value = true
      lastCheckTime.value = new Date().toISOString()
    }

    // Handle online/offline events from the browser
    const handleOnline = () => {
      // When browser reports online, verify with server
      console.log('[AppOfflineBanner] Browser reported ONLINE event')
      checkServerConnection()
    }

    const handleOffline = () => {
      // When browser reports offline, we're definitely offline
      console.log('[AppOfflineBanner] Browser reported OFFLINE event')
      isReallyOffline.value = true
      lastCheckResult.value = 'Browser offline event'
      lastCheckTime.value = new Date().toISOString()
    }

    onMounted(() => {
      console.log('[AppOfflineBanner] Component mounted')
      console.log('[AppOfflineBanner] Initial navigator.onLine status:', navigator.onLine)

      // Initial check
      checkServerConnection()

      // Set up event listeners
      window.addEventListener('online', handleOnline)
      window.addEventListener('offline', handleOffline)

      // Periodically check connection (every 15 seconds)
      console.log('[AppOfflineBanner] Setting up periodic check every 15 seconds')
      pingInterval.value = setInterval(() => {
        console.log('[AppOfflineBanner] Running periodic connection check')
        checkServerConnection()
      }, 15000)

      // Log initial connection status
      console.log('[AppOfflineBanner] Initialized connection monitoring')
    })

    onUnmounted(() => {
      // Clean up event listeners and interval
      console.log('[AppOfflineBanner] Component unmounting, cleaning up resources')
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)

      if (pingInterval.value) {
        clearInterval(pingInterval.value)
        console.log('[AppOfflineBanner] Cleared ping interval')
      }
    })

    return {
      isReallyOffline,
      lastCheckTime,
      lastCheckResult
    }
  }
}
</script>

<style scoped>
.offline-banner {
  position: fixed;
  bottom: 0;
  width: 100%;
  z-index: 1000;
}
</style>

