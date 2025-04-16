<template>
  <div v-if="showInstallPrompt" class="pwa-install-prompt">
    <v-alert
      color="info"
      icon="mdi-cellphone-arrow-down"
      variant="tonal"
      closable
      class="ma-4"
    >
      <div class="d-flex flex-column">
        <div class="text-body-1 mb-2">
          {{ $t('common.installez_lapplication_sur_votre_appareil_pour_un_accs_rapide') }}
        </div>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            :loading="installing"
            @click="installPwa"
          >
            {{ $t('common.installer_lapplication') }}
          </v-btn>
          <v-btn
            variant="text"
            @click="dismissPrompt"
          >
            {{ $t('common.plus_tard') }}
          </v-btn>
        </div>
      </div>
    </v-alert>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import { ref, onMounted, onBeforeUnmount } from 'vue'

export default {
  name: 'PwaInstall',
  setup() {
    const { t } = useI18n()
    const deferredPrompt = ref(null)
    const showInstallPrompt = ref(false)
    const installing = ref(false)

    // Vérifie si l'app est déjà installée
    const isAppInstalled = () => {
      return window.matchMedia('(display-mode: standalone)').matches ||
             window.navigator.standalone === true
    }

    // Gestionnaire d'événement beforeinstallprompt
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault()
      deferredPrompt.value = e
      
      // Ne pas montrer si déjà installé ou si l'utilisateur a déjà refusé
      if (!isAppInstalled() && !localStorage.getItem('pwa-install-dismissed')) {
        showInstallPrompt.value = true
      }
    }

    // Installation de la PWA
    const installPwa = async () => {
      if (!deferredPrompt.value) return

      installing.value = true
      try {
        await deferredPrompt.value.prompt()
        const choiceResult = await deferredPrompt.value.userChoice
        
        if (choiceResult.outcome === 'accepted') {
          console.log('Utilisateur a accepté l\'installation PWA')
          showInstallPrompt.value = false
        }
      } catch (error) {
        console.error('Erreur lors de l\'installation:', error)
      } finally {
        installing.value = false
        deferredPrompt.value = null
      }
    }

    // Fermer le prompt et sauvegarder la préférence
    const dismissPrompt = () => {
      showInstallPrompt.value = false
      localStorage.setItem('pwa-install-dismissed', 'true')
    }

    // Instructions spécifiques pour iOS
    const isIOS = () => {
      return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
    }

    onMounted(() => {
      // Écouter l'événement beforeinstallprompt
      window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

      // Afficher le prompt pour iOS si nécessaire
      if (isIOS() && !isAppInstalled() && !localStorage.getItem('pwa-install-dismissed')) {
        showInstallPrompt.value = true
      }
    })

    onBeforeUnmount(() => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    })

    return {
      showInstallPrompt,
      installing,
      installPwa,
      dismissPrompt
    }
  }
}
</script>

<style scoped>
.pwa-install-prompt {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  pointer-events: none; /* Permet de cliquer à travers quand caché */
}

.pwa-install-prompt .v-alert {
  pointer-events: auto; /* Réactive les événements pour l'alerte */
  margin: 16px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.gap-2 {
  gap: 8px;
}
</style> 