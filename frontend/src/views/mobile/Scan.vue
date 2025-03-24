<template>
  <div class="scan-container">
    <v-card class="scan-card">
      <v-card-title class="text-center">
        Pointage
      </v-card-title>
      
      <v-card-text>
        <div v-if="!scanning" class="text-center">
          <p class="mb-4">Appuyez sur le bouton ci-dessous pour scanner un badge NFC ou un QR code</p>
          <v-btn 
            color="primary" 
            size="large" 
            @click="startScan" 
            :loading="loading"
            class="mt-4"
          >
            Scanner
          </v-btn>
        </div>
        
        <div v-else class="text-center">
          <p class="mb-4">Approchez votre téléphone du badge NFC ou scannez le QR code</p>
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
          ></v-progress-circular>
          <v-btn 
            color="error" 
            variant="outlined" 
            @click="cancelScan" 
            class="mt-6"
          >
            Annuler
          </v-btn>
        </div>
        
        <v-dialog v-model="showAmbiguousDialog" max-width="500">
          <v-card>
            <v-card-title>Précisez votre action</v-card-title>
            <v-card-text>
              <p>Ce pointage est entre deux plages horaires. Veuillez préciser s'il s'agit d'un départ ou d'une arrivée.</p>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn color="primary" @click="confirmAmbiguousTimesheet('ARRIVAL')">
                Arrivée
              </v-btn>
              <v-btn color="secondary" @click="confirmAmbiguousTimesheet('DEPARTURE')">
                Départ
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-card-text>
    </v-card>
    
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useTimesheetStore } from '@/stores/timesheet'
import { useGeolocation } from '@/composables/useGeolocation'

// Polyfill pour NDEFReader si non disponible
const NDEFReader = window.NDEFReader || class NDEFReader {
  async scan() {
    throw new Error('NFC non supporté sur cet appareil')
  }
}

export default {
  name: 'ScanView',
  setup() {
    const timesheetStore = useTimesheetStore()
    const { getCurrentPosition, position } = useGeolocation()
    
    const scanning = ref(false)
    const loading = ref(false)
    const showAmbiguousDialog = ref(false)
    const ambiguousTimesheetData = ref(null)
    const snackbar = ref({
      show: false,
      text: '',
      color: 'success'
    })
    
    // Fonction pour démarrer le scan
    const startScan = async () => {
      loading.value = true
      
      try {
        // Obtenir la position actuelle
        await getCurrentPosition()
        
        // Démarrer le scan NFC ou QR code
        scanning.value = true
        
        if ('NDEFReader' in window) {
          // Utiliser l'API Web NFC si disponible
          startNfcScan()
        } else {
          // Sinon, utiliser la caméra pour scanner un QR code
          startQrScan()
        }
      } catch (err) {
        showError('Impossible d\'obtenir votre position. Veuillez activer la géolocalisation.')
      } finally {
        loading.value = false
      }
    }
    
    // Fonction pour scanner un badge NFC
    const startNfcScan = async () => {
      try {
        const ndef = new NDEFReader()
        await ndef.scan()
        
        ndef.addEventListener('reading', ({ serialNumber }) => {
          // Traiter les données du badge NFC
          const siteId = serialNumber
          handleScanResult(siteId)
        })
      } catch (err) {
        showError('Erreur lors du scan NFC: ' + err.message)
        scanning.value = false
      }
    }
    
    // Fonction pour scanner un QR code
    const startQrScan = () => {
      // Implémentation du scan QR code
      // Cette partie nécessiterait une bibliothèque comme quagga.js ou zxing
      // Pour simplifier, nous simulons un scan réussi après 2 secondes
      setTimeout(() => {
        const mockSiteId = 'SITE123'
        handleScanResult(mockSiteId)
      }, 2000)
    }
    
    // Fonction pour traiter le résultat du scan
    const handleScanResult = async (siteId) => {
      try {
        const result = await timesheetStore.createTimesheet({
          site_id: siteId,
          latitude: position.value?.coords.latitude,
          longitude: position.value?.coords.longitude
        })
        
        if (result.is_ambiguous) {
          // Cas ambigu, demander à l'utilisateur de préciser
          ambiguousTimesheetData.value = {
            site_id: siteId,
            latitude: position.value?.coords.latitude,
            longitude: position.value?.coords.longitude,
            timestamp: new Date().toISOString()
          }
          showAmbiguousDialog.value = true
        } else {
          // Pointage réussi
          showSuccess(result.message || 'Pointage enregistré avec succès')
        }
      } catch (err) {
        showError(err.message || 'Erreur lors de l\'enregistrement du pointage')
      } finally {
        scanning.value = false
      }
    }
    
    // Fonction pour confirmer un pointage ambigu
    const confirmAmbiguousTimesheet = async (entryType) => {
      try {
        const result = await timesheetStore.createTimesheet({
          ...ambiguousTimesheetData.value,
          entry_type: entryType
        })
        
        showSuccess(result.message || 'Pointage enregistré avec succès')
      } catch (err) {
        showError(err.message || 'Erreur lors de l\'enregistrement du pointage')
      } finally {
        showAmbiguousDialog.value = false
        ambiguousTimesheetData.value = null
      }
    }
    
    // Fonction pour annuler le scan
    const cancelScan = () => {
      scanning.value = false
    }
    
    // Fonctions pour afficher des messages
    const showSuccess = (text) => {
      snackbar.value = {
        show: true,
        text,
        color: 'success'
      }
    }
    
    const showError = (text) => {
      snackbar.value = {
        show: true,
        text,
        color: 'error'
      }
    }
    
    return {
      scanning,
      loading,
      showAmbiguousDialog,
      snackbar,
      startScan,
      cancelScan,
      confirmAmbiguousTimesheet
    }
  }
}
</script>

<style scoped>
.scan-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 56px);
  padding: 16px;
}

.scan-card {
  width: 100%;
  max-width: 500px;
  padding: 16px;
}
</style>

