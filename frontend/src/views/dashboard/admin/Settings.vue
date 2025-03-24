<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Paramètres Système</h1>
    </div>

    <v-card>
      <v-card-title>Configuration Générale</v-card-title>
      <v-card-text>
        <v-form>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="settings.appName"
                label="Nom de l'Application"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="settings.defaultLanguage"
                :items="languages"
                label="Langue par Défaut"
                variant="outlined"
                density="comfortable"
              ></v-select>
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="settings.maintenanceMessage"
                label="Message de Maintenance"
                variant="outlined"
                density="comfortable"
                rows="3"
              ></v-textarea>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          :loading="saving"
          @click="saveSettings"
        >
          Enregistrer
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
import { ref } from 'vue'
import api from '@/services/api'

export default {
  name: 'AdminSettings',
  setup() {
    const saving = ref(false)
    const settings = ref({
      appName: 'PG Pointage',
      defaultLanguage: 'fr',
      maintenanceMessage: ''
    })

    const languages = [
      { title: 'Français', value: 'fr' },
      { title: 'English', value: 'en' }
    ]

    const saveSettings = async () => {
      saving.value = true
      try {
        await api.post('/api/v1/admin/settings/', settings.value)
        // Ajouter une notification de succès ici
      } catch (error) {
        console.error('Erreur lors de la sauvegarde des paramètres:', error)
        // Ajouter une notification d'erreur ici
      } finally {
        saving.value = false
      }
    }

    return {
      saving,
      settings,
      languages,
      saveSettings
    }
  }
}
</script> 