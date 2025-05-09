import { api } from '../api'
import type { Organization } from '@/types/api'

interface OrganizationResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Organization[];
}

export const organizationsApi = {
  // Organisations
  getAllOrganizations: (params?: any) => {
    return api.get<OrganizationResponse>('/organizations/', { params })
  },

  getOrganization: (id: number) => {
    return api.get<Organization>(`/organizations/${id}/`)
  },

  createOrganization: (data: Partial<Organization>) => {
    return api.post<Organization>('/organizations/', data)
  },

  updateOrganization: (id: number, data: Partial<Organization>) => {
    return api.patch<Organization>(`/organizations/${id}/`, data)
  },

  deleteOrganization: (id: number) => {
    return api.delete(`/organizations/${id}/`)
  },

  toggleOrganizationStatus: (id: number, status: boolean) => api.patch(`/organizations/${id}/`, { is_active: status }),

  // Utilisateurs de l'organisation
  getOrganizationUsers: (id: number, params?: any) => api.get(`/organizations/${id}/users/`, { params }),
  getUnassignedEmployees: (id: number, params?: any) => api.get(`/organizations/${id}/unassigned-employees/`, { params }),
  updateOrganizationUsers: (organizationId: number, users: number[]) => 
    api.patch(`/organizations/${organizationId}/`, { users }),

  // Sites de l'organisation
  getOrganizationSites: (id: number, params?: any) => api.get(`/organizations/${id}/sites/`, { params }),
  getUnassignedSites: (id: number) => api.get(`/organizations/${id}/unassigned-sites/`),
  assignSiteToOrganization: (id: number, siteId: number) => api.post(`/organizations/${id}/assign-site/`, { site_id: siteId }),

  // Statistiques
  getOrganizationStatistics: (id: number) => api.get(`/organizations/${id}/statistics/`),

  // Autres données liées
  getOrganizationTimesheets: (id: number, params?: any) => api.get(`/organizations/${id}/timesheets/`, { params }),
  getOrganizationAnomalies: (id: number, params?: any) => api.get(`/organizations/${id}/anomalies/`, { params }),
  getOrganizationReports: (id: number, params?: any) => api.get(`/organizations/${id}/reports/`, { params })
} 