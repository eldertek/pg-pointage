<template>
  <div class="update-notification">
    <v-alert
      type="info"
      variant="tonal"
      icon="mdi-update"
      prominent
    >
      Une nouvelle version est disponible.
      <v-btn
        color="primary"
        variant="text"
        @click="$emit('update')"
        class="ml-2"
      >
        Mettre à jour
      </v-btn>
    </v-alert>
  </div>
</template>

<script>
export default {
  name: 'AppUpdateNotification',
  emits: ['update']
}
</script>

<style scoped>
.update-notification {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}
</style>

