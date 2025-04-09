<template>
  <div class="scan-container">
    <v-card class="scan-card">
      <v-card-title class="text-center">
        Enregistrement
      </v-card-title>
      
      <v-card-text>
        <div v-if="!scanning" class="text-center">
          <p class="mb-4">
            <span v-if="userScanPreference === 'BOTH'">
              Choisissez votre méthode de scan ci-dessous
            </span>
            <span v-else-if="userScanPreference === 'NFC_ONLY'">
              Appuyez sur le bouton ci-dessous pour scanner
            </span>
            <span v-else>
              Appuyez sur le bouton ci-dessous pour scanner
            </span>
          </p>
          
          <!-- Boutons de scan -->
          <div class="d-flex flex-column align-center gap-4">
            <!-- Bouton NFC -->
            <v-btn 
              v-if="userScanPreference === 'NFC_ONLY' || userScanPreference === 'BOTH'"
              color="primary" 
              size="large" 
              :loading="loading && scanMode === 'NFC'"
              class="scan-button"
              @click="startNfcScan"
            >
              <v-icon start class="mr-3">mdi-nfc</v-icon>
              Scanner
            </v-btn>

            <!-- Bouton QR Code -->
            <v-btn 
              v-if="userScanPreference === 'QR_ONLY' || userScanPreference === 'BOTH'"
              color="primary" 
              size="large" 
              :loading="loading && scanMode === 'QR'"
              class="scan-button"
              @click="startQrScan"
            >
              <v-icon start class="mr-3">mdi-qrcode-scan</v-icon>
              Scanner
            </v-btn>
          </div>
        </div>
        
        <div v-else class="text-center">
          <div v-if="isQrScanning" class="video-container">
            <video ref="videoPreview" playsinline class="video-preview"></video>
            <div class="scan-region-highlight">
              <div class="scanning-line"></div>
            </div>
          </div>
          <p v-else class="mb-4">
            <span v-if="scanMode === 'NFC'">
              Approchez votre téléphone du badge NFC
            </span>
            <span v-else>
              Scannez le QR code
            </span>
          </p>
          <div class="loading-container">
            <v-progress-circular
              indeterminate
              color="primary"
              size="32"
            ></v-progress-circular>
            <v-btn 
              color="error" 
              variant="outlined" 
              class="ml-4"
              @click="cancelScan"
            >
              Annuler
            </v-btn>
          </div>
        </div>
        
        <v-dialog v-model="showAmbiguousDialog" max-width="500">
          <v-card>
            <v-card-title>Précisez votre action</v-card-title>
            <v-card-text>
              <p>Cet enregistrement est entre deux plages horaires. Veuillez préciser s'il s'agit d'un départ ou d'une arrivée.</p>
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
      timeout="5000"
      multi-line
    >
      {{ snackbar.text }}
      
      <template #actions>
        <v-btn
          color="white"
          variant="text"
          @click="snackbar.show = false"
        >
          Fermer
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useTimesheetStore } from '@/stores/timesheet'
import { useGeolocation } from '@/composables/useGeolocation'
import { usersApi } from '@/services/api'

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
      return new window.NDEFReader()
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
    const userScanPreference = ref('BOTH')
    const snackbar = ref({
      show: false,
      text: '',
      color: 'success'
    })
    const videoPreview = ref(null)
    const isQrScanning = ref(false)
    const scanMode = ref('QR')
    
    // Récupérer la préférence de scan de l'utilisateur
    const fetchUserScanPreference = async () => {
      try {
        const response = await usersApi.getProfile()
        userScanPreference.value = response.data.scan_preference
      } catch (error) {
        console.error('Erreur lors de la récupération des préférences:', error)
        showError('Erreur lors de la récupération de vos préférences')
      }
    }
    
    // Fonction pour vérifier la compatibilité NFC
    const checkNFCCompatibility = () => {
      // Si l'utilisateur est configuré pour QR uniquement, on ne vérifie pas le NFC
      if (userScanPreference.value === 'QR_ONLY') {
        return { compatible: false, message: 'Mode QR Code uniquement activé' }
      }

      if (isIOS) {
        return {
          compatible: false,
          message: 'Apple ne permet pas d\'utiliser le NFC sur iOS.'
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
    
    // Fonction pour démarrer le scan NFC
    const startNfcScan = async () => {
      loading.value = true
      scanMode.value = 'NFC'
      
      try {
        scanning.value = true
        const nfcStatus = checkNFCCompatibility()
        if (!nfcStatus.compatible) {
          showError(nfcStatus.message)
          scanning.value = false
          return
        }
        
        const nfcReader = getNFCImplementation()
        await nfcReader.scan()
        
        nfcReader.addEventListener('reading', async ({ serialNumber }) => {
          console.log('Badge NFC détecté:', serialNumber)
          
          // Formater l'ID
          let siteId = serialNumber
          if (!siteId.includes('-')) {
            showError('Badge NFC invalide. Format attendu: Oxxx-Syyyy')
            scanning.value = false
            return
          }

          // Valider le format
          if (!validateSiteId(siteId)) {
            showError('Format de badge NFC invalide')
            scanning.value = false
            return
          }

          try {
            await getCurrentPosition()
            console.log('Position GPS obtenue au moment du scan NFC:', position.value)
            handleScanResult(siteId, 'NFC')
          } catch (gpsError) {
            showError('Impossible d\'obtenir votre position. Veuillez activer la géolocalisation.')
            console.error('Erreur lors de la récupération de la position:', gpsError)
            scanning.value = false
          }
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
      } finally {
        loading.value = false
      }
    }
    
    // Fonction pour démarrer le scan QR
    const startQrScan = async () => {
      loading.value = true
      scanMode.value = 'QR'
      
      try {
        scanning.value = true
        isQrScanning.value = true
        
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            facingMode: 'environment',
            width: { ideal: 1280 },
            height: { ideal: 720 },
            zoom: 1,
            focusMode: 'continuous',
            advanced: [{
              facingMode: 'environment',
              zoom: { ideal: 1 },
              focusMode: { ideal: 'continuous' },
              resizeMode: { ideal: 'crop-and-scale' }
            }]
          } 
        })
        const video = videoPreview.value
        video.srcObject = stream
        video.setAttribute('playsinline', true)
        video.setAttribute('autoplay', true)
        video.setAttribute('muted', true)
        video.setAttribute('webkit-playsinline', true)
        await new Promise((resolve) => {
          video.onloadedmetadata = () => {
            resolve()
          }
        })
        await video.play()

        const canvas = document.createElement('canvas')
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        const context = canvas.getContext('2d', { willReadFrequently: true })

        const { default: jsQR } = await import('jsqr')
        
        let lastFrameTime = 0
        const frameInterval = 1000 / 30
        
        const scanFrame = async (timestamp) => {
          if (!scanning.value) {
            stream.getTracks().forEach(track => track.stop())
            isQrScanning.value = false
            return
          }

          if (timestamp - lastFrameTime < frameInterval) {
            requestAnimationFrame(scanFrame)
            return
          }
          
          lastFrameTime = timestamp
          
          try {
            context.drawImage(video, 0, 0, canvas.width, canvas.height)
            const imageData = context.getImageData(0, 0, canvas.width, canvas.height)
            const code = jsQR(imageData.data, imageData.width, imageData.height)

            if (code) {
              try {
                let qrData
                try {
                  qrData = JSON.parse(code.data)
                } catch {
                  const url = new URL(code.data)
                  if (url.hostname.includes('planetegardiens') && url.searchParams.has('site')) {
                    qrData = {
                      type: 'PG_SITE',
                      nfc_id: url.searchParams.get('site')
                    }
                  } else {
                    throw new Error('QR code non reconnu')
                  }
                }
                
                if (qrData.type === 'PG_SITE' && qrData.nfc_id) {
                  // Valider le format de l'ID
                  if (!validateSiteId(qrData.nfc_id)) {
                    throw new Error('Format d\'ID de site invalide')
                  }
                  try {
                    await getCurrentPosition()
                    console.log('Position GPS obtenue au moment du scan QR:', position.value)
                    handleScanResult(qrData.nfc_id, 'QR_CODE')
                    stream.getTracks().forEach(track => track.stop())
                    isQrScanning.value = false
                    return
                  } catch (gpsError) {
                    showError('Impossible d\'obtenir votre position. Veuillez activer la géolocalisation.')
                    console.error('Erreur lors de la récupération de la position:', gpsError)
                    scanning.value = false
                    stream.getTracks().forEach(track => track.stop())
                    isQrScanning.value = false
                    return
                  }
                }
              } catch (e) {
                console.debug('QR code non valide détecté:', e)
              }
            }
          } catch (error) {
            console.error('Erreur lors du scan:', error)
          }
          
          requestAnimationFrame(scanFrame)
        }

        requestAnimationFrame(scanFrame)
      } catch (error) {
        console.error('Erreur lors de l\'initialisation du scan QR:', error)
        showError('Impossible d\'accéder à la caméra. Veuillez vérifier les permissions.')
        scanning.value = false
        isQrScanning.value = false
      } finally {
        loading.value = false
      }
    }
    
    // Validation des IDs de sites
    const validateSiteId = (siteId) => {
      if (!siteId || !siteId.includes('-')) return false;
      
      try {
        const [orgPart, sitePart] = siteId.split('-');
        
        // Valider la partie organisation (Oxxx)
        if (!orgPart.startsWith('O') || orgPart.length !== 4) return false;
        const orgNumber = parseInt(orgPart.slice(1));
        if (isNaN(orgNumber) || orgNumber < 0 || orgNumber > 999) return false;
        
        // Valider la partie site (Syyyy)
        if (!sitePart.startsWith('S') || sitePart.length !== 5) return false;
        const siteNumber = parseInt(sitePart.slice(1));
        if (isNaN(siteNumber) || siteNumber < 1 || siteNumber > 9999) return false;
        
        return true;
      } catch {
        return false;
      }
    };
    
    // Fonction pour traiter le résultat du scan
    const handleScanResult = async (siteId, scanMethod) => {
      try {
        // Formater les coordonnées GPS avec 10 décimales maximum
        const latitude = position.value?.coords.latitude 
          ? Number(position.value.coords.latitude.toFixed(10))
          : null
        const longitude = position.value?.coords.longitude
          ? Number(position.value.coords.longitude.toFixed(10))
          : null

        const result = await timesheetStore.createTimesheet({
          site_id: siteId,
          latitude,
          longitude,
          scan_type: scanMethod
        })
        
        if (result.is_ambiguous) {
          console.log('Cas ambigu détecté')
          // Cas ambigu, demander à l'utilisateur de préciser
          ambiguousTimesheetData.value = {
            site_id: siteId,
            latitude,
            longitude,
            scan_type: scanMethod
          }
          showAmbiguousDialog.value = true
        } else {
          // Enregistrement réussi
          showSuccess(result.message || 'Enregistrement effectué avec succès')
        }
        
        scanning.value = false
      } catch (error) {
        console.error('Erreur lors de l\'enregistrement:', error)
        showError(error.response?.data?.detail || 'Erreur lors de l\'enregistrement')
        scanning.value = false
      }
    }
    
    // Fonction pour confirmer un enregistrement ambigu
    const confirmAmbiguousTimesheet = async (entryType) => {
      try {
        const result = await timesheetStore.createTimesheet({
          ...ambiguousTimesheetData.value,
          entry_type: entryType
        })
        
        showSuccess(result.message || 'Enregistrement effectué avec succès')
      } catch (err) {
        console.error('Erreur lors de l\'enregistrement ambigu:', err)
        
        // Gestion des erreurs de validation du backend
        if (err.response?.data?.detail) {
          const detail = err.response.data.detail
          
          // Si c'est un objet avec des champs d'erreur
          if (typeof detail === 'object') {
            // Extraire les messages d'erreur
            const messages = Object.values(detail)
              .flat()
              .filter(msg => msg)
              .join('\n')
            showError(messages)
          } else {
            // Si c'est une chaîne simple
            showError(detail)
          }
        } else {
          showError('Erreur lors de l\'enregistrement')
        }
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

    onMounted(() => {
      fetchUserScanPreference()
    })

    return {
      scanning,
      loading,
      showAmbiguousDialog,
      snackbar,
      startNfcScan,
      startQrScan,
      cancelScan,
      confirmAmbiguousTimesheet,
      userScanPreference,
      videoPreview,
      isQrScanning,
      scanMode
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

.video-container {
  position: relative;
  width: 100%;
  max-width: 400px;
  margin: 0 auto 20px;
  overflow: hidden;
  border-radius: 8px;
}

.video-preview {
  width: 100%;
  height: auto;
  aspect-ratio: 4/3;
  object-fit: cover;
  background-color: #000;
}

.scan-region-highlight {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 200px;
  height: 200px;
  transform: translate(-50%, -50%);
  border: 2px solid #42A5F5;
  border-radius: 12px;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.scanning-line {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #42A5F5, transparent);
  animation: scanning 2s linear infinite;
}

@keyframes scanning {
  0% {
    top: 0;
  }
  50% {
    top: 100%;
  }
  100% {
    top: 0;
  }
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}

.scan-button {
  min-width: 250px;
  height: 56px;
  font-size: 1.1rem;
  padding-left: 24px;
  padding-right: 24px;
  white-space: nowrap;
}

.gap-4 {
  gap: 1rem;
}

/* Style pour le snackbar */
:deep(.v-snackbar__content) {
  white-space: pre-line;
  text-align: left;
}
</style>

