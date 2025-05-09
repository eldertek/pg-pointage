<template>
  <div class="dashboard-container">
    <!-- Vue simplifiée -->
    <template v-if="user?.simplified_mobile_view">
      <v-card class="simplified-view">
        <v-card-text class="text-center">
          <AppTitle :level="2" class="mb-4">Bonjour{{ user?.first_name ? ' ' + user.first_name : '' }}</AppTitle>
          <v-btn
            color="primary"
            size="x-large"
            to="/mobile/scan"
            class="mb-4"
            block
          >
            {{ $t('mobile.senregistrer_maintenant') }}
          </v-btn>
          <v-btn
            variant="text"
            color="primary"
            to="/mobile/profile"
            size="small"
          >
            {{ $t('mobile.accder_au_profil') }}
          </v-btn>
        </v-card-text>
      </v-card>
    </template>

    <!-- Vue complète -->
    <v-card v-else class="dashboard-card">
      <v-card-title class="text-center">
        {{ $t('dashboard.title') }}
      </v-card-title>
      
      <v-card-text>
        <div class="text-center mb-6">
          <AppTitle :level="2" class="mb-2">Bonjour{{ user?.first_name ? ' ' + user.first_name : '' }}</AppTitle>
          <AppText>{{ currentDate }}</AppText>
        </div>
        
        <v-row>
          <v-col cols="6">
            <v-card variant="outlined" class="stat-card">
              <v-card-text class="text-center">
                <div class="text-overline mb-1">{{ $t('mobile.retards') }}</div>
                <div class="text-h4 mb-2">{{ stats?.lateCount || 0 }}</div>
                <div class="text-caption">{{ $t('mobile.ce_moisci') }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="6">
            <v-card variant="outlined" class="stat-card">
              <v-card-text class="text-center">
                <div class="text-overline mb-1">{{ $t('mobile.dparts_anticips') }}</div>
                <div class="text-h4 mb-2">{{ stats?.earlyDepartureCount || 0 }}</div>
                <div class="text-caption">{{ $t('mobile.ce_moisci') }}</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <div class="mt-6">
          <AppTitle :level="3" class="mb-3">Derniers enregistrements</AppTitle>
          <v-timeline density="compact" align="start">
            <v-timeline-item
              v-for="(timesheet, index) in recentTimesheets"
              :key="index"
              :dot-color="getTimesheetColor(timesheet)"
              size="small"
            >
              <div class="d-flex justify-space-between align-center">
                <div>
                  <div class="text-subtitle-2">{{ timesheet.site_name }}</div>
                  <div class="text-caption">{{ formatDate(timesheet.timestamp) }}</div>
                </div>
                <v-chip
                  :color="getTimesheetColor(timesheet)"
                  size="small"
                  class="ml-2"
                >
                  {{ timesheet.entry_type === 'ARRIVAL' ? 'Arrivée' : 'Départ' }}
                </v-chip>
              </div>
              <div v-if="timesheet.is_late || timesheet.is_early_departure" class="mt-1">
                <v-chip
                  size="x-small"
                  color="warning"
                  variant="outlined"
                  class="mt-1"
                >
                  {{ timesheet.is_late ? `Retard de ${timesheet.late_minutes} min` : `Départ anticipé de ${timesheet.early_departure_minutes} min` }}
                </v-chip>
              </div>
            </v-timeline-item>
          </v-timeline>
          
          <div v-if="recentTimesheets.length === 0" class="text-center pa-4">
            <AppText class="text-medium-emphasis">Aucun enregistrement récent</AppText>
          </div>
          
          <div class="text-center mt-4">
            <v-btn
              variant="text"
              color="primary"
              to="/mobile/history"
              size="small"
            >
              {{ $t('mobile.voir_tout_lhistorique') }}
            </v-btn>
          </div>
        </div>
        
        <div class="mt-6">
          <AppTitle :level="3" class="mb-3">Message</AppTitle>
          <v-card
            :color="stats.lateCount > 0 || stats.earlyDepartureCount > 0 ? 'warning' : 'success'"
            variant="outlined"
            class="message-card"
          >
            <v-card-text>
              <AppText v-if="!stats.lateCount && !stats.earlyDepartureCount">
                Félicitations ! Vous n'avez aucun retard ni départ anticipé ce mois-ci.
              </AppText>
              <AppText v-else>
                Vous avez {{ stats.lateCount || 0 }} retard(s) et {{ stats.earlyDepartureCount || 0 }} départ(s) anticipé(s) ce mois-ci.
              </AppText>
            </v-card-text>
          </v-card>
        </div>
      </v-card-text>
      
      <v-card-actions class="justify-center">
        <v-btn
          color="primary"
          size="large"
          to="/mobile/scan"
          block
        >
          {{ $t('mobile.senregistrer_maintenant') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTimesheetStore } from '@/stores/timesheet'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { AppTitle, AppText } from '@/components/typography'

export default {
  name: 'MobileDashboard',
  components: {
    AppTitle,
    AppText
  },
  setup() {
    const { t } = useI18n()
    const authStore = useAuthStore()
    const timesheetStore = useTimesheetStore()
    
    const user = computed(() => authStore.user)
    const recentTimesheets = ref([])
    const stats = ref({
      lateCount: 0,
      earlyDepartureCount: 0,
      totalHours: 0
    })
    
    const currentDate = computed(() => {
      return format(new Date(), 'EEEE d MMMM yyyy', { locale: fr })
    })
    
    const fetchData = async () => {
      try {
        // Récupérer les derniers pointages
        const timesheets = await timesheetStore.fetchRecentTimesheets()
        recentTimesheets.value = timesheets?.slice(0, 5) || []
        
        // Récupérer les statistiques
        const userStats = await timesheetStore.fetchUserStats()
        if (userStats) {
          stats.value = {
            lateCount: userStats.lateCount || 0,
            earlyDepartureCount: userStats.earlyDepartureCount || 0,
            totalHours: userStats.totalHours || 0
          }
        }
      } catch (err) {
        console.error('Erreur lors de la récupération des données:', err)
      }
    }
    
    const formatDate = (dateString) => {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm')
    }
    
    const getTimesheetColor = (timesheet) => {
      if (timesheet.is_late) return 'warning'
      if (timesheet.is_early_departure) return 'error'
      return timesheet.entry_type === 'ARRIVAL' ? 'success' : 'info'
    }
    
    onMounted(() => {
      fetchData()
    })
    
    return {
      user,
      currentDate,
      recentTimesheets,
      stats,
      formatDate,
      getTimesheetColor
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 16px;
}

.dashboard-card,
.simplified-view {
  width: 100%;
}

.simplified-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  margin-top: 20vh;
}

.stat-card {
  height: 100%;
}

.message-card {
  border-radius: 8px;
}
</style>

