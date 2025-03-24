<template>
  <div>
    <h1 class="text-h4 mb-4">Tableau de bord</h1>
    
    <v-row>
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">Sites</div>
            <div class="text-h3 mb-2">{{ stats.sitesCount }}</div>
            <div class="text-caption">Total des sites actifs</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">Employés</div>
            <div class="text-h3 mb-2">{{ stats.employeesCount }}</div>
            <div class="text-caption">Total des employés actifs</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">Pointages</div>
            <div class="text-h3 mb-2">{{ stats.timesheetsCount }}</div>
            <div class="text-caption">Pointages aujourd'hui</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6" lg="3">
        <v-card class="mb-4">
          <v-card-text class="text-center">
            <div class="text-overline mb-2">Anomalies</div>
            <div class="text-h3 mb-2">{{ stats.anomaliesCount }}</div>
            <div class="text-caption">Anomalies à traiter</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <v-row>
      <v-col cols="12" lg="8">
        <v-card class="mb-4">
          <v-card-title>Activité récente</v-card-title>
          <v-card-text>
            <p class="text-center py-4">Graphique d'activité à venir</p>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" lg="4">
        <v-card class="mb-4">
          <v-card-title>Dernières anomalies</v-card-title>
          <v-card-text v-if="recentAnomalies.length === 0" class="text-center py-4">
            Aucune anomalie récente
          </v-card-text>
          <v-list v-else>
            <v-list-item v-for="(anomaly, index) in recentAnomalies" :key="index">
              <v-list-item-title>{{ anomaly.type }}</v-list-item-title>
              <v-list-item-subtitle>{{ anomaly.employee }} - {{ anomaly.site }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'DashboardView',
  setup() {
    const stats = ref({
      sitesCount: 0,
      employeesCount: 0,
      timesheetsCount: 0,
      anomaliesCount: 0
    })
    
    const recentAnomalies = ref([])
    
    // Simulation de chargement des données
    setTimeout(() => {
      stats.value = {
        sitesCount: 12,
        employeesCount: 45,
        timesheetsCount: 28,
        anomaliesCount: 3
      }
      
      recentAnomalies.value = [
        { type: 'Retard', employee: 'Jean Dupont', site: 'Centre Commercial' },
        { type: 'Départ anticipé', employee: 'Marie Martin', site: 'Hôpital Nord' },
        { type: 'Arrivée manquante', employee: 'Pierre Lambert', site: 'Résidence Les Pins' }
      ]
    }, 1000)
    
    return {
      stats,
      recentAnomalies
    }
  }
}
</script>

