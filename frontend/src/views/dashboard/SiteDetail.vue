<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Détails du site</h1>
      <div>
        <v-btn color="#00346E" class="mr-2" prepend-icon="mdi-pencil" @click="editSite">
          Modifier
        </v-btn>
        <v-btn color="#F78C48" prepend-icon="mdi-delete" @click="deleteSite">
          Supprimer
        </v-btn>
      </div>
    </div>
    
    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="#00346E" size="64"></v-progress-circular>
      </v-col>
    </v-row>
    
    <template v-else>
      <v-row>
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title>Informations générales</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-domain"></v-icon>
                  </template>
                  <v-list-item-title>Nom</v-list-item-title>
                  <v-list-item-subtitle>{{ site.name }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-map-marker"></v-icon>
                  </template>
                  <v-list-item-title>Adresse</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ site.address }}<br>
                    {{ site.postal_code }} {{ site.city }}<br>
                    {{ site.country }}
                  </v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-domain"></v-icon>
                  </template>
                  <v-list-item-title>Franchise</v-list-item-title>
                  <v-list-item-subtitle>{{ site.organization }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-nfc"></v-icon>
                  </template>
                  <v-list-item-title>ID NFC</v-list-item-title>
                  <v-list-item-subtitle>{{ site.nfcId }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="site.qrCode">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-qrcode"></v-icon>
                  </template>
                  <v-list-item-title>QR Code</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-img :src="site.qrCode" max-width="150" contain></v-img>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
        
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title>Paramètres de géolocalisation et synchronisation</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-map-marker-radius"></v-icon>
                  </template>
                  <v-list-item-title>Géolocalisation requise</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip
                      :color="site.requireGeolocation ? 'success' : 'error'"
                      :text="site.requireGeolocation ? 'Oui' : 'Non'"
                    ></v-chip>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="site.requireGeolocation">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-radius"></v-icon>
                  </template>
                  <v-list-item-title>Rayon de géolocalisation</v-list-item-title>
                  <v-list-item-subtitle>{{ site.geolocationRadius }} mètres</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-sync"></v-icon>
                  </template>
                  <v-list-item-title>Mode hors ligne autorisé</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip
                      :color="site.allowOfflineMode ? 'success' : 'error'"
                      :text="site.allowOfflineMode ? 'Oui' : 'Non'"
                    ></v-chip>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="site.allowOfflineMode">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-timer"></v-icon>
                  </template>
                  <v-list-item-title>Durée maximale hors ligne</v-list-item-title>
                  <v-list-item-subtitle>{{ site.maxOfflineDuration }} heures</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <v-card class="mb-4">
        <v-card-title>Paramètres d'alertes</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-clock-alert"></v-icon>
              </template>
              <v-list-item-title>Marge de retard</v-list-item-title>
              <v-list-item-subtitle>{{ site.lateMargin }} minutes</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-clock-fast"></v-icon>
              </template>
              <v-list-item-title>Marge de départ anticipé</v-list-item-title>
              <v-list-item-subtitle>{{ site.earlyDepartureMargin }} minutes</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-clock-question"></v-icon>
              </template>
              <v-list-item-title>Marge pour cas ambigus</v-list-item-title>
              <v-list-item-subtitle>{{ site.ambiguousMargin }} minutes</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon icon="mdi-email-alert"></v-icon>
              </template>
              <v-list-item-title>Emails pour alertes</v-list-item-title>
              <v-list-item-subtitle>
                <v-chip
                  v-for="email in site.alertEmailList"
                  :key="email"
                  class="ma-1"
                  size="small"
                >
                  {{ email }}
                </v-chip>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
      
      <v-card class="mb-4">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Plannings ({{ schedules.length }})</span>
          <v-btn color="#00346E" size="small" prepend-icon="mdi-plus-circle" @click="openScheduleDialog">
            Ajouter un planning
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="schedulesHeaders"
            :items="schedules"
            :items-per-page="5"
            :no-data-text="'Aucun planning trouvé'"
            :loading-text="'Chargement des plannings...'"
            :items-per-page-text="'Lignes par page'"
            :page-text="'{0}-{1} sur {2}'"
            :items-per-page-options="[
              { title: '5', value: 5 },
              { title: '10', value: 10 },
              { title: '15', value: 15 },
              { title: 'Tout', value: -1 }
            ]"
          >
            <template #actions="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                :to="`/dashboard/schedules/${item.raw.id}`"
              >
                <v-icon>mdi-eye</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
      
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Employés assignés ({{ employees.length }})</span>
          <v-btn color="#00346E" size="small" prepend-icon="mdi-plus-circle" @click="openEmployeeDialog">
            Assigner un employé
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="employeesHeaders"
            :items="employees"
            :items-per-page="5"
            :no-data-text="'Aucun employé trouvé'"
            :loading-text="'Chargement des employés...'"
            :items-per-page-text="'Lignes par page'"
            :page-text="'{0}-{1} sur {2}'"
            :items-per-page-options="[
              { title: '5', value: 5 },
              { title: '10', value: 10 },
              { title: '15', value: 15 },
              { title: 'Tout', value: -1 }
            ]"
          >
            <template #actions="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                :to="`/dashboard/employees/${item.raw.id}`"
              >
                <v-icon>mdi-eye</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </template>

    <!-- Dialog pour modifier le site -->
    <v-dialog v-model="showEditDialog" max-width="800px" @update:model-value="onDialogClose">
      <v-card>
        <v-card-title>Modifier le site</v-card-title>
        <v-card-text>
          <v-form ref="form" @submit.prevent="saveSite">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.name"
                  label="Nom du site"
                  required
                  :rules="[v => !!v || 'Le nom est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.nfcId"
                  label="ID NFC"
                  required
                  :prefix="'PG'"
                  placeholder="123456"
                  :rules="[
                    v => !!v || 'L\'ID NFC est requis',
                    v => /^\d{6}$/.test(v) || 'L\'ID NFC doit être composé de 6 chiffres'
                  ]"
                  hint="Entrez uniquement les 6 chiffres, PG sera ajouté automatiquement"
                  persistent-hint
                  @update:model-value="formatNfcId"
                  maxlength="6"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="siteForm.address"
                  label="Adresse"
                  required
                  :rules="[v => !!v || 'L\'adresse est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.postal_code"
                  label="Code postal"
                  required
                  :rules="[
                    v => !!v || 'Le code postal est requis',
                    v => /^\d{5}$/.test(v) || 'Le code postal doit contenir 5 chiffres'
                  ]"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.city"
                  label="Ville"
                  required
                  :rules="[v => !!v || 'La ville est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.country"
                  label="Pays"
                  required
                  value="France"
                  :rules="[v => !!v || 'Le pays est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.lateMargin"
                  label="Marge de retard (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge de retard est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.earlyDepartureMargin"
                  label="Marge de départ anticipé (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge de départ anticipé est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.ambiguousMargin"
                  label="Marge pour cas ambigus (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge pour cas ambigus est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="siteForm.alertEmails"
                  label="Emails pour les alertes (séparés par des virgules)"
                  required
                  :rules="[
                    v => !!v || 'Au moins un email est requis',
                    v => v.split(',').every(email => /.+@.+\..+/.test(email.trim())) || 'Format d\'email invalide'
                  ]"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-divider class="mb-3">Paramètres de géolocalisation</v-divider>
                <v-switch
                  v-model="siteForm.requireGeolocation"
                  label="Géolocalisation requise"
                  color="primary"
                ></v-switch>
                <v-text-field
                  v-if="siteForm.requireGeolocation"
                  v-model="siteForm.geolocationRadius"
                  label="Rayon de géolocalisation (mètres)"
                  type="number"
                  required
                  :rules="[v => !!v || 'Le rayon de géolocalisation est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-divider class="mb-3">Paramètres de synchronisation</v-divider>
                <v-switch
                  v-model="siteForm.allowOfflineMode"
                  label="Autoriser le mode hors ligne"
                  color="primary"
                ></v-switch>
                <v-text-field
                  v-if="siteForm.allowOfflineMode"
                  v-model="siteForm.maxOfflineDuration"
                  label="Durée maximale hors ligne (heures)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La durée maximale hors ligne est requise']"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="primary" @click="saveSite" :loading="saving">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog pour créer un nouveau planning -->
    <v-dialog v-model="showScheduleDialog" max-width="800px" @update:model-value="onDialogClose">
      <v-card>
        <v-card-title>Créer un nouveau planning</v-card-title>
        <v-card-text>
          <v-form ref="scheduleForm" @submit.prevent="addSchedule">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="scheduleFormData.name"
                  label="Nom du planning"
                  required
                  :rules="[v => !!v || 'Le nom est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="scheduleFormData.schedule_type"
                  label="Type de planning"
                  :items="[
                    { title: 'Fixe (gardien)', value: 'FIXED' },
                    { title: 'Fréquence (nettoyage)', value: 'FREQUENCY' }
                  ]"
                  required
                ></v-select>
              </v-col>
              
              <template v-if="scheduleFormData.schedule_type === 'FIXED'">
                <v-col cols="12">
                  <v-divider class="my-4">Configuration des jours et horaires</v-divider>
                </v-col>
                
                <!-- Sélection des jours de travail -->
                <v-col cols="12">
                  <v-select
                    v-model="scheduleFormData.working_days"
                    label="Jours de travail"
                    :items="[
                      { title: 'Lundi', value: 1 },
                      { title: 'Mardi', value: 2 },
                      { title: 'Mercredi', value: 3 },
                      { title: 'Jeudi', value: 4 },
                      { title: 'Vendredi', value: 5 },
                      { title: 'Samedi', value: 6 },
                      { title: 'Dimanche', value: 7 }
                    ]"
                    multiple
                    chips
                    required
                    :rules="[v => v.length > 0 || 'Sélectionnez au moins un jour']"
                  ></v-select>
                </v-col>

                <!-- Configuration des horaires pour chaque jour -->
                <v-col cols="12" v-for="day in scheduleFormData.working_days" :key="day">
                  <v-card class="pa-3">
                    <div class="text-h6 mb-2">{{ ['', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][day] }}</div>
                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="getScheduleForDay(day).morning_start"
                          label="Début matin"
                          type="time"
                          required
                          :rules="[v => !!v || 'L\'heure de début est requise']"
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="getScheduleForDay(day).morning_end"
                          label="Fin matin"
                          type="time"
                          required
                          :rules="[v => !!v || 'L\'heure de fin est requise']"
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="getScheduleForDay(day).afternoon_start"
                          label="Début après-midi"
                          type="time"
                          required
                          :rules="[v => !!v || 'L\'heure de début est requise']"
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="getScheduleForDay(day).afternoon_end"
                          label="Fin après-midi"
                          type="time"
                          required
                          :rules="[v => !!v || 'L\'heure de fin est requise']"
                        ></v-text-field>
                      </v-col>
                    </v-row>
                  </v-card>
                </v-col>
              </template>
              
              <template v-if="scheduleFormData.schedule_type === 'FREQUENCY'">
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="scheduleFormData.min_daily_hours"
                    label="Heures min. quotidiennes"
                    type="number"
                    required
                    :rules="[v => !!v || 'Les heures quotidiennes sont requises']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="scheduleFormData.min_weekly_hours"
                    label="Heures min. hebdomadaires"
                    type="number"
                    required
                    :rules="[v => !!v || 'Les heures hebdomadaires sont requises']"
                  ></v-text-field>
                </v-col>
              </template>
              
              <v-col cols="12">
                <v-divider class="my-4">Paramètres de flexibilité</v-divider>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-switch
                  v-model="scheduleFormData.allow_early_arrival"
                  label="Autoriser l'arrivée en avance"
                  color="primary"
                  :hint="'Permet à l\'employé de pointer avant son heure de début prévue'"
                  persistent-hint
                ></v-switch>
              </v-col>
              <v-col cols="12" md="6">
                <v-switch
                  v-model="scheduleFormData.allow_late_departure"
                  label="Autoriser le départ tardif"
                  color="primary"
                  :hint="'Permet à l\'employé de pointer après son heure de fin prévue'"
                  persistent-hint
                ></v-switch>
              </v-col>
              
              <v-col cols="12" md="6" v-if="scheduleFormData.allow_early_arrival">
                <v-text-field
                  v-model="scheduleFormData.early_arrival_limit"
                  label="Limite d'arrivée en avance (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La limite d\'arrivée en avance est requise']"
                  :hint="'Nombre de minutes maximum avant l\'heure prévue où l\'employé peut pointer'"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6" v-if="scheduleFormData.allow_late_departure">
                <v-text-field
                  v-model="scheduleFormData.late_departure_limit"
                  label="Limite de départ tardif (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La limite de départ tardif est requise']"
                  :hint="'Nombre de minutes maximum après l\'heure prévue où l\'employé peut pointer'"
                  persistent-hint
                ></v-text-field>
              </v-col>
              
              <v-col cols="12">
                <v-divider class="my-4">Paramètres de pause</v-divider>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="scheduleFormData.break_duration"
                  label="Durée de pause (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La durée de pause est requise']"
                  :hint="'Durée obligatoire de la pause en minutes (ex: 60 pour 1h de pause déjeuner)'"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="scheduleFormData.min_break_start"
                  label="Début pause au plus tôt"
                  type="time"
                  :rules="[v => !v || /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(v) || 'Format invalide (HH:MM)']"
                  :hint="'Heure la plus tôt à laquelle la pause peut commencer (ex: 11:30)'"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="scheduleFormData.max_break_end"
                  label="Fin pause au plus tard"
                  type="time"
                  :rules="[v => !v || /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(v) || 'Format invalide (HH:MM)']"
                  :hint="'Heure la plus tard à laquelle la pause doit se terminer (ex: 14:00)'"
                  persistent-hint
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="primary" @click="addSchedule" :loading="saving">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog pour assigner un employé -->
    <v-dialog v-model="showEmployeeDialog" max-width="800px" @update:model-value="onDialogClose">
      <v-card>
        <v-card-title>Assigner un employé</v-card-title>
        <v-card-text>
          <v-form ref="employeeForm" @submit.prevent="assignEmployee">
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="employeeFormData.employee"
                  label="Employé"
                  :items="availableEmployees"
                  item-title="display_name"
                  item-value="id"
                  required
                  :rules="[v => !!v || 'L\'employé est requis']"
                  no-data-text="Aucun employé disponible"
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="employeeFormData.schedule"
                  label="Planning"
                  :items="schedules"
                  item-title="name"
                  item-value="id"
                  required
                  :rules="[v => !!v || 'Le planning est requis']"
                  no-data-text="Aucun planning disponible"
                ></v-select>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="primary" @click="assignEmployee" :loading="saving">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api, { sitesApi } from '@/services/api'

