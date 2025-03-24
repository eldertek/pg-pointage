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

// Détection de la plateforme
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
const isAndroid = /Android/.test(navigator.userAgent)

// Polyfill pour NDEFReader avec gestion spécifique par plateforme
const getNFCImplementation = () => {
  // iOS : Utilisation de Core NFC via une app native
  if (isIOS) {
    return {
      async scan() {
        throw new Error('La lecture NFC sur iOS nécessite l\'application native. Veuillez installer l\'application Planète Gardiens depuis l\'App Store.')
      }
    }
  }
  
  // Android : Utilisation de Web NFC si disponible
  if (isAndroid) {
    if ('NDEFReader' in window) {
      return new NDEFReader()
    }
    return {
      async scan() {
        throw new Error('Votre appareil Android ne supporte pas la lecture NFC via le navigateur. Veuillez installer l\'application native depuis le Play Store.')
      }
    }
  }
  
  // Autres plateformes
  return {
    async scan() {
      throw new Error('Votre appareil ne supporte pas la lecture NFC')
    }
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
    
    // Fonction pour vérifier la compatibilité NFC
    const checkNFCCompatibility = () => {
      if (isIOS) {
        return {
          compatible: false,
          message: 'Pour utiliser le NFC sur iOS, veuillez installer notre application native depuis l\'App Store'
        }
      }
      
      if (isAndroid) {
        if (!('NDEFReader' in window)) {
          return {
            compatible: false,
            message: 'Votre navigateur ne supporte pas la lecture NFC. Veuillez utiliser Chrome ou installer notre application native'
          }
        }
        return { compatible: true }
      }
      
      return {
        compatible: false,
        message: 'Votre appareil ne supporte pas la lecture NFC'
      }
    }
    
    // Fonction pour démarrer le scan
    const startScan = async () => {
      loading.value = true
      
      try {
        // Vérifier la compatibilité NFC
        const nfcStatus = checkNFCCompatibility()
        if (!nfcStatus.compatible) {
          showError(nfcStatus.message)
          return
        }

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
        const nfcReader = getNFCImplementation()
        await nfcReader.scan()
        
        nfcReader.addEventListener('reading', ({ serialNumber }) => {
          console.log('Badge NFC détecté:', serialNumber)
          
          // Formater l'ID NFC
          let siteId = serialNumber
          if (!siteId.startsWith('PG')) {
            showError('Badge NFC invalide. Format attendu: PG suivi de 6 chiffres')
            scanning.value = false
            return
          }

          // Valider le format
          if (!/^PG\d{6}$/.test(siteId)) {
            showError('Format de badge NFC invalide')
            scanning.value = false
            return
          }

          console.log('ID du site validé:', siteId)
          handleScanResult(siteId)
        })

        nfcReader.addEventListener('error', (error) => {
          console.error('Erreur NFC:', error)
          let errorMessage = 'Erreur lors de la lecture du badge NFC'
          
          if (isAndroid) {
            errorMessage += '. Assurez-vous que le NFC est activé dans les paramètres de votre téléphone'
          }
          
          showError(errorMessage)
          scanning.value = false
        })

      } catch (err) {
        console.error('Erreur lors de l\'initialisation du scan NFC:', err)
        let errorMessage = ''
        
        if (err.name === 'NotAllowedError') {
          errorMessage = 'Veuillez autoriser l\'accès NFC dans les paramètres de votre appareil'
        } else if (err.name === 'NotSupportedError') {
          errorMessage = isIOS 
            ? 'Veuillez utiliser notre application native pour iOS'
            : 'Votre appareil ne supporte pas le NFC'
        } else {
          errorMessage = 'Erreur lors du scan NFC: ' + err.message
        }
        
        showError(errorMessage)
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
      console.log('Traitement du scan pour le site:', siteId)
      try {
        const result = await timesheetStore.createTimesheet({
          site_id: siteId,
          latitude: position.value?.coords.latitude,
          longitude: position.value?.coords.longitude,
          scan_type: 'NFC'
        })
        
        if (result.is_ambiguous) {
          console.log('Cas ambigu détecté')
          // Cas ambigu, demander à l'utilisateur de préciser
          ambiguousTimesheetData.value = {
            site_id: siteId,
            latitude: position.value?.coords.latitude,
            longitude: position.value?.coords.longitude,
            timestamp: new Date().toISOString(),
            scan_type: 'NFC'
          }
          showAmbiguousDialog.value = true
        } else {
          // Pointage réussi
          showSuccess(result.message || 'Pointage enregistré avec succès')
        }
      } catch (err) {
        console.error('Erreur lors du pointage:', err)
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

