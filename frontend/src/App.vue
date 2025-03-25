<template>
  <v-app>
    <v-main>
      <router-view />
    </v-main>
    <app-offline-banner v-if="!isOnline" />
  </v-app>
</template>

<script>
import { ref, onMounted } from 'vue'
import AppOfflineBanner from '@/components/common/AppOfflineBanner.vue'

export default {
  name: 'App',
  components: {
    AppOfflineBanner
  },
  setup() {
    const isOnline = ref(navigator.onLine)

    const updateOnlineStatus = () => {
      isOnline.value = navigator.onLine
    }

    onMounted(() => {
      window.addEventListener('online', updateOnlineStatus)
      window.addEventListener('offline', updateOnlineStatus)
    })

    return {
      isOnline
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