export default {
  name: 'SiteDetailView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const siteId = route.params.id
    
    const loading = ref(true)
    const saving = ref(false)
    const showEditDialog = ref(false)
    const showScheduleDialog = ref(false)
    const showEmployeeDialog = ref(false)
    const form = ref(null)
    const scheduleForm = ref(null)
    const employeeForm = ref(null)
    const site = ref({})
    
    const siteForm = ref({
      name: '',
      address: '',
      postal_code: '',
      city: '',
      country: 'France',
      nfcId: '',
      organization: null,
      lateMargin: 15,
      earlyDepartureMargin: 15,
      ambiguousMargin: 20,
      alertEmails: '',
      requireGeolocation: true,
      geolocationRadius: 100,
      allowOfflineMode: true,
      maxOfflineDuration: 24
    })

    const scheduleFormData = ref({
      name: '',
      schedule_type: 'FIXED',
      min_daily_hours: null,
      min_weekly_hours: null,
      allow_early_arrival: true,
      allow_late_departure: true,
      early_arrival_limit: 30,
      late_departure_limit: 30,
      break_duration: 60,
      min_break_start: null,
      max_break_end: null,
      details: [],
      working_days: [],
      daily_schedules: [
        {
          day: 1, // Lundi
          morning_start: '',
          morning_end: '',
          afternoon_start: '',
          afternoon_end: ''
        }
      ]
    })

    const employeeFormData = ref({
      employee: null,
      schedule: null
    })

    const availableEmployees = ref([])

    const schedulesHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Type', align: 'center', key: 'type' },
      { title: 'Heures min. quotidiennes', align: 'center', key: 'minDailyHours' },
      { title: 'Heures min. hebdomadaires', align: 'center', key: 'minWeeklyHours' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const employeesHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone' },
      { title: 'Planning', align: 'center', key: 'schedule' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const schedules = ref([])
    const employees = ref([])
    
    const fetchSiteData = async () => {
      loading.value = true
      
      try {
        const response = await sitesApi.getSite(siteId)
        const siteData = response.data
        
        // Récupérer les informations de l'organisation
        if (siteData.organization) {
          try {
            const orgResponse = await api.get(`/organizations/${siteData.organization}/`)
            siteData.organization_name = orgResponse.data.name
          } catch (error) {
            console.error('Erreur lors du chargement de l\'organisation:', error)
          }
        }

        // Conversion des données pour l'affichage
        site.value = {
          id: siteData.id,
          name: siteData.name,
          address: siteData.address,
          postal_code: siteData.postal_code,
          city: siteData.city,
          country: siteData.country || 'France',
          nfcId: siteData.nfc_id,
          organization: siteData.organization_name || siteData.organization,
          lateMargin: siteData.late_margin || 15,
          earlyDepartureMargin: siteData.early_departure_margin || 15,
          ambiguousMargin: siteData.ambiguous_margin || 20,
          alertEmails: siteData.alert_emails || '',
          alertEmailList: siteData.alert_emails ? siteData.alert_emails.split(',').map(email => email.trim()) : [],
          requireGeolocation: siteData.require_geolocation ?? true,
          geolocationRadius: siteData.geolocation_radius || 100,
          allowOfflineMode: siteData.allow_offline_mode ?? true,
          maxOfflineDuration: siteData.max_offline_duration || 24,
          qrCode: siteData.qr_code,
          isActive: siteData.is_active
        }
        
        schedules.value = siteData.schedules || []
        employees.value = siteData.employees || []
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error)
      } finally {
        loading.value = false
      }
    }

    const editSite = () => {
      const itemData = { ...site.value }
      siteForm.value = {
        name: itemData.name,
        address: itemData.address,
        postal_code: itemData.postal_code,
        city: itemData.city,
        country: itemData.country || 'France',
        nfcId: itemData.nfc_id?.replace('PG', '') || '',
        organization: itemData.organization,
        lateMargin: itemData.late_margin || 15,
        earlyDepartureMargin: itemData.early_departure_margin || 15,
        ambiguousMargin: itemData.ambiguous_margin || 20,
        alertEmails: itemData.alert_emails || '',
        requireGeolocation: itemData.require_geolocation ?? true,
        geolocationRadius: itemData.geolocation_radius || 100,
        allowOfflineMode: itemData.allow_offline_mode ?? true,
        maxOfflineDuration: itemData.max_offline_duration || 24
      }
      showEditDialog.value = true
    }

    const closeDialog = () => {
      showEditDialog.value = false
      showScheduleDialog.value = false
      showEmployeeDialog.value = false
      resetForm()
      resetScheduleForm()
      resetEmployeeForm()
    }

    const onDialogClose = (val) => {
      if (!val) {
        resetForm()
      }
    }

    const resetForm = () => {
      if (form.value) {
        form.value.reset()
      }
      siteForm.value = {
        name: '',
        address: '',
        postal_code: '',
        city: '',
        country: 'France',
        nfcId: '',
        organization: null,
        lateMargin: 15,
        earlyDepartureMargin: 15,
        ambiguousMargin: 20,
        alertEmails: '',
        requireGeolocation: true,
        geolocationRadius: 100,
        allowOfflineMode: true,
        maxOfflineDuration: 24
      }
    }

    const saveSite = async () => {
      if (!form.value) return
      const { valid } = await form.value.validate()
      if (!valid) return

      saving.value = true
      try {
        const siteData = { ...siteForm.value }
        siteData.nfcId = 'PG' + siteData.nfcId
        
        await sitesApi.updateSite(siteId, siteData)
        await fetchSiteData()
        closeDialog()
      } catch (error) {
        console.error('Erreur lors de la modification du site:', error)
      } finally {
        saving.value = false
      }
    }

    const deleteSite = async () => {
      try {
        await sitesApi.deleteSite(siteId)
        router.push('/dashboard/sites')
      } catch (error) {
        console.error('Erreur lors de la suppression du site:', error)
      }
    }

    const formatNfcId = (value) => {
      if (!value) {
        siteForm.value.nfcId = ''
        return
      }
      
      const numbers = String(value).replace(/\D/g, '')
      
      siteForm.value.nfcId = numbers.substring(0, 6)
    }

    const addSchedule = async () => {
      if (!scheduleForm.value) return
      const { valid } = await scheduleForm.value.validate()
      if (!valid) return

      saving.value = true
      try {
        // Préparer les données
        const scheduleData = {
          ...scheduleFormData.value,
          site: siteId,
          // Convertir les heures en nombres si type FREQUENCY
          min_daily_hours: scheduleFormData.value.schedule_type === 'FREQUENCY' ? 
            parseFloat(scheduleFormData.value.min_daily_hours) : null,
          min_weekly_hours: scheduleFormData.value.schedule_type === 'FREQUENCY' ? 
            parseFloat(scheduleFormData.value.min_weekly_hours) : null,
          // Convertir les minutes en nombres
          early_arrival_limit: parseInt(scheduleFormData.value.early_arrival_limit),
          late_departure_limit: parseInt(scheduleFormData.value.late_departure_limit),
          break_duration: parseInt(scheduleFormData.value.break_duration),
          // Ajouter les horaires fixes si c'est un planning de type FIXED
          working_days: scheduleFormData.value.schedule_type === 'FIXED' ? 
            scheduleFormData.value.working_days : [],
          daily_schedules: scheduleFormData.value.schedule_type === 'FIXED' ? 
            scheduleFormData.value.daily_schedules.filter(schedule => 
              scheduleFormData.value.working_days.includes(schedule.day)
            ) : []
        }

        console.log('Données du planning à créer:', scheduleData)
        const response = await sitesApi.createSchedule(siteId, scheduleData)
        console.log('Planning créé avec succès:', response.data)
        await fetchSiteData()
        showScheduleDialog.value = false
        resetScheduleForm()
      } catch (error) {
        console.error('Erreur lors de la création du planning:', error)
      } finally {
        saving.value = false
      }
    }

    const assignEmployee = async () => {
      if (!employeeForm.value) return
      const { valid } = await employeeForm.value.validate()
      if (!valid) return

      saving.value = true
      try {
        const assignmentData = {
          employee: employeeFormData.value.employee,
          schedule: employeeFormData.value.schedule,
          site: siteId
        }

        const response = await sitesApi.assignEmployee(siteId, assignmentData)
        console.log('Employé assigné avec succès:', response.data)
        await fetchSiteData()
        showEmployeeDialog.value = false
        resetEmployeeForm()
      } catch (error) {
        console.error('Erreur lors de l\'assignation de l\'employé:', error)
      } finally {
        saving.value = false
      }
    }

    const fetchAvailableEmployees = async () => {
      try {
        const response = await api.get('/users/', {
          params: {
            role: 'EMPLOYEE',
            organization: site.value.organization
          }
        })
        // Ajouter une propriété display_name pour chaque employé
        availableEmployees.value = response.data.results.map(employee => ({
          ...employee,
          display_name: `${employee.first_name} ${employee.last_name} (${employee.email})`
        }))
      } catch (error) {
        console.error('Erreur lors du chargement des employés:', error)
      }
    }

    const resetScheduleForm = () => {
      if (scheduleForm.value) {
        scheduleForm.value.reset()
      }
      scheduleFormData.value = {
        name: '',
        schedule_type: 'FIXED',
        min_daily_hours: null,
        min_weekly_hours: null,
        allow_early_arrival: true,
        allow_late_departure: true,
        early_arrival_limit: 30,
        late_departure_limit: 30,
        break_duration: 60,
        min_break_start: null,
        max_break_end: null,
        details: [],
        working_days: [],
        daily_schedules: []
      }
    }

    const resetEmployeeForm = () => {
      if (employeeForm.value) {
        employeeForm.value.reset()
      }
      employeeFormData.value = {
        employee: null,
        schedule: null
      }
    }

    const openScheduleDialog = () => {
      resetScheduleForm()
      showScheduleDialog.value = true
    }

    const openEmployeeDialog = async () => {
      resetEmployeeForm()
      await fetchAvailableEmployees() // Recharger la liste des employés disponibles
      showEmployeeDialog.value = true
    }

    const getScheduleForDay = (day) => {
      let schedule = scheduleFormData.value.daily_schedules.find(s => s.day === day)
      if (!schedule) {
        schedule = {
          day,
          morning_start: '',
          morning_end: '',
          afternoon_start: '',
          afternoon_end: ''
        }
        scheduleFormData.value.daily_schedules.push(schedule)
      }
      return schedule
    }

    onMounted(() => {
      fetchSiteData()
      fetchAvailableEmployees()
    })
    
    return {
      loading,
      saving,
      showEditDialog,
      showScheduleDialog,
      showEmployeeDialog,
      form,
      scheduleForm,
      employeeForm,
      site,
      siteForm,
      scheduleFormData,
      employeeFormData,
      availableEmployees,
      schedulesHeaders,
      employeesHeaders,
      schedules,
      employees,
      editSite,
      deleteSite,
      closeDialog,
      onDialogClose,
      saveSite,
      formatNfcId,
      addSchedule,
      assignEmployee,
      openScheduleDialog,
      openEmployeeDialog,
      getScheduleForDay
    }
  }
}
</script>

