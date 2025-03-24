<template>
  <v-banner color="warning" class="offline-banner">
    <v-banner-text>
      Vous êtes actuellement hors ligne. Certaines fonctionnalités peuvent être limitées.
    </v-banner-text>
  </v-banner>
</template>

<script>
export default {
  name: 'AppOfflineBanner'
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

