<template>
  <div v-if="errors && Object.keys(errors).length > 0" class="form-errors">
    <v-alert
      type="error"
      variant="tonal"
      class="mb-4"
    >
      <div class="d-flex align-center mb-2">
        <v-icon icon="mdi-alert-circle" class="mr-2"></v-icon>
        <span>Veuillez corriger les erreurs suivantes :</span>
      </div>
      <ul class="mb-0 pl-4">
        <li v-for="(error, field) in errors" :key="field">
          <strong>{{ getFieldLabel(field) }} :</strong> {{ formatError(error) }}
        </li>
      </ul>
    </v-alert>
  </div>
</template>

<script setup lang="ts">
import { typography } from '@/styles/typography'

interface Props {
  errors?: Record<string, string[]>
}

const props = defineProps<Props>()

const fieldLabels: Record<string, string> = {
  username: 'Nom d\'utilisateur',
  password: 'Mot de passe',
  first_name: 'Prénom',
  last_name: 'Nom',
  email: 'Email',
  phone_number: 'Téléphone',
  role: 'Rôle',
  sites: 'Sites',
  name: 'Nom',
  phone: 'Téléphone',
  address: 'Adresse',
  country: 'Pays',
  postal_code: 'Code postal',
  city: 'Ville',
  contact_email: 'Email de contact',
  siret: 'Numéro SIRET',
  notes: 'Notes',
  is_active: 'Statut',
  scan_preference: 'Préférence de scan',
  simplified_mobile_view: 'Vue mobile simplifiée',
  organization: 'Organisation'
}

const getFieldLabel = (field: string): string => {
  return fieldLabels[field] || field
}

const formatError = (error: string | string[]): string => {
  if (Array.isArray(error)) {
    return error[0]
  }
  return error
}
</script>

<style scoped>
.form-errors {
  font-family: v-bind('typography.body.family');
  font-size: v-bind('typography.body.size');
  font-weight: v-bind('typography.body.weight');
  line-height: v-bind('typography.body.lineHeight');
}

.form-errors ul {
  margin: 0;
  padding-left: 1.5rem;
}

.form-errors li {
  margin-bottom: 0.25rem;
}

.form-errors li:last-child {
  margin-bottom: 0;
}

.form-errors strong {
  color: #00346E;
  font-weight: 600;
}
</style> 