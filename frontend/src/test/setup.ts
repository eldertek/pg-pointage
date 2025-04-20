import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// Mock des composants globaux
config.global.components = {
  'v-icon': {
    template: '<i class="v-icon">{{ $slots.default?.()?.[0]?.children }}</i>'
  }
}

// Mock des plugins
config.global.plugins = []

// Mock des directives
config.global.directives = {
  ripple: {}
}

// Mock des propriétés window qui n'existent pas dans jsdom
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
})

// Mock de ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock de fetch
global.fetch = vi.fn()

// Mock de localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn(),
  removeItem: vi.fn(),
  key: vi.fn(),
  length: 0
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock des traductions
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
    locale: { value: 'fr' }
  })
})) 