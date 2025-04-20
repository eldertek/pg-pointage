import { describe, it, expect, vi } from 'vitest'
import { useNotification } from '../useNotification'

describe('useNotification', () => {
  it('initializes with default values', () => {
    const { notification } = useNotification()
    
    expect(notification.value).toEqual({
      show: false,
      text: '',
      color: 'success',
      timeout: 3000
    })
  })

  it('shows success notification with correct message', () => {
    const { notification, showSuccess } = useNotification()
    
    showSuccess('Operation successful')
    
    expect(notification.value).toEqual({
      show: true,
      text: 'Operation successful',
      color: 'success',
      timeout: 3000
    })
  })

  it('shows error notification with correct message', () => {
    const { notification, showError } = useNotification()
    
    showError('Operation failed')
    
    expect(notification.value).toEqual({
      show: true,
      text: 'Operation failed',
      color: 'error',
      timeout: 3000
    })
  })

  it('shows warning notification with correct message', () => {
    const { notification, showWarning } = useNotification()
    
    showWarning('Warning message')
    
    expect(notification.value).toEqual({
      show: true,
      text: 'Warning message',
      color: 'warning',
      timeout: 3000
    })
  })

  it('allows custom timeout', () => {
    const { notification, showSuccess } = useNotification()
    
    showSuccess('Custom timeout', 5000)
    
    expect(notification.value).toEqual({
      show: true,
      text: 'Custom timeout',
      color: 'success',
      timeout: 5000
    })
  })

  it('can hide notification', () => {
    const { notification, showSuccess, hideNotification } = useNotification()
    
    showSuccess('Test')
    hideNotification()
    
    expect(notification.value.show).toBe(false)
  })
}) 