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

export default {
  name: 'AppOfflineBanner',
  setup() {
    const isReallyOffline = ref(false)
    const pingInterval = ref(null)
    const pingUrl = '/api/v1/users/profile/' // Use an existing endpoint for connectivity check

    // Check if we can reach the server
    const checkServerConnection = async () => {
      if (!navigator.onLine) {
        // If browser reports offline, we're definitely offline
        isReallyOffline.value = true
        return
      }

      // Try up to 3 times with a short delay between attempts
      let attempts = 0
      const maxAttempts = 3

      while (attempts < maxAttempts) {
        try {
          // Try to fetch from the server with a timeout
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout

          const response = await fetch(pingUrl, {
            method: 'HEAD', // Just check headers, don't need body
            cache: 'no-store', // Don't use cache
            signal: controller.signal,
            // Include credentials to handle authenticated endpoints
            credentials: 'include'
          })

          clearTimeout(timeoutId)

          // If we get a successful response, we're online
          if (response.ok) {
            if (isReallyOffline.value) {
              console.log('[AppOfflineBanner] Connection restored')
            }
            isReallyOffline.value = false
            return // Success, exit the function
          }

          // If response is not OK but it's a 401 Unauthorized, we're still online
          // just not authenticated, which is fine for connectivity check
          if (response.status === 401) {
            if (isReallyOffline.value) {
              console.log('[AppOfflineBanner] Connection restored (401 response)')
            }
            isReallyOffline.value = false
            return
          }

          console.log(`[AppOfflineBanner] Server returned status ${response.status}`)

          // For other error status codes, increment attempts and try again
          attempts++

        } catch (error) {
          console.log(`Connection check attempt ${attempts + 1}/${maxAttempts} failed:`, error.message)
          attempts++

          // Wait a bit before retrying
          if (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        }
      }

      // If we've exhausted all attempts, we're offline
      if (!isReallyOffline.value) {
        console.log('[AppOfflineBanner] Connection lost after multiple failed attempts')
      }
      isReallyOffline.value = true
    }

    // Handle online/offline events from the browser
    const handleOnline = () => {
      // When browser reports online, verify with server
      checkServerConnection()
    }

    const handleOffline = () => {
      // When browser reports offline, we're definitely offline
      console.log('[AppOfflineBanner] Browser reported offline')
      isReallyOffline.value = true
    }

    onMounted(() => {
      // Initial check
      checkServerConnection()

      // Set up event listeners
      window.addEventListener('online', handleOnline)
      window.addEventListener('offline', handleOffline)

      // Periodically check connection (every 15 seconds)
      pingInterval.value = setInterval(checkServerConnection, 15000)

      // Log initial connection status
      console.log('[AppOfflineBanner] Initialized connection monitoring')
    })

    onUnmounted(() => {
      // Clean up event listeners and interval
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)

      if (pingInterval.value) {
        clearInterval(pingInterval.value)
      }
    })

    return {
      isReallyOffline
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

