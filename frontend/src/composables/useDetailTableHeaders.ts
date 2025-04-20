import { useI18n } from 'vue-i18n'
import type { TableHeader } from '@/components/common/DataTable.vue'

export function useDetailTableHeaders() {
  const { t } = useI18n()

  const sitesHeaders: TableHeader[] = [
    { title: t('common.name'), key: 'name' },
    { title: t('common.address'), key: 'address' },
    { title: t('common.organization'), key: 'organization_name' },
    { title: t('common.actions'), key: 'actions', sortable: false }
  ]

  const planningsHeaders: TableHeader[] = [
    { title: t('common.site'), key: 'site_name', align: 'start' },
    { title: t('common.employee'), key: 'employees', align: 'start' },
    { title: t('common.type'), key: 'schedule_type', align: 'start' },
    { title: t('common.actions'), key: 'actions', sortable: false, align: 'end' }
  ]

  const pointagesHeaders: TableHeader[] = [
    { title: t('common.site'), key: 'site_name' },
    { title: t('timesheets.entryType'), key: 'entry_type' },
    { title: t('timesheets.dateTime', 'Date/Heure'), key: 'timestamp' }
  ]

  const anomaliesHeaders: TableHeader[] = [
    { title: t('common.site'), key: 'site_name' },
    { title: t('common.type'), key: 'type' },
    { title: t('timesheets.dateTime', 'Date/Heure'), key: 'created_at' },
    { title: t('common.status'), key: 'status' }
  ]

  const reportsHeaders: TableHeader[] = [
    { title: t('common.name'), key: 'name' },
    { title: t('common.type'), key: 'type' },
    { title: t('reports.creationDate', 'Date de création'), key: 'created_at' },
    { title: t('common.actions'), key: 'actions', sortable: false }
  ]

  const employeesHeaders: TableHeader[] = [
    { title: t('common.name'), key: 'employee_name' },
    { title: t('common.actions'), key: 'actions', sortable: false }
  ]

  return {
    sitesHeaders,
    planningsHeaders,
    pointagesHeaders,
    anomaliesHeaders,
    reportsHeaders,
    employeesHeaders
  }
}