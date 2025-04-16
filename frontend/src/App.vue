<template>
  <v-app>
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>

export default {
  name: 'App',
  components: {}
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

/* Styles globaux pour les boutons */
.v-btn {
  opacity: 1 !important;
}

.v-btn--icon {
  background-color: transparent !important;
}

.v-btn--icon .v-icon {
  color: inherit !important;
  opacity: 1 !important;
}

/* Style des boutons colorés */
.v-btn[color="#00346E"] {
  background-color: #00346E !important;
  color: white !important;
}

.v-btn[color="#F78C48"] {
  background-color: #F78C48 !important;
  color: white !important;
}

.v-btn--icon[color="#00346E"] {
  color: #00346E !important;
}

.v-btn--icon[color="#F78C48"] {
  color: #F78C48 !important;
}

/* Correction des overlays et underlays */
.v-btn__overlay,
.v-btn__underlay {
  opacity: 0 !important;
}
</style>

