<template>
  <div class="offline-banner">
    <v-alert
      type="warning"
      variant="tonal"
      icon="mdi-wifi-off"
      prominent
      closable
    >
      Vous êtes actuellement hors ligne. Vos pointages seront synchronisés lorsque vous serez de nouveau connecté.
    </v-alert>
  </div>
</template>

<script>
export default {
  name: 'AppOfflineBanner'
}
</script>

<style scoped>
.offline-banner {
  position: fixed;
  bottom: 56px;
  left: 0;
  right: 0;
  z-index: 100;
}
</style>

