import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { createRouter, createWebHistory } from 'vue-router'
import SiteDetail from '../SiteDetail.vue'
import { sitesApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

// Mock des dépendances
vi.mock('@/services/api', () => ({
  sitesApi: {
    getSite: vi.fn(),
    getSiteStatistics: vi.fn(),
    getSiteEmployees: vi.fn(),
    getSitePlannings: vi.fn(),
    getSitePointages: vi.fn(),
    getSiteAnomalies: vi.fn(),
    getSiteReports: vi.fn(),
    updateSite: vi.fn(),
    deleteSite: vi.fn()
  }
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    user: {
      role: 'ADMIN'
    }
  }))
}))

const vuetify = createVuetify({ components, directives })

// Configuration du router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/dashboard/sites/:id',
      name: 'SiteDetail',
      component: SiteDetail
    }
  ]
})

describe('SiteDetail', () => {
  const mockSite = {
    id: 1,
    name: 'Test Site',
    address: '123 Test St',
    postal_code: '75000',
    city: 'Paris',
    country: 'France',
    is_active: true,
    nfc_id: 'NFC123',
    manager_name: 'John Doe',
    organization_name: 'Test Org',
    late_margin: 15
  }

  const mockStats = {
    total_employees: 10,
    total_hours: 100,
    anomalies: 5
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock des réponses API
    sitesApi.getSite.mockResolvedValue({ data: mockSite })
    sitesApi.getSiteStatistics.mockResolvedValue({ data: mockStats })
    sitesApi.getSiteEmployees.mockResolvedValue({ data: { results: [] } })
    sitesApi.getSitePlannings.mockResolvedValue({ data: { results: [] } })
    sitesApi.getSitePointages.mockResolvedValue({ data: { results: [] } })
    sitesApi.getSiteAnomalies.mockResolvedValue({ data: { results: [] } })
    sitesApi.getSiteReports.mockResolvedValue({ data: { results: [] } })
  })

  const mountComponent = () => {
    return mount(SiteDetail, {
      global: {
        plugins: [vuetify, router],
        stubs: {
          'router-link': true,
          'router-view': true
        }
      }
    })
  }

  it('loads site data on mount', async () => {
    const wrapper = mountComponent()
    await router.isReady()
    
    expect(sitesApi.getSite).toHaveBeenCalled()
    expect(sitesApi.getSiteStatistics).toHaveBeenCalled()
  })

  it('displays site information correctly', async () => {
    const wrapper = mountComponent()
    await router.isReady()
    
    // Vérifier les informations de base
    expect(wrapper.text()).toContain(mockSite.name)
    expect(wrapper.text()).toContain(mockSite.manager_name)
    expect(wrapper.text()).toContain(mockSite.organization_name)
  })

  it('shows all tabs', async () => {
    const wrapper = mountComponent()
    await router.isReady()
    
    const tabs = wrapper.findAll('.v-tab')
    expect(tabs).toHaveLength(6) // Informations, Employés, Plannings, Pointages, Anomalies, Rapports
  })

  it('loads tab data when switching tabs', async () => {
    const wrapper = mountComponent()
    await router.isReady()
    
    // Cliquer sur l'onglet Employés
    await wrapper.findAll('.v-tab')[1].trigger('click')
    expect(sitesApi.getSiteEmployees).toHaveBeenCalled()
    
    // Cliquer sur l'onglet Plannings
    await wrapper.findAll('.v-tab')[2].trigger('click')
    expect(sitesApi.getSitePlannings).toHaveBeenCalled()
  })

  it('shows edit and delete buttons for admin users', async () => {
    const wrapper = mountComponent()
    await router.isReady()
    
    const editButton = wrapper.find('[data-test="edit-button"]')
    const deleteButton = wrapper.find('[data-test="delete-button"]')
    
    expect(editButton.exists()).toBe(true)
    expect(deleteButton.exists()).toBe(true)
  })

  it('hides edit and delete buttons for non-admin users', async () => {
    vi.mocked(useAuthStore).mockImplementation(() => ({
      user: {
        role: 'USER'
      }
    }))
    
    const wrapper = mountComponent()
    await router.isReady()
    
    const editButton = wrapper.find('[data-test="edit-button"]')
    const deleteButton = wrapper.find('[data-test="delete-button"]')
    
    expect(editButton.exists()).toBe(false)
    expect(deleteButton.exists()).toBe(false)
  })

  it('generates and displays QR code', async () => {
    const wrapper = mountComponent()
    await router.isReady()
    
    const qrCodeImage = wrapper.find('.qr-code-container img')
    expect(qrCodeImage.exists()).toBe(true)
  })

  it('handles QR code download', async () => {
    const wrapper = mountComponent()
    await router.isReady()
    
    const downloadButton = wrapper.find('[data-test="download-qr"]')
    await downloadButton.trigger('click')
    
    // Vérifier que le lien de téléchargement a été créé
    expect(document.querySelector('a[download]')).toBeTruthy()
  })
}) 