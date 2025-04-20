import { describe, it, expect, vi } from 'vitest'
import { useDetailActions } from '../useDetailActions'
import { useRouter } from 'vue-router'
import { useConfirmDialog } from '../useConfirmDialog'
import { useNotification } from '../useNotification'

vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn()
  }))
}))

vi.mock('../useConfirmDialog', () => ({
  useConfirmDialog: vi.fn(() => ({
    showConfirmDialog: vi.fn()
  }))
}))

vi.mock('../useNotification', () => ({
  useNotification: vi.fn(() => ({
    showSuccess: vi.fn(),
    showError: vi.fn()
  }))
}))

describe('useDetailActions', () => {
  const mockItem = {
    id: 1,
    is_active: true,
    name: 'Test Item'
  }

  const mockApi = {
    updateItem: vi.fn(),
    deleteItem: vi.fn()
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('handles view action correctly', () => {
    const { handleView } = useDetailActions({
      baseRoute: '/dashboard/items',
      api: mockApi
    })
    
    handleView(mockItem)
    
    expect(useRouter().push).toHaveBeenCalledWith('/dashboard/items/1')
  })

  it('handles edit action correctly', () => {
    const { handleEdit } = useDetailActions({
      baseRoute: '/dashboard/items',
      api: mockApi
    })
    
    handleEdit(mockItem)
    
    expect(useRouter().push).toHaveBeenCalledWith('/dashboard/items/1/edit')
  })

  it('shows confirmation dialog when toggling status', () => {
    const { handleToggleStatus } = useDetailActions({
      baseRoute: '/dashboard/items',
      api: mockApi
    })
    
    handleToggleStatus(mockItem)
    
    expect(useConfirmDialog().showConfirmDialog).toHaveBeenCalledWith(
      expect.objectContaining({
        title: expect.any(String),
        message: expect.any(String),
        confirmColor: expect.any(String)
      })
    )
  })

  it('shows confirmation dialog when deleting', () => {
    const { handleDelete } = useDetailActions({
      baseRoute: '/dashboard/items',
      api: mockApi
    })
    
    handleDelete(mockItem)
    
    expect(useConfirmDialog().showConfirmDialog).toHaveBeenCalledWith(
      expect.objectContaining({
        title: expect.any(String),
        message: expect.any(String),
        confirmColor: 'error'
      })
    )
  })

  it('calls API and shows success notification when toggling status', async () => {
    mockApi.updateItem.mockResolvedValue({ data: { ...mockItem, is_active: false } })
    
    const { toggleStatus } = useDetailActions({
      baseRoute: '/dashboard/items',
      api: mockApi
    })
    
    await toggleStatus(mockItem)
    
    expect(mockApi.updateItem).toHaveBeenCalledWith(mockItem.id, { is_active: false })
    expect(useNotification().showSuccess).toHaveBeenCalled()
  })

  it('shows error notification when API call fails', async () => {
    mockApi.updateItem.mockRejectedValue(new Error('API Error'))
    
    const { toggleStatus } = useDetailActions({
      baseRoute: '/dashboard/items',
      api: mockApi
    })
    
    await toggleStatus(mockItem)
    
    expect(useNotification().showError).toHaveBeenCalled()
  })
}) 