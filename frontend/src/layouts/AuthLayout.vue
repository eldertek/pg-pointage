<template>
  <div class="auth-layout">
    <div class="auth-container">
      <router-view />
    </div>
    <PwaInstall />
  </div>
</template>

<script>
import PwaInstall from '@/components/PwaInstall.vue'

export default {
  name: 'AuthLayout',
  components: {
    PwaInstall
  }
}
</script>

<style scoped>
.auth-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  height: 100vh; /* Force la hauteur exacte */
  background-color: #f5f5f5;
  padding: 16px;
  overflow: hidden; /* Empêche le scroll */
  position: fixed; /* Empêche le scroll sur mobile */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.auth-container {
  width: 100%;
  max-width: 450px;
  /* Suppression de margin-bottom car le PwaInstall est en position fixed */
}
</style>

