import { describe, it, expect, vi } from 'vitest'
import { useConfirmDialog } from '../useConfirmDialog'

describe('useConfirmDialog', () => {
  it('initializes with default values', () => {
    const { dialog } = useConfirmDialog()
    
    expect(dialog.value).toEqual({
      show: false,
      title: '',
      message: '',
      confirmText: '',
      cancelText: '',
      confirmColor: 'primary',
      onConfirm: expect.any(Function),
      onCancel: expect.any(Function)
    })
  })

  it('shows dialog with correct options', () => {
    const { dialog, showConfirmDialog } = useConfirmDialog()
    const mockOnConfirm = vi.fn()
    
    showConfirmDialog({
      title: 'Test Title',
      message: 'Test Message',
      confirmText: 'Confirm',
      cancelText: 'Cancel',
      confirmColor: 'error',
      onConfirm: mockOnConfirm
    })
    
    expect(dialog.value).toEqual({
      show: true,
      title: 'Test Title',
      message: 'Test Message',
      confirmText: 'Confirm',
      cancelText: 'Cancel',
      confirmColor: 'error',
      onConfirm: mockOnConfirm,
      onCancel: expect.any(Function)
    })
  })

  it('calls onConfirm and closes dialog when confirmed', () => {
    const { dialog, showConfirmDialog } = useConfirmDialog()
    const mockOnConfirm = vi.fn()
    
    showConfirmDialog({
      title: 'Test',
      message: 'Test',
      onConfirm: mockOnConfirm
    })
    
    dialog.value.onConfirm()
    
    expect(mockOnConfirm).toHaveBeenCalled()
    expect(dialog.value.show).toBe(false)
  })

  it('closes dialog when cancelled', () => {
    const { dialog, showConfirmDialog } = useConfirmDialog()
    
    showConfirmDialog({
      title: 'Test',
      message: 'Test'
    })
    
    dialog.value.onCancel()
    
    expect(dialog.value.show).toBe(false)
  })
}) 