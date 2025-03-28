<template>
  <div class="d-flex align-center address-container">
    <span class="address-text">{{ address }}</span>
    <v-icon
      v-if="address"
      class="map-icon"
      color="primary"
      size="small"
      @click.stop="openGoogleMaps"
    >
      mdi-map-marker
    </v-icon>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  address?: string
  postalCode?: string
  city?: string
  country?: string
}>()

const fullAddress = computed(() => {
  const parts = [
    props.address,
    props.postalCode,
    props.city,
    props.country
  ].filter(Boolean)
  return parts.join(', ')
})

const openGoogleMaps = () => {
  if (fullAddress.value) {
    const encodedAddress = encodeURIComponent(fullAddress.value)
    window.open(`https://www.google.com/maps/search/?api=1&query=${encodedAddress}`, '_blank')
  }
}
</script>

<style scoped>
.address-container {
  min-height: 24px;
  padding: 4px 0;
}

.address-text {
  margin-right: 4px;
}

.map-icon {
  cursor: pointer;
  transition: all 0.2s ease;
  opacity: 1 !important;
  color: #00346E !important;
  font-size: 18px !important;
}

.map-icon:hover {
  opacity: 0.8 !important;
  transform: scale(1.1);
}

/* Styles spécifiques pour le tableau */
:deep(.v-data-table) .map-icon {
  margin-left: 4px;
  background-color: transparent !important;
}

:deep(.v-data-table) .address-container {
  padding: 0;
}
</style> 