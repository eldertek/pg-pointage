import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { RoleEnum } from '@/types/api'
import type { NavigationFailure } from 'vue-router'

export interface ActionButton {
  icon: string
  color: string
  tooltip: string
  action: (item: any) => void | Promise<void | NavigationFailure | undefined>
  visible: boolean
  route?: string
}

export interface ActionConfig {
  type: 'user' | 'site' | 'planning' | 'organization'
  baseRoute: string
  toggleStatus: (item: any) => Promise<void>
  deleteItem: (item: any) => Promise<void>
  editItem?: (item: any) => void
}

export function useDetailActions(config: ActionConfig) {
  const { t } = useI18n()
  const router = useRouter()
  const authStore = useAuthStore()

  const canEdit = computed(() => {
    const role = authStore.user?.role
    return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN || role === RoleEnum.MANAGER
  })

  const canCreateDelete = computed(() => {
    const role = authStore.user?.role
    return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN
  })

  const getStatusIcon = (item: any, type: string) => {
    if (type === 'user') {
      return item.is_active ? 'mdi-account-off' : 'mdi-account'
    }
    if (type === 'site') {
      return item.is_active ? 'mdi-domain-off' : 'mdi-domain'
    }
    if (type === 'organization') {
      return item.is_active ? 'mdi-domain-off' : 'mdi-domain'
    }
    return item.is_active ? 'mdi-calendar-remove' : 'mdi-calendar-check'
  }

  const getStatusTooltip = (item: any) => {
    return item.is_active ? t('common.deactivate') : t('common.activate')
  }

  const getDetailActions = (item: any): ActionButton[] => {
    const actions: ActionButton[] = [
      {
        icon: 'mdi-eye',
        color: 'primary',
        tooltip: t('common.viewDetails'),
        action: () => router.push(`${config.baseRoute}/${item.id}`),
        visible: true,
        route: `${config.baseRoute}/${item.id}`
      },
      {
        icon: 'mdi-pencil',
        color: 'primary',
        tooltip: t('common.edit'),
        action: () => {
          if (config.editItem) {
            config.editItem(item)
          } else {
            router.push(`${config.baseRoute}/${item.id}/edit`)
          }
        },
        visible: canEdit.value
      },
      {
        icon: getStatusIcon(item, config.type),
        color: 'warning',
        tooltip: getStatusTooltip(item),
        action: () => config.toggleStatus(item),
        visible: canCreateDelete.value
      },
      {
        icon: 'mdi-delete',
        color: 'error',
        tooltip: t('common.delete'),
        action: () => config.deleteItem(item),
        visible: canCreateDelete.value
      }
    ]

    return actions
  }

  return {
    getDetailActions,
    canEdit,
    canCreateDelete
  }
} 