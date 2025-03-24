<template>
  <v-snackbar
    v-model="show"
    :timeout="-1"
    color="info"
    location="bottom"
  >
    Une nouvelle version est disponible.
    
    <template v-slot:actions>
      <v-btn
        color="white"
        variant="text"
        @click="update"
      >
        Mettre à jour
      </v-btn>
      <v-btn
        color="white"
        variant="text"
        @click="show = false"
      >
        Plus tard
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'AppUpdateNotification',
  emits: ['update'],
  setup(props, { emit }) {
    const show = ref(true)

    const update = () => {
      show.value = false
      emit('update')
    }

    return {
      show,
      update
    }
  }
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

