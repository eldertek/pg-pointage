import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DetailActions from '../DetailActions.vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({ components, directives })

describe('DetailActions', () => {
  const mockItem = {
    id: 1,
    is_active: true,
    name: 'Test Item'
  }

  const mockConfig = {
    type: 'site',
    baseRoute: '/dashboard/sites',
    toggleStatus: vi.fn(),
    deleteItem: vi.fn()
  }

  const mountComponent = () => {
    return mount(DetailActions, {
      props: {
        item: mockItem,
        config: mockConfig
      },
      global: {
        plugins: [vuetify],
        stubs: {
          'router-link': true
        }
      }
    })
  }

  it('renders all action buttons', () => {
    const wrapper = mountComponent()
    
    // Vérifie la présence des boutons
    expect(wrapper.find('[data-test="view-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="edit-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="toggle-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="delete-button"]').exists()).toBe(true)
  })

  it('calls toggleStatus when toggle button is clicked', async () => {
    const wrapper = mountComponent()
    
    await wrapper.find('[data-test="toggle-button"]').trigger('click')
    expect(mockConfig.toggleStatus).toHaveBeenCalledWith(mockItem)
  })

  it('calls deleteItem when delete button is clicked', async () => {
    const wrapper = mountComponent()
    
    await wrapper.find('[data-test="delete-button"]').trigger('click')
    expect(mockConfig.deleteItem).toHaveBeenCalledWith(mockItem)
  })

  it('shows correct toggle button icon based on item status', () => {
    const wrapper = mountComponent()
    
    // Pour un item actif
    expect(wrapper.find('[data-test="toggle-button"] .v-icon').text()).toBe('mdi-domain-off')
    
    // Pour un item inactif
    wrapper.setProps({
      item: { ...mockItem, is_active: false }
    })
    expect(wrapper.find('[data-test="toggle-button"] .v-icon').text()).toBe('mdi-domain')
  })

  it('generates correct view and edit routes', () => {
    const wrapper = mountComponent()
    
    const viewLink = wrapper.find('[data-test="view-button"]')
    const editLink = wrapper.find('[data-test="edit-button"]')
    
    expect(viewLink.attributes('to')).toBe('/dashboard/sites/1')
    expect(editLink.attributes('to')).toBe('/dashboard/sites/1/edit')
  })
}) 