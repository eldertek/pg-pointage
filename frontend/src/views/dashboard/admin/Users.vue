<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Gestion des Utilisateurs</h1>
      <v-btn color="primary" prepend-icon="mdi-account-plus" @click="showCreateDialog = true">
        Nouvel Utilisateur
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
      >
        <template #[`item.role`]="{ item }">
          <v-chip
            :color="getRoleColor(item.raw.role)"
            size="small"
          >
            {{ item.raw.role }}
          </v-chip>
        </template>

        <template #[`item.is_active`]="{ item }">
          <v-chip
            :color="item.raw.is_active ? 'success' : 'error'"
            size="small"
          >
            {{ item.raw.is_active ? 'Actif' : 'Inactif' }}
          </v-chip>
        </template>

        <template #[`item.actions`]="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click="editUser(item.raw)"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            :color="item.raw.is_active ? 'error' : 'success'"
            @click="toggleUserStatus(item.raw)"
          >
            <v-icon>{{ item.raw.is_active ? 'mdi-account-off' : 'mdi-account-check' }}</v-icon>
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
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="userForm.last_name"
                  label="Nom"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="userForm.email"
                  label="Email"
                  type="email"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="userForm.role"
                  :items="roles"
                  label="Rôle"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="userForm.organization"
                  :items="organizations"
                  label="Organisation"
                  item-title="name"
                  item-value="id"
                  :disabled="userForm.role === 'SUPER_ADMIN'"
                ></v-select>
              </v-col>
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
import { ref, onMounted } from 'vue'
import api from '@/services/api'

export default {
  name: 'AdminUsersView',
  setup() {
    const loading = ref(false)
    const saving = ref(false)
    const search = ref('')
    const showCreateDialog = ref(false)
    const form = ref(null)
    const editedUser = ref(null)
    
    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Courriel', key: 'email' },
      { title: 'Rôle', key: 'role', align: 'center' },
      { title: 'Organisation', key: 'organization' },
      { title: 'Statut', key: 'is_active', align: 'center' },
      { title: 'Actions', key: 'actions', align: 'end', sortable: false }
    ])

    const users = ref([])
    const organizations = ref([])
    const roles = ['SUPER_ADMIN', 'MANAGER', 'EMPLOYEE']

    const userForm = ref({
      first_name: '',
      last_name: '',
      email: '',
      role: '',
      organization: null
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
        // Extraire le tableau results de la réponse paginée
        users.value = response.data.results || []
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
      editedUser.value = user
      userForm.value = { ...user }
      showCreateDialog.value = true
    }

    const toggleUserStatus = async (user) => {
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

    const saveUser = async () => {
      saving.value = true
      try {
        if (editedUser.value) {
          console.log('Mise à jour utilisateur:', userForm.value)
          await api.put(`/users/${editedUser.value.id}/`, userForm.value)
        } else {
          console.log('Création utilisateur:', userForm.value)
          await api.post('/users/', userForm.value)
        }
        await fetchUsers()
        showCreateDialog.value = false
        editedUser.value = null
        userForm.value = {
          first_name: '',
          last_name: '',
          email: '',
          role: '',
          organization: null
        }
      } catch (error) {
        console.error('Erreur lors de l\'enregistrement:', error)
      } finally {
        saving.value = false
      }
    }

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
      showCreateDialog,
      form,
      userForm,
      getRoleColor,
      editUser,
      toggleUserStatus,
      saveUser
    }
  }
}
</script> 