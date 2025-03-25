import Toast, { type PluginOptions } from 'vue-toastification'
import 'vue-toastification/dist/index.css'

const options: PluginOptions = {
  position: 'top-right',
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false,
  transition: 'Vue-Toastification__bounce',
  maxToasts: 20,
  newestOnTop: true,
  toastClassName: 'custom-toast',
  bodyClassName: ['custom-toast-body'],
  containerClassName: 'custom-toast-container',
  // Personnalisation des couleurs selon la charte graphique
  toastDefaults: {
    success: {
      containerClassName: 'success-toast',
      bodyClassName: ['success-toast-body'],
      toastClassName: 'success-toast'
    },
    error: {
      containerClassName: 'error-toast',
      bodyClassName: ['error-toast-body'],
      toastClassName: 'error-toast'
    },
    warning: {
      containerClassName: 'warning-toast',
      bodyClassName: ['warning-toast-body'],
      toastClassName: 'warning-toast'
    },
    info: {
      containerClassName: 'info-toast',
      bodyClassName: ['info-toast-body'],
      toastClassName: 'info-toast'
    }
  }
}

export { Toast, options } 