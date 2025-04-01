<template>
  <!-- No changes to template section -->
</template>

<script>
import sitesApi from '../services/sitesApi';

export default {
  // No changes to component options

  methods: {
    async fetchSiteDetails() {
      try {
        const [siteResponse, employeesResponse, schedulesResponse] = await Promise.all([
          sitesApi.getSite(this.siteId),
          sitesApi.getSiteEmployees(this.siteId),
          sitesApi.getSiteSchedules(this.siteId)
        ]);

        this.site = siteResponse.data;
        this.employees = employeesResponse.data.results;
        this.schedules = schedulesResponse.data.results;
      } catch (error) {
        console.error('Erreur lors du chargement des détails du site:', error);
        this.$toast.error('Erreur lors du chargement des détails du site');
      }
    },

    async assignEmployeesToSchedule(scheduleId: number, employeeIds: number[]) {
      try {
        await sitesApi.assignEmployeesToSchedule(this.siteId, scheduleId, employeeIds);
        this.$toast.success('Employés assignés avec succès');
        await this.fetchSiteDetails();
      } catch (error) {
        console.error('Erreur lors de l\'assignation des employés:', error);
        this.$toast.error('Erreur lors de l\'assignation des employés');
      }
    },

    async fetchScheduleDetails(scheduleId: number) {
      try {
        const response = await sitesApi.getScheduleDetails(this.siteId, scheduleId);
        this.selectedSchedule = response.data;
      } catch (error) {
        console.error('Erreur lors du chargement des détails du planning:', error);
        this.$toast.error('Erreur lors du chargement des détails du planning');
      }
    }
  }
};
</script>

<style>
  /* No changes to style section */
</style> 