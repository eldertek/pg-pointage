<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <div>
        <h1 class="text-h4">{{ isSuperAdmin ? 'Gestion des accès' : 'Gestion des Employés' }}</h1>
        <v-btn-toggle
          v-if="isSuperAdmin"
          v-model="currentView"
          mandatory
          color="primary"
          class="mt-2"
        >
          <v-btn value="users" variant="text">
            <v-icon start>mdi-account-group</v-icon>
            Utilisateurs
          </v-btn>
          <v-btn value="organizations" variant="text">
            <v-icon start>mdi-domain</v-icon>
            Organisations
          </v-btn>
        </v-btn-toggle>
      </div>
      <v-btn 
        color="primary" 
        :prepend-icon="currentView === 'users' ? 'mdi-account-plus' : 'mdi-domain-plus'"
        @click="showCreateDialog = true"
      >
        {{ currentView === 'users' ? 'Nouvel Utilisateur' : 'Nouvelle Organisation' }}
      </v-btn>
    </div>

    <v-card>
      <v-card-title>
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Rechercher"
          single-line
          hide-details
          variant="outlined"
          density="compact"
        ></v-text-field>
      </v-card-title>

      <!-- Table des utilisateurs -->
      <v-data-table
        v-if="currentView === 'users' || !isSuperAdmin"
        :headers="userHeaders"
        :items="users"
        :search="search"
        :loading="loading"
        :items-per-page-options="[5, 10, 20, 50, 100]"
        :items-per-page="10"
        :no-data-text="'Aucun utilisateur trouvé'"
        :loading-text="'Chargement des utilisateurs...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :footer-props="{
          'items-per-page-all-text': 'Tout',
          'items-per-page-text': 'Lignes par page',
          'page-text': '{0}-{1} sur {2}',
          'items-per-page-options': [5, 10, 20, 50, 100]
        }"
        @click:row="(_, { item }) => editItem(item)"
      >
        <template v-slot:item.fullName="{ item }">
          {{ item.first_name }} {{ item.last_name }}
        </template>

        <template v-slot:item.role="{ item }">
          <v-chip
            :color="getRoleColor(item.role)"
            size="small"
          >
            {{ item.role }}
          </v-chip>
        </template>

        <template v-slot:item.sites="{ item }">
          <div v-if="item.role === 'MANAGER'">
            <v-tooltip v-if="item.managed_sites && item.managed_sites.length > 0">
              <template v-slot:activator="{ props }">
                <v-chip
                  color="primary"
                  size="small"
                  v-bind="props"
                >
                  {{ item.managed_sites.length }} site(s) géré(s)
                </v-chip>
              </template>
              <div>Sites gérés :</div>
              <ul>
                <li v-for="site in item.managed_sites" :key="site.id">
                  {{ site.name }}
                </li>
              </ul>
            </v-tooltip>
            <span v-else>Aucun site géré</span>
          </div>
          <div v-else-if="item.role === 'EMPLOYEE'">
            <v-tooltip v-if="item.assigned_sites && item.assigned_sites.length > 0">
              <template v-slot:activator="{ props }">
                <v-chip
                  color="success"
                  size="small"
                  v-bind="props"
                >
                  {{ item.assigned_sites.length }} site(s) assigné(s)
                </v-chip>
              </template>
              <div>Sites assignés :</div>
              <ul>
                <li v-for="site in item.assigned_sites" :key="site.id">
                  {{ site.name }}
                </li>
              </ul>
            </v-tooltip>
            <span v-else>Aucun site assigné</span>
          </div>
        </template>

        <template v-slot:item.is_active="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'error'"
            size="small"
          >
            {{ item.is_active ? 'Actif' : 'Inactif' }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-tooltip text="Modifier">
            <template v-slot:activator="{ props }">
              <v-btn
                icon
                variant="text"
                size="small"
                color="primary"
                @click="editItem(item)"
                v-bind="props"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
            </template>
          </v-tooltip>
          <v-tooltip
            :text="isCurrentUser(item) ? 'Vous ne pouvez pas désactiver votre propre compte' : item.is_active ? 'Désactiver' : 'Activer'"
          >
            <template v-slot:activator="{ props }">
              <v-btn
                icon
                variant="text"
                size="small"
                :color="item.is_active ? 'error' : 'success'"
                @click="toggleUserStatus(item)"
                :disabled="isCurrentUser(item)"
                v-bind="props"
              >
                <v-icon>{{ item.is_active ? 'mdi-account-off' : 'mdi-account-check' }}</v-icon>
              </v-btn>
            </template>
          </v-tooltip>
        </template>
      </v-data-table>

      <!-- Table des organisations (uniquement pour super admin) -->
      <v-data-table
        v-if="currentView === 'organizations' && isSuperAdmin"
        :headers="organizationHeaders"
        :items="organizations"
        :search="search"
        :loading="loading"
        :items-per-page-options="[5, 10, 20, 50, 100]"
        :items-per-page="10"
        :no-data-text="'Aucune organisation trouvée'"
        :loading-text="'Chargement des organisations...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :footer-props="{
          'items-per-page-all-text': 'Tout',
          'items-per-page-text': 'Lignes par page',
          'page-text': '{0}-{1} sur {2}',
          'items-per-page-options': [5, 10, 20, 50, 100]
        }"
        @click:row="(_, { item }) => editItem(item)"
      >
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'error'"
            size="small"
          >
            {{ item.is_active ? 'Active' : 'Inactive' }}
          </v-chip>
        </template>

        <template v-slot:item.phone="{ item }">
          {{ formatPhoneNumber(item.phone) }}
        </template>

        <template v-slot:item.org_id="{ item }">
          <v-chip
            color="primary"
            size="small"
            variant="outlined"
          >
            {{ item.org_id }}
          </v-chip>
        </template>

        <template v-slot:item.address="{ item }">
          {{ item.address }}, {{ item.postal_code }} {{ item.city }}
          <v-btn
            icon
            variant="text"
            size="x-small"
            :href="formatAddressForMaps(item.address, item.postal_code, item.city, item.country)"
            target="_blank"
            color="primary"
          >
            <v-icon>mdi-map-marker</v-icon>
          </v-btn>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-tooltip text="Modifier">
            <template v-slot:activator="{ props }">
              <v-btn
                icon
                variant="text"
                size="small"
                color="primary"
                @click="editItem(item)"
                v-bind="props"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
            </template>
          </v-tooltip>
          <v-tooltip :text="item.is_active ? 'Désactiver' : 'Activer'">
            <template v-slot:activator="{ props }">
              <v-btn
                icon
                variant="text"
                size="small"
                :color="item.is_active ? 'error' : 'success'"
                @click="toggleOrganizationStatus(item)"
                v-bind="props"
              >
                <v-icon>{{ item.is_active ? 'mdi-domain-off' : 'mdi-domain' }}</v-icon>
              </v-btn>
            </template>
          </v-tooltip>
          <v-tooltip text="Voir les détails">
            <template v-slot:activator="{ props }">
              <v-btn
                icon
                variant="text"
                size="small"
                :to="`/dashboard/organizations/${item.id}`"
                v-bind="props"
              >
                <v-icon>mdi-eye</v-icon>
              </v-btn>
            </template>
          </v-tooltip>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog pour créer/éditer -->
    <v-dialog v-model="showCreateDialog" max-width="600px" @update:model-value="onDialogClose">
      <v-card>
        <v-card-title>
          {{ getDialogTitle() }}
        </v-card-title>
        <v-card-text>
          <v-form ref="form" @submit.prevent="saveItem">
            <!-- Formulaire utilisateur -->
            <template v-if="currentView === 'users' || !isSuperAdmin">
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="userForm.first_name"
                    label="Prénom"
                    required
                    autocomplete="given-name"
                    :rules="[v => !!v || 'Le prénom est requis']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="userForm.last_name"
                    label="Nom"
                    required
                    autocomplete="family-name"
                    :rules="[v => !!v || 'Le nom est requis']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="userForm.email"
                    label="Email"
                    type="email"
                    required
                    autocomplete="email"
                    :rules="[
                      v => !!v || 'L\'email est requis',
                      v => /.+@.+\..+/.test(v) || 'L\'email doit être valide'
                    ]"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="userForm.role"
                    :items="availableRoles"
                    label="Rôle"
                    required
                    autocomplete="off"
                    :rules="[v => !!v || 'Le rôle est requis']"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6" v-if="isSuperAdmin">
                  <v-select
                    v-model="userForm.organization"
                    :items="organizations"
                    label="Organisation"
                    item-title="name"
                    item-value="id"
                    autocomplete="off"
                    :disabled="userForm.role === 'SUPER_ADMIN'"
                    :rules="[v => userForm.role === 'SUPER_ADMIN' || !!v || 'L\'organisation est requise']"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6" v-if="userForm.role === 'EMPLOYEE'">
                  <v-select
                    v-model="userForm.scan_preference"
                    :items="scanPreferences"
                    label="Méthode de scan"
                    item-title="text"
                    item-value="value"
                    autocomplete="off"
                    :rules="[v => !!v || 'La méthode de scan est requise']"
                  ></v-select>
                </v-col>
                <v-col cols="12" v-if="userForm.role === 'EMPLOYEE'">
                  <v-switch
                    v-model="userForm.simplified_mobile_view"
                    label="Vue mobile simplifiée"
                    color="primary"
                    hint="Affiche uniquement le bouton de pointage sur mobile"
                    persistent-hint
                  ></v-switch>
                </v-col>
                <!-- Champs mot de passe en création et édition -->
                <template v-if="!editedItem || (editedItem && showPasswordFields)">
                  <v-col cols="12" sm="6">
                    <v-text-field
                      v-model="userForm.password"
                      label="Mot de passe"
                      type="password"
                      :rules="passwordRules"
                      autocomplete="new-password"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field
                      v-model="userForm.confirm_password"
                      label="Confirmer le mot de passe"
                      type="password"
                      :rules="confirmPasswordRules"
                      autocomplete="new-password"
                    ></v-text-field>
                  </v-col>
                </template>
                <v-col v-if="editedItem" cols="12">
                  <v-btn
                    variant="text"
                    color="primary"
                    @click="showPasswordFields = !showPasswordFields"
                  >
                    {{ showPasswordFields ? 'Annuler le changement de mot de passe' : 'Changer le mot de passe' }}
                  </v-btn>
                </v-col>
              </v-row>
            </template>

            <!-- Formulaire organisation (uniquement pour super admin) -->
            <template v-else-if="isSuperAdmin">
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="organizationForm.name"
                    label="Nom de l'organisation"
                    required
                    :rules="[v => !!v || 'Le nom est requis']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="organizationForm.contact_email"
                    label="Email de contact"
                    type="email"
                    required
                    :rules="[
                      v => !!v || 'L\'email est requis',
                      v => /.+@.+\..+/.test(v) || 'L\'email doit être valide'
                    ]"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="organizationForm.phone"
                    label="Téléphone"
                    required
                    :rules="[v => !!v || 'Le téléphone est requis']"
                    :value="organizationForm.phone ? formatPhoneNumber(organizationForm.phone) : ''"
                    @input="e => organizationForm.phone = e.target.value.replace(/\D/g, '')"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="organizationForm.siret"
                    label="SIRET"
                    required
                    :rules="[
                      v => !!v || 'Le SIRET est requis',
                      v => /^\d{14}$/.test(v) || 'Le SIRET doit contenir 14 chiffres'
                    ]"
                  ></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="organizationForm.address"
                    label="Adresse"
                    required
                    :rules="[v => !!v || 'L\'adresse est requise']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model="organizationForm.postal_code"
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
                    v-model="organizationForm.city"
                    label="Ville"
                    required
                    :rules="[v => !!v || 'La ville est requise']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model="organizationForm.country"
                    label="Pays"
                    required
                    value="France"
                    :rules="[v => !!v || 'Le pays est requis']"
                  ></v-text-field>
                </v-col>
              </v-row>
            </template>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="primary" @click="saveItem" :loading="saving">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useRoute, useRouter } from 'vue-router'
