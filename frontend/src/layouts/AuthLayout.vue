<template>
  <div class="auth-layout">
    <div class="auth-container">
      <router-view />
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuthLayout'
}
</script>

<style scoped>
.auth-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 16px;
}

.auth-container {
  width: 100%;
  max-width: 450px;
}
</style>

