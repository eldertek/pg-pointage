import { ref } from 'vue'

export interface DialogState {
  show: boolean
  title: string
  message: string
  confirmText: string
  cancelText: string
  confirmColor: string
  loading: boolean
  onConfirm: () => Promise<void>
}

const dialogState = ref<DialogState>({
  show: false,
  title: '',
  message: '',
  confirmText: 'Confirmer',
  cancelText: 'Annuler',
  confirmColor: 'primary',
  loading: false,
  onConfirm: async () => {}
})

export const useConfirmDialog = () => {
  const showConfirmDialog = async ({
    title,
    message,
    confirmText = 'Confirmer',
    cancelText = 'Annuler',
    confirmColor = 'primary',
    onConfirm
  }: Partial<DialogState> & { onConfirm: () => Promise<void> }) => {
    dialogState.value = {
      show: true,
      title,
      message,
      confirmText,
      cancelText,
      confirmColor,
      loading: false,
      onConfirm
    }
  }

  const handleConfirm = async () => {
    dialogState.value.loading = true
    try {
      await dialogState.value.onConfirm()
    } finally {
      dialogState.value.loading = false
      dialogState.value.show = false
    }
  }

  return {
    dialogState,
    showConfirmDialog,
    handleConfirm
  }
} 