import { formatPhoneNumber, formatAddressForMaps } from '@/utils/formatters'

export default {
  name: 'AdminUsersView',
  setup() {
    const authStore = useAuthStore()
    const route = useRoute()
    const router = useRouter()
    const loading = ref(false)
    const saving = ref(false)
    const search = ref('')
    const showCreateDialog = ref(false)
    const form = ref(null)
    const editedItem = ref(null)
    const currentView = ref(authStore.isSuperAdmin ? 'organizations' : 'users')
    const currentUser = ref(null)
    const showPasswordFields = ref(false)
    
    const isSuperAdmin = computed(() => authStore.isSuperAdmin)
    
    const userHeaders = computed(() => {
      const headers = [
        { title: 'Nom', align: 'start', key: 'fullName' },
        { title: 'Courriel', key: 'email' },
        { title: 'Rôle', key: 'role', align: 'center' },
        { title: 'Sites', key: 'sites', align: 'center' },
        { title: 'Statut', key: 'is_active', align: 'center' },
        { title: 'Actions', key: 'actions', align: 'end', sortable: false }
      ]
      
      if (isSuperAdmin.value) {
        headers.splice(3, 0, { title: 'Organisation', key: 'organization_name' })
      }
      
      return headers
    })

    const organizationHeaders = ref([
      { title: 'ID', align: 'start', key: 'org_id' },
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', key: 'contact_email' },
      { title: 'Adresse', key: 'address' },
      { title: 'Téléphone', key: 'phone', format: value => formatPhoneNumber(value) },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])

    const users = ref([])
    const organizations = ref([])
    const roles = ['SUPER_ADMIN', 'MANAGER', 'EMPLOYEE']
    
    const roleLabels = {
      'SUPER_ADMIN': 'Super Administrateur',
      'MANAGER': 'Gestionnaire',
      'EMPLOYEE': 'Employé'
    }

    const scanPreferences = [
      { text: 'NFC et QR Code', value: 'BOTH' },
      { text: 'NFC uniquement', value: 'NFC_ONLY' },
      { text: 'QR Code uniquement', value: 'QR_ONLY' }
    ]

    const userForm = ref({
      first_name: '',
      last_name: '',
      email: '',
      username: '',
      role: '',
      organization: null,
      password: '',
      confirm_password: '',
      scan_preference: 'BOTH',
      simplified_mobile_view: false
    })

    const organizationForm = ref({
      name: '',
      contact_email: '',
      phone: '',
      siret: '',
      address: '',
      postal_code: '',
      city: '',
      country: 'France',
      notes: ''
    })

    const passwordRules = [
      v => !showPasswordFields.value || !editedItem.value || !!v || 'Le mot de passe est requis',
      v => !v || v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères'
    ]

    const confirmPasswordRules = [
      v => !showPasswordFields.value || !editedItem.value || !!v || 'La confirmation du mot de passe est requise',
      v => !v || v === userForm.value.password || 'Les mots de passe ne correspondent pas'
    ]

    const availableRoles = computed(() => {
      if (isSuperAdmin.value) {
        return ['SUPER_ADMIN', 'MANAGER', 'EMPLOYEE']
      }
      return ['EMPLOYEE'] // Les managers ne peuvent créer que des employés
    })

    const getRoleColor = (role) => {
      switch (role) {
        case 'SUPER_ADMIN':
          return 'purple'
        case 'MANAGER':
          return 'primary'
        case 'EMPLOYEE':
          return 'success'
        default:
          return 'grey'
      }
    }

    const fetchUsers = async () => {
      loading.value = true
      try {
        const response = await api.get('/users/', {
          params: {
            role: isSuperAdmin.value ? undefined : 'EMPLOYEE'
          }
        })
        console.log('Données utilisateurs reçues:', response.data)
        users.value = response.data.results || []
      } catch (error) {
        console.error('Erreur lors du chargement des utilisateurs:', error)
      } finally {
        loading.value = false
      }
    }

    const fetchOrganizations = async () => {
      loading.value = true
      try {
        const response = await api.get('/organizations/')
        console.log('Données organisations reçues:', response.data)
        organizations.value = response.data.results || []
      } catch (error) {
        console.error('Erreur lors du chargement des organisations:', error)
      } finally {
        loading.value = false
      }
    }

    const fetchCurrentUser = async () => {
      try {
        const response = await api.get('/users/profile/')
        currentUser.value = response.data
      } catch (error) {
        console.error('Erreur lors de la récupération du profil:', error)
      }
    }

    const isCurrentUser = (user) => {
      return currentUser.value && user.id === currentUser.value.id
    }

    const editItem = (item) => {
      editedItem.value = item
      if (currentView.value === 'users') {
        userForm.value = { ...item }
      } else {
        organizationForm.value = { ...item }
      }
      showCreateDialog.value = true
    }

    const toggleUserStatus = async (user) => {
      if (isCurrentUser(user)) {
        return // Empêcher la désactivation si c'est l'utilisateur courant
      }
      try {
        await api.patch(`/users/${user.id}/`, {
          is_active: !user.is_active
        })
        console.log('Statut utilisateur modifié avec succès')
        await fetchUsers()
      } catch (error) {
        console.error('Erreur lors de la modification du statut:', error)
      }
    }

    const toggleOrganizationStatus = async (organization) => {
      try {
        await api.patch(`/organizations/${organization.id}/`, {
          is_active: !organization.is_active
        })
        console.log('Statut organisation modifié avec succès')
        await fetchOrganizations()
      } catch (error) {
        console.error('Erreur lors de la modification du statut:', error)
      }
    }

    const getDialogTitle = () => {
      if (currentView.value === 'users') {
        return editedItem.value ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur'
      }
      return editedItem.value ? 'Modifier l\'organisation' : 'Nouvelle organisation'
    }

    const closeDialog = () => {
      showCreateDialog.value = false
      editedItem.value = null
      resetForm()
    }

    const onDialogClose = (val) => {
      if (!val) {
        editedItem.value = null
        resetForm()
      }
    }

    const saveItem = async () => {
      if (!form.value) return
      const { valid } = await form.value.validate()
      if (!valid) return

      saving.value = true
      try {
        if (currentView.value === 'users' || !isSuperAdmin.value) {
          const userData = { ...userForm.value }
          // Si c'est un manager, on force l'organisation
          if (!isSuperAdmin.value) {
            userData.organization = authStore.user.organization
            userData.role = 'EMPLOYEE'
          }
          
          // Générer le username à partir de l'email
          userData.username = userData.email.split('@')[0]
          
          if (editedItem.value) {
            // En mode édition, on envoie le mot de passe uniquement s'il est renseigné
            console.log('Données avant traitement:', userData)
            if (!showPasswordFields.value || !userData.password) {
              console.log('Suppression des champs mot de passe car non modifiés')
              delete userData.password
              delete userData.confirm_password
            } else {
              console.log('Envoi du nouveau mot de passe')
              delete userData.confirm_password
            }
            console.log('Données finales envoyées:', userData)
            await api.put(`/users/${editedItem.value.id}/`, userData)
          } else {
            // En mode création, on supprime la confirmation du mot de passe
            delete userData.confirm_password
            console.log('Données envoyées pour création:', userData)
            await api.post('/users/', userData)
          }
          await fetchUsers()
        } else if (isSuperAdmin.value) {
          if (editedItem.value) {
            await api.put(`/organizations/${editedItem.value.id}/`, organizationForm.value)
            // Si on est en mode édition depuis la vue de détail, on redirige vers la vue de détail
            if (route.meta.editMode) {
              router.push(`/dashboard/organizations/${editedItem.value.id}`)
              return
            }
          } else {
            await api.post('/organizations/', organizationForm.value)
          }
          await fetchOrganizations()
        }
        closeDialog()
      } catch (error) {
        console.error('Erreur lors de l\'enregistrement:', error)
      } finally {
        saving.value = false
      }
    }

    const resetForm = () => {
      if (form.value) {
        form.value.reset()
      }
      showPasswordFields.value = false
      
      if (currentView.value === 'users') {
        userForm.value = {
          first_name: '',
          last_name: '',
          email: '',
          role: '',
          organization: null,
          password: '',
          confirm_password: '',
          scan_preference: 'BOTH',
          simplified_mobile_view: false
        }
      } else {
        organizationForm.value = {
          name: '',
          contact_email: '',
          phone: '',
          siret: '',
          address: '',
          postal_code: '',
          city: '',
          country: 'France',
          notes: ''
        }
      }
    }

    // Surveiller les changements de vue pour recharger les données
    watch(currentView, () => {
      if (currentView.value === 'users') {
        fetchUsers()
      } else {
        fetchOrganizations()
      }
    })

    // Si on est en mode édition depuis la vue de détail
    if (route.meta.editMode && route.params.id) {
      currentView.value = 'organizations'
      // Charger l'organisation à éditer
      onMounted(async () => {
        try {
          const response = await api.get(`/organizations/${route.params.id}/`)
          editedItem.value = response.data
          organizationForm.value = { ...response.data }
          showCreateDialog.value = true
        } catch (error) {
          console.error('Erreur lors du chargement de l\'organisation:', error)
        }
      })
    }

    onMounted(() => {
      fetchCurrentUser()
      fetchUsers()
      fetchOrganizations()
    })

    return {
      loading,
      saving,
      search,
      userHeaders,
      organizationHeaders,
      users,
      organizations,
      roles,
      roleLabels,
      showCreateDialog,
      form,
      userForm,
      organizationForm,
      currentView,
      getRoleColor,
      editItem,
      toggleUserStatus,
      toggleOrganizationStatus,
      saveItem,
      getDialogTitle,
      closeDialog,
      onDialogClose,
      isCurrentUser,
      showPasswordFields,
      passwordRules,
      confirmPasswordRules,
      editedItem,
      scanPreferences,
      isSuperAdmin,
      availableRoles,
      formatPhoneNumber,
      formatAddressForMaps
    }
  }
}
</script>

