<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Gestion des utilisateurs</h1>
      <v-btn color="primary" prepend-icon="mdi-account-plus" @click="showCreateNewUserDialog">
        Nouvel utilisateur
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

      <v-data-table
        :headers="headers"
        :items="users"
        :search="search"
        :loading="loading"
        :no-data-text="'Aucun utilisateur trouvé'"
        :loading-text="'Chargement des utilisateurs...'"
        :items-per-page-text="'Lignes par page'"
      >
        <template #[`item.role`]="{ item }">
          <v-chip
            :color="getRoleColor(item.role)"
            size="small"
          >
            {{ roleLabels[item.role] || item.role }}
          </v-chip>
        </template>

        <template #[`item.is_active`]="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'error'"
            size="small"
          >
            {{ item.is_active ? 'Actif' : 'Inactif' }}
          </v-chip>
        </template>

        <template #[`item.actions`]="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click="editUser(item)"
            :title="'Modifier ' + item.full_name"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            :color="item.is_active ? 'error' : 'success'"
            @click="toggleUserStatus(item)"
            :disabled="isCurrentUser(item.id)"
            :title="isCurrentUser(item.id) 
              ? 'Vous ne pouvez pas modifier votre propre statut'
              : (item.is_active ? 'Désactiver ' : 'Activer ') + item.full_name"
          >
            <v-icon>{{ item.is_active ? 'mdi-account-off' : 'mdi-account-check' }}</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog pour créer/éditer un utilisateur -->
    <v-dialog v-model="showCreateDialog" max-width="600px">
      <v-card>
        <v-card-title>
          {{ editedUser ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur' }}
        </v-card-title>
        <v-card-text>
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
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
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
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="text" @click="showCreateDialog = false">Annuler</v-btn>
          <v-btn color="primary" @click="saveUser" :loading="saving">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
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
    const editedUser = ref(null)
    
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
      { title: 'Courriel', key: 'email' },
      { title: 'Rôle', key: 'role', align: 'center' },
      { title: 'Franchise', key: 'organization_name' },
      { title: 'Statut', key: 'is_active', align: 'center' },
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
      organization: '',
      password: '',
      password_confirmation: ''
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
        const response = await api.get('/users/')
        console.log('Données utilisateurs reçues:', response.data)
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
      } catch (error) {
        console.error('Erreur lors du chargement des utilisateurs:', error)
      } finally {
        loading.value = false
      }
    }

    const fetchOrganizations = async () => {
      try {
        const response = await api.get('/organizations/')
        console.log('Données organisations reçues:', response.data)
        organizations.value = response.data.results || []
      } catch (error) {
        console.error('Erreur lors du chargement des organisations:', error)
      }
    }

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
      showCreateDialog.value = true
    }

    const toggleUserStatus = async (user) => {
      // Empêcher la désactivation de son propre compte
      if (user.id === authStore.user?.id) {
        console.warn('Un utilisateur ne peut pas désactiver son propre compte')
        return
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

    // Computed property pour vérifier si un utilisateur est l'utilisateur courant
    const isCurrentUser = computed(() => {
      return (userId) => userId === authStore.user?.id
    })

    const handleRoleChange = (newRole) => {
      if (newRole === 'SUPER_ADMIN') {
        userForm.value.organization = null
      } else if (!userForm.value.organization && organizations.value.length > 0) {
        userForm.value.organization = organizations.value[0].id
      }
    }

    const resetForm = () => {
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

    onMounted(() => {
      fetchUsers()
      fetchOrganizations()
    })

    return {
      loading,
      saving,
      search,
      headers,
      users,
      organizations,
      roles,
      roleLabels,
      showCreateDialog,
      form,
      userForm,
      getRoleColor,
      editUser,
      toggleUserStatus,
      saveUser,
      rules,
      editedUser,
      isCurrentUser,
      showCreateNewUserDialog,
      resetForm,
      handleRoleChange
    }
  }
}
</script> 