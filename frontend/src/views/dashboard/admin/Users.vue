<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
<<<<<<< HEAD
      <div>
        <h1 class="text-h4">{{ currentView === 'users' ? 'Gestion des Utilisateurs' : 'Gestion des Franchises' }}</h1>
        <v-btn-toggle
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
            Franchises
          </v-btn>
        </v-btn-toggle>
      </div>
      <v-btn 
        color="primary" 
        :prepend-icon="currentView === 'users' ? 'mdi-account-plus' : 'mdi-domain-plus'"
        @click="showCreateDialog = true"
      >
        {{ currentView === 'users' ? 'Nouvel Utilisateur' : 'Nouvelle Franchise' }}
=======
      <h1 class="text-h4">Gestion des utilisateurs</h1>
      <v-btn color="primary" prepend-icon="mdi-account-plus" @click="showCreateNewUserDialog">
        Nouvel utilisateur
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
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
        v-if="currentView === 'users'"
        :headers="userHeaders"
        :items="users"
        :search="search"
        :loading="loading"
<<<<<<< HEAD
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
=======
        :no-data-text="'Aucun utilisateur trouvé'"
        :loading-text="'Chargement des utilisateurs...'"
        :items-per-page-text="'Lignes par page'"
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
      >
        <template v-slot:item.fullName="{ item }">
          {{ item.first_name }} {{ item.last_name }}
        </template>

        <template v-slot:item.role="{ item }">
          <v-chip
            :color="getRoleColor(item.role)"
            size="small"
          >
<<<<<<< HEAD
            {{ item.role }}
=======
            {{ roleLabels[item.role] || item.role }}
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
          </v-chip>
        </template>

        <template v-slot:item.is_active="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'error'"
            size="small"
          >
            {{ item.is_active ? 'Actif' : 'Inactif' }}
          </v-chip>
        </template>

<<<<<<< HEAD
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
=======
        <template #[`item.actions`]="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click="editUser(item)"
            :title="'Modifier ' + item.full_name"
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
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

      <!-- Table des franchises -->
      <v-data-table
        v-else
        :headers="organizationHeaders"
        :items="organizations"
        :search="search"
        :loading="loading"
        :items-per-page-options="[5, 10, 20, 50, 100]"
        :items-per-page="10"
        :no-data-text="'Aucune franchise trouvée'"
        :loading-text="'Chargement des franchises...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :footer-props="{
          'items-per-page-all-text': 'Tout',
          'items-per-page-text': 'Lignes par page',
          'page-text': '{0}-{1} sur {2}',
          'items-per-page-options': [5, 10, 20, 50, 100]
        }"
      >
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'error'"
            size="small"
<<<<<<< HEAD
          >
            {{ item.is_active ? 'Active' : 'Inactive' }}
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
=======
            :color="item.is_active ? 'error' : 'success'"
            @click="toggleUserStatus(item)"
            :disabled="isCurrentUser(item.id)"
            :title="isCurrentUser(item.id) 
              ? 'Vous ne pouvez pas modifier votre propre statut'
              : (item.is_active ? 'Désactiver ' : 'Activer ') + item.full_name"
          >
            <v-icon>{{ item.is_active ? 'mdi-account-off' : 'mdi-account-check' }}</v-icon>
          </v-btn>
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
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
<<<<<<< HEAD
          <v-form ref="form" @submit.prevent="saveItem">
            <!-- Formulaire utilisateur -->
            <template v-if="currentView === 'users'">
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
                    :items="roles"
                    label="Rôle"
                    required
                    autocomplete="off"
                    :rules="[v => !!v || 'Le rôle est requis']"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6">
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

            <!-- Formulaire franchise -->
            <template v-else>
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="organizationForm.name"
                    label="Nom de la franchise"
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
=======
          <v-form ref="form">
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="userForm.first_name"
                  label="Prénom"
                  required
                  :rules="[rules.required]"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="userForm.last_name"
                  label="Nom"
                  required
                  :rules="[rules.required]"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="userForm.email"
                  label="Courriel"
                  type="email"
                  required
                  :rules="[rules.required, rules.email]"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="userForm.username"
                  label="Nom d'utilisateur"
                  :hint="!userForm.username ? 'Si non renseigné, sera généré à partir de l\'email' : ''"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="userForm.role"
                  :items="roles"
                  label="Rôle"
                  required
                  :rules="[rules.required]"
                  :item-title="role => roleLabels[role] || role"
                  item-value="role"
                  @update:model-value="handleRoleChange"
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6">
                <template v-if="userForm.role === 'SUPER_ADMIN'">
                  <v-text-field
                    label="Franchise"
                    value="Non applicable"
                    disabled
                    readonly
                    hint="Un Super Administrateur n'a pas besoin d'organisation"
                    persistent-hint
                  ></v-text-field>
                </template>
                <template v-else>
                  <v-select
                    v-model="userForm.organization"
                    :items="organizations"
                    label="Franchise"
                    item-title="name"
                    item-value="id"
                    :rules="[rules.required]"
                    hint="Sélectionnez une organisation"
                    persistent-hint
                    clearable
                    @click:clear="userForm.organization = null"
                  ></v-select>
                </template>
              </v-col>
              <template v-if="!editedUser">
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="userForm.password"
                    label="Mot de passe"
                    type="password"
                    required
                    autocomplete="new-password"
                    :rules="[rules.required, rules.password]"
                    hint="Minimum 8 caractères, incluant majuscules, minuscules et chiffres"
                    persistent-hint
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
<<<<<<< HEAD
                    v-model="organizationForm.phone"
                    label="Téléphone"
                    required
                    :rules="[v => !!v || 'Le téléphone est requis']"
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
=======
                    v-model="userForm.password_confirmation"
                    label="Confirmer le mot de passe"
                    type="password"
                    required
                    autocomplete="new-password"
                    :rules="[rules.required, rules.passwordMatch]"
                  ></v-text-field>
                </v-col>
              </template>
            </v-row>
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
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
<<<<<<< HEAD
import { ref, onMounted, watch } from 'vue'
=======
import { ref, onMounted, computed, watch } from 'vue'
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'AdminUsersView',
  setup() {
    const authStore = useAuthStore()
    const loading = ref(false)
    const saving = ref(false)
    const search = ref('')
    const showCreateDialog = ref(false)
    const form = ref(null)
    const editedItem = ref(null)
    const currentView = ref('users')
    const currentUser = ref(null)
    const showPasswordFields = ref(false)
    
<<<<<<< HEAD
    const userHeaders = ref([
      { title: 'Nom', align: 'start', key: 'fullName' },
=======
    const rules = {
      required: v => !!v || 'Ce champ est requis',
      email: v => /.+@.+\..+/.test(v) || 'Veuillez entrer une adresse courriel valide',
      password: v => {
        const hasMinLength = v && v.length >= 8
        const hasUpperCase = /[A-Z]/.test(v)
        const hasLowerCase = /[a-z]/.test(v)
        const hasNumber = /[0-9]/.test(v)
        return (hasMinLength && hasUpperCase && hasLowerCase && hasNumber) || 
          'Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule et un chiffre'
      },
      passwordMatch: v => v === userForm.value.password || 'Les mots de passe ne correspondent pas'
    }

    const headers = ref([
      { title: 'Nom', align: 'start', key: 'full_name' },
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
      { title: 'Courriel', key: 'email' },
      { title: 'Rôle', key: 'role', align: 'center' },
      { title: 'Franchise', key: 'organization_name' },
      { title: 'Statut', key: 'is_active', align: 'center' },
      { title: 'Actions', key: 'actions', align: 'end', sortable: false }
    ])

    const organizationHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', key: 'contact_email' },
      { title: 'Téléphone', key: 'phone' },
      { title: 'Ville', key: 'city' },
      { title: 'Statut', key: 'status', align: 'center' },
      { title: 'Actions', key: 'actions', align: 'end', sortable: false }
    ])

    const users = ref([])
    const organizations = ref([])
    const roles = ['SUPER_ADMIN', 'MANAGER', 'EMPLOYEE']
    
    const roleLabels = {
      'SUPER_ADMIN': 'Super Administrateur',
      'MANAGER': 'Gestionnaire',
      'EMPLOYEE': 'Employé'
    }

    const userForm = ref({
      first_name: '',
      last_name: '',
      email: '',
      username: '',
      role: '',
<<<<<<< HEAD
      organization: null,
      password: '',
      confirm_password: ''
=======
      organization: '',
      password: '',
      password_confirmation: ''
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
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
        const response = await api.get('/users/')
        console.log('Données utilisateurs reçues:', response.data)
<<<<<<< HEAD
        users.value = response.data.results || []
=======
        // Transformer les données pour l'affichage
        users.value = (response.data.results || []).map(user => ({
          id: user.id,
          full_name: `${user.first_name} ${user.last_name}`.trim() || user.email,
          email: user.email,
          role: user.role || 'EMPLOYEE',
          organization_name: user.organization?.name || '-',
          is_active: user.is_active ?? true,
          // Garder les données originales pour l'édition
          first_name: user.first_name,
          last_name: user.last_name,
          organization: user.organization?.id,
          username: user.username
        }))
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
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

<<<<<<< HEAD
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
=======
    const editUser = (user) => {
      userForm.value = {
        first_name: user.first_name,
        last_name: user.last_name,
        email: user.email,
        username: user.username,
        role: user.role,
        organization: user.role === 'SUPER_ADMIN' ? null : user.organization,
        password: '',
        password_confirmation: ''
      }
      editedUser.value = user
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
      showCreateDialog.value = true
    }

    const toggleUserStatus = async (user) => {
<<<<<<< HEAD
      if (isCurrentUser(user)) {
        return // Empêcher la désactivation si c'est l'utilisateur courant
      }
=======
      // Empêcher la désactivation de son propre compte
      if (user.id === authStore.user?.id) {
        console.warn('Un utilisateur ne peut pas désactiver son propre compte')
        return
      }

>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
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

<<<<<<< HEAD
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
      return editedItem.value ? 'Modifier la franchise' : 'Nouvelle franchise'
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
        if (currentView.value === 'users') {
          const userData = { ...userForm.value }
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
        } else {
          if (editedItem.value) {
            await api.put(`/organizations/${editedItem.value.id}/`, organizationForm.value)
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
=======
    // Computed property pour vérifier si un utilisateur est l'utilisateur courant
    const isCurrentUser = computed(() => {
      return (userId) => userId === authStore.user?.id
    })

    const handleRoleChange = (newRole) => {
      if (newRole === 'SUPER_ADMIN') {
        userForm.value.organization = null
      } else if (!userForm.value.organization && organizations.value.length > 0) {
        userForm.value.organization = organizations.value[0].id
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
      }
    }

    const resetForm = () => {
<<<<<<< HEAD
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
          confirm_password: ''
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
=======
      userForm.value = {
        first_name: '',
        last_name: '',
        email: '',
        username: '',
        role: '',
        organization: null,
        password: '',
        password_confirmation: ''
      }
    }

    const showCreateNewUserDialog = () => {
      editedUser.value = null
      resetForm()
      showCreateDialog.value = true
    }

    const saveUser = async () => {
      try {
        const { valid } = await form.value.validate()
        if (!valid) {
          console.log('Formulaire invalide')
          alert('Veuillez remplir tous les champs requis')
          return
        }

        const userData = {
          first_name: userForm.value.first_name,
          last_name: userForm.value.last_name,
          email: userForm.value.email,
          username: userForm.value.username || userForm.value.email.split('@')[0],
          role: userForm.value.role,
          organization: userForm.value.role === 'SUPER_ADMIN' ? null : userForm.value.organization,
        }

        // Ajouter le mot de passe uniquement lors de la création
        if (!editedUser.value) {
          userData.password = userForm.value.password
          userData.password_confirmation = userForm.value.password_confirmation
        }

        console.log('Données à envoyer:', userData)

        if (editedUser.value) {
          // Mise à jour d'un utilisateur existant
          const userId = editedUser.value.id
          console.log(`Mise à jour de l'utilisateur ${userId}:`, userData)
          try {
            const response = await api.put(`/users/${userId}/`, userData)
            console.log('Réponse de mise à jour:', response.data)
            Object.assign(editedUser.value, response.data)
          } catch (error) {
            console.error('Erreur lors de la mise à jour:', error.response?.data || error.message)
            let errorMessage = ''
            if (error.response?.data) {
              const errors = error.response.data
              errorMessage = Object.entries(errors)
                .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
                .join('\n')
            } else {
              errorMessage = error.message
            }
            alert(`Erreur lors de la mise à jour: ${errorMessage}`)
            return
          }
        } else {
          // Création d'un nouvel utilisateur
          console.log('Création d\'un nouvel utilisateur:', userData)
          try {
            const response = await api.post('/users/', userData)
            console.log('Réponse de création:', response.data)
            users.value.push(response.data)
          } catch (error) {
            console.error('Erreur lors de la création:', error.response?.data || error.message)
            let errorMessage = ''
            if (error.response?.data) {
              const errors = error.response.data
              errorMessage = Object.entries(errors)
                .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
                .join('\n')
            } else {
              errorMessage = error.message
            }
            alert(`Erreur lors de la création: ${errorMessage}`)
            return
          }
        }

        showCreateDialog.value = false
        editedUser.value = null
        resetForm()
      } catch (error) {
        console.error('Erreur lors de la sauvegarde:', error)
        alert('Une erreur est survenue lors de la sauvegarde')
      }
    }

    // Watcher pour le changement de rôle
    watch(() => userForm.value.role, (newRole) => {
      handleRoleChange(newRole)
    }, { immediate: true })
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f

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
<<<<<<< HEAD
      toggleOrganizationStatus,
      saveItem,
      getDialogTitle,
      closeDialog,
      onDialogClose,
      currentUser,
      isCurrentUser,
      showPasswordFields,
      passwordRules,
      confirmPasswordRules,
      editedItem
=======
      saveUser,
      rules,
      editedUser,
      isCurrentUser,
      showCreateNewUserDialog,
      resetForm,
      handleRoleChange
>>>>>>> c428db7b2297cd863d61b58d609607168d30704f
    }
  }
}
</script>

<style scoped>
.v-btn-toggle {
  background-color: rgba(var(--v-theme-surface-variant), 0.08);
  border-radius: 8px;
}
</style> 