<style scoped>
.v-btn-toggle {
  background-color: rgba(var(--v-theme-surface-variant), 0.08);
  border-radius: 8px;
}

/* Styles des boutons d'action */
:deep(.v-btn--icon) {
  background-color: transparent !important;
  opacity: 1 !important;
}

:deep(.v-btn--icon .v-icon) {
  color: inherit !important;
  opacity: 1 !important;
}

/* Style des boutons colorés */
:deep(.v-btn[color="primary"]) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn[color="error"]) {
  background-color: #F78C48 !important;
  color: white !important;
}

:deep(.v-btn[color="success"]) {
  background-color: #00346E !important;
  color: white !important;
}

/* Style des boutons icônes colorés */
:deep(.v-btn--icon[color="primary"]) {
  color: #00346E !important;
}

:deep(.v-btn--icon[color="error"]) {
  color: #F78C48 !important;
}

:deep(.v-btn--icon[color="success"]) {
  color: #00346E !important;
}

/* Correction des overlays et underlays */
:deep(.v-btn__overlay),
:deep(.v-btn__underlay) {
  opacity: 0 !important;
}

/* Style des boutons dans le toggle */
:deep(.v-btn-toggle .v-btn) {
  opacity: 1 !important;
  color: #00346E !important;
}

:deep(.v-btn-toggle .v-btn--active) {
  background-color: rgba(0, 52, 110, 0.1) !important;
  color: #00346E !important;
}
</style> 