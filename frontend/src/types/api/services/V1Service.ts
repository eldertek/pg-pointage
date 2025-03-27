/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Alert } from '../models/Alert';
import type { AlertRequest } from '../models/AlertRequest';
import type { Anomaly } from '../models/Anomaly';
import type { AnomalyRequest } from '../models/AnomalyRequest';
import type { CustomTokenObtainPairRequest } from '../models/CustomTokenObtainPairRequest';
import type { DashboardStats } from '../models/DashboardStats';
import type { EmployeeReport } from '../models/EmployeeReport';
import type { Organization } from '../models/Organization';
import type { OrganizationRequest } from '../models/OrganizationRequest';
import type { OrganizationStatistics } from '../models/OrganizationStatistics';
import type { PaginatedAlertList } from '../models/PaginatedAlertList';
import type { PaginatedAnomalyList } from '../models/PaginatedAnomalyList';
import type { PaginatedEmployeeReportList } from '../models/PaginatedEmployeeReportList';
import type { PaginatedOrganizationList } from '../models/PaginatedOrganizationList';
import type { PaginatedReportList } from '../models/PaginatedReportList';
import type { PaginatedScheduleDetailList } from '../models/PaginatedScheduleDetailList';
import type { PaginatedScheduleList } from '../models/PaginatedScheduleList';
import type { PaginatedSiteEmployeeList } from '../models/PaginatedSiteEmployeeList';
import type { PaginatedSiteList } from '../models/PaginatedSiteList';
import type { PaginatedTimesheetList } from '../models/PaginatedTimesheetList';
import type { PaginatedUserList } from '../models/PaginatedUserList';
import type { PatchedAlertRequest } from '../models/PatchedAlertRequest';
import type { PatchedAnomalyRequest } from '../models/PatchedAnomalyRequest';
import type { PatchedOrganizationRequest } from '../models/PatchedOrganizationRequest';
import type { PatchedScheduleRequest } from '../models/PatchedScheduleRequest';
import type { PatchedSiteEmployeeRequest } from '../models/PatchedSiteEmployeeRequest';
import type { PatchedSiteRequest } from '../models/PatchedSiteRequest';
import type { PatchedTimesheetRequest } from '../models/PatchedTimesheetRequest';
import type { PatchedUserProfileRequest } from '../models/PatchedUserProfileRequest';
import type { PatchedUserRequest } from '../models/PatchedUserRequest';
import type { Report } from '../models/Report';
import type { ReportGenerateRequest } from '../models/ReportGenerateRequest';
import type { ReportRequest } from '../models/ReportRequest';
import type { ScanAnomaliesRequest } from '../models/ScanAnomaliesRequest';
import type { Schedule } from '../models/Schedule';
import type { ScheduleDetail } from '../models/ScheduleDetail';
import type { ScheduleDetailRequest } from '../models/ScheduleDetailRequest';
import type { ScheduleRequest } from '../models/ScheduleRequest';
import type { Site } from '../models/Site';
import type { SiteEmployee } from '../models/SiteEmployee';
import type { SiteEmployeeRequest } from '../models/SiteEmployeeRequest';
import type { SiteRequest } from '../models/SiteRequest';
import type { Timesheet } from '../models/Timesheet';
import type { TimesheetCreate } from '../models/TimesheetCreate';
import type { TimesheetCreateRequest } from '../models/TimesheetCreateRequest';
import type { TimesheetReportGenerateRequest } from '../models/TimesheetReportGenerateRequest';
import type { TimesheetRequest } from '../models/TimesheetRequest';
import type { TokenRefresh } from '../models/TokenRefresh';
import type { TokenRefreshRequest } from '../models/TokenRefreshRequest';
import type { User } from '../models/User';
import type { UserChangePasswordRequest } from '../models/UserChangePasswordRequest';
import type { UserProfile } from '../models/UserProfile';
import type { UserProfileRequest } from '../models/UserProfileRequest';
import type { UserRegister } from '../models/UserRegister';
import type { UserRegisterRequest } from '../models/UserRegisterRequest';
import type { UserRequest } from '../models/UserRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class V1Service {
    /**
     * Vue pour lister les alertes
     * @param page A page number within the paginated result set.
     * @returns PaginatedAlertList
     * @throws ApiError
     */
    public static v1AlertsList(
        page?: number,
    ): CancelablePromise<PaginatedAlertList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/alerts/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour obtenir et mettre à jour une alerte
     * @param id
     * @returns Alert
     * @throws ApiError
     */
    public static v1AlertsRetrieve(
        id: number,
    ): CancelablePromise<Alert> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/alerts/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour obtenir et mettre à jour une alerte
     * @param id
     * @param requestBody
     * @returns Alert
     * @throws ApiError
     */
    public static v1AlertsUpdate(
        id: number,
        requestBody: AlertRequest,
    ): CancelablePromise<Alert> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/alerts/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir et mettre à jour une alerte
     * @param id
     * @param requestBody
     * @returns Alert
     * @throws ApiError
     */
    public static v1AlertsPartialUpdate(
        id: number,
        requestBody?: PatchedAlertRequest,
    ): CancelablePromise<Alert> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/alerts/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Obtenir les anomalies récentes
     * @returns Anomaly
     * @throws ApiError
     */
    public static v1DashboardAnomaliesRecentList(): CancelablePromise<Array<Anomaly>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboard/anomalies/recent/',
        });
    }
    /**
     * Obtenir les statistiques du tableau de bord
     * @returns DashboardStats
     * @throws ApiError
     */
    public static v1DashboardStatsRetrieve(): CancelablePromise<DashboardStats> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/dashboard/stats/',
        });
    }
    /**
     * Vue pour lister toutes les organisations et en créer de nouvelles
     * @param page A page number within the paginated result set.
     * @returns PaginatedOrganizationList
     * @throws ApiError
     */
    public static v1OrganizationsList(
        page?: number,
    ): CancelablePromise<PaginatedOrganizationList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour lister toutes les organisations et en créer de nouvelles
     * @param requestBody
     * @returns Organization
     * @throws ApiError
     */
    public static v1OrganizationsCreate(
        requestBody: OrganizationRequest,
    ): CancelablePromise<Organization> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/organizations/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer une organisation spécifique
     * @param id
     * @returns Organization
     * @throws ApiError
     */
    public static v1OrganizationsRetrieve(
        id: number,
    ): CancelablePromise<Organization> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer une organisation spécifique
     * @param id
     * @param requestBody
     * @returns Organization
     * @throws ApiError
     */
    public static v1OrganizationsUpdate(
        id: number,
        requestBody: OrganizationRequest,
    ): CancelablePromise<Organization> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/organizations/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer une organisation spécifique
     * @param id
     * @param requestBody
     * @returns Organization
     * @throws ApiError
     */
    public static v1OrganizationsPartialUpdate(
        id: number,
        requestBody?: PatchedOrganizationRequest,
    ): CancelablePromise<Organization> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/organizations/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer une organisation spécifique
     * @param id
     * @returns void
     * @throws ApiError
     */
    public static v1OrganizationsDestroy(
        id: number,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/organizations/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Obtenir les statistiques d'une organisation
     * @param id
     * @returns OrganizationStatistics
     * @throws ApiError
     */
    public static v1OrganizationsStatisticsRetrieve(
        id: number,
    ): CancelablePromise<OrganizationStatistics> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{id}/statistics/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour lister tous les utilisateurs d'une organisation spécifique
     * @param id
     * @param page A page number within the paginated result set.
     * @returns PaginatedUserList
     * @throws ApiError
     */
    public static v1OrganizationsUsersList(
        id: number,
        page?: number,
    ): CancelablePromise<PaginatedUserList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/organizations/{id}/users/',
            path: {
                'id': id,
            },
            query: {
                'page': page,
            },
        });
    }
    /**
     * @param page A page number within the paginated result set.
     * @returns PaginatedReportList
     * @throws ApiError
     */
    public static v1ReportsList(
        page?: number,
    ): CancelablePromise<PaginatedReportList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * @param requestBody
     * @returns Report
     * @throws ApiError
     */
    public static v1ReportsCreate(
        requestBody: ReportRequest,
    ): CancelablePromise<Report> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/reports/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir les détails d'un rapport
     * @param id
     * @returns Report
     * @throws ApiError
     */
    public static v1ReportsRetrieve(
        id: number,
    ): CancelablePromise<Report> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * @param id
     * @returns any Fichier du rapport
     * @throws ApiError
     */
    public static v1ReportsDownloadRetrieve(
        id: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/reports/{id}/download/',
            path: {
                'id': id,
            },
            errors: {
                404: `Rapport non trouvé`,
            },
        });
    }
    /**
     * @param requestBody
     * @returns any Rapport généré avec succès
     * @throws ApiError
     */
    public static v1ReportsGenerateCreate(
        requestBody: ReportGenerateRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/reports/generate/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `Données invalides`,
            },
        });
    }
    /**
     * Vue pour lister tous les sites et en créer de nouveaux
     * @param page A page number within the paginated result set.
     * @returns PaginatedSiteList
     * @throws ApiError
     */
    public static v1SitesList(
        page?: number,
    ): CancelablePromise<PaginatedSiteList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour lister tous les sites et en créer de nouveaux
     * @param requestBody
     * @returns Site
     * @throws ApiError
     */
    public static v1SitesCreate(
        requestBody: SiteRequest,
    ): CancelablePromise<Site> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sites/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un site spécifique
     * @param id
     * @returns Site
     * @throws ApiError
     */
    public static v1SitesRetrieve(
        id: number,
    ): CancelablePromise<Site> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un site spécifique
     * @param id
     * @param requestBody
     * @returns Site
     * @throws ApiError
     */
    public static v1SitesUpdate(
        id: number,
        requestBody: SiteRequest,
    ): CancelablePromise<Site> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/sites/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un site spécifique
     * @param id
     * @param requestBody
     * @returns Site
     * @throws ApiError
     */
    public static v1SitesPartialUpdate(
        id: number,
        requestBody?: PatchedSiteRequest,
    ): CancelablePromise<Site> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/sites/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un site spécifique
     * @param id
     * @returns void
     * @throws ApiError
     */
    public static v1SitesDestroy(
        id: number,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/sites/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour lister tous les employés d'un site et en ajouter de nouveaux
     * @param sitePk
     * @param page A page number within the paginated result set.
     * @returns PaginatedSiteEmployeeList
     * @throws ApiError
     */
    public static v1SitesEmployeesList(
        sitePk: number,
        page?: number,
    ): CancelablePromise<PaginatedSiteEmployeeList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/{site_pk}/employees/',
            path: {
                'site_pk': sitePk,
            },
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour lister tous les employés d'un site et en ajouter de nouveaux
     * @param sitePk
     * @param requestBody
     * @returns SiteEmployee
     * @throws ApiError
     */
    public static v1SitesEmployeesCreate(
        sitePk: number,
        requestBody: SiteEmployeeRequest,
    ): CancelablePromise<SiteEmployee> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sites/{site_pk}/employees/',
            path: {
                'site_pk': sitePk,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un employé d'un site
     * @param id
     * @param sitePk
     * @returns SiteEmployee
     * @throws ApiError
     */
    public static v1SitesEmployeesRetrieve(
        id: number,
        sitePk: number,
    ): CancelablePromise<SiteEmployee> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/{site_pk}/employees/{id}/',
            path: {
                'id': id,
                'site_pk': sitePk,
            },
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un employé d'un site
     * @param id
     * @param sitePk
     * @param requestBody
     * @returns SiteEmployee
     * @throws ApiError
     */
    public static v1SitesEmployeesUpdate(
        id: number,
        sitePk: number,
        requestBody: SiteEmployeeRequest,
    ): CancelablePromise<SiteEmployee> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/sites/{site_pk}/employees/{id}/',
            path: {
                'id': id,
                'site_pk': sitePk,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un employé d'un site
     * @param id
     * @param sitePk
     * @param requestBody
     * @returns SiteEmployee
     * @throws ApiError
     */
    public static v1SitesEmployeesPartialUpdate(
        id: number,
        sitePk: number,
        requestBody?: PatchedSiteEmployeeRequest,
    ): CancelablePromise<SiteEmployee> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/sites/{site_pk}/employees/{id}/',
            path: {
                'id': id,
                'site_pk': sitePk,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un employé d'un site
     * @param id
     * @param sitePk
     * @returns void
     * @throws ApiError
     */
    public static v1SitesEmployeesDestroy(
        id: number,
        sitePk: number,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/sites/{site_pk}/employees/{id}/',
            path: {
                'id': id,
                'site_pk': sitePk,
            },
        });
    }
    /**
     * Vue pour lister tous les plannings d'un site et en créer de nouveaux
     * @param sitePk
     * @param page A page number within the paginated result set.
     * @returns PaginatedScheduleList
     * @throws ApiError
     */
    public static v1SitesSchedulesList2(
        sitePk: number,
        page?: number,
    ): CancelablePromise<PaginatedScheduleList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/{site_pk}/schedules/',
            path: {
                'site_pk': sitePk,
            },
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour lister tous les plannings d'un site et en créer de nouveaux
     * @param sitePk
     * @param requestBody
     * @returns Schedule
     * @throws ApiError
     */
    public static v1SitesSchedulesCreate2(
        sitePk: number,
        requestBody: ScheduleRequest,
    ): CancelablePromise<Schedule> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sites/{site_pk}/schedules/',
            path: {
                'site_pk': sitePk,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un planning spécifique
     * @param id
     * @param sitePk
     * @returns Schedule
     * @throws ApiError
     */
    public static v1SitesSchedulesRetrieve2(
        id: number,
        sitePk: number,
    ): CancelablePromise<Schedule> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/{site_pk}/schedules/{id}/',
            path: {
                'id': id,
                'site_pk': sitePk,
            },
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un planning spécifique
     * @param id
     * @param sitePk
     * @param requestBody
     * @returns Schedule
     * @throws ApiError
     */
    public static v1SitesSchedulesUpdate2(
        id: number,
        sitePk: number,
        requestBody: ScheduleRequest,
    ): CancelablePromise<Schedule> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/sites/{site_pk}/schedules/{id}/',
            path: {
                'id': id,
                'site_pk': sitePk,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un planning spécifique
     * @param id
     * @param sitePk
     * @param requestBody
     * @returns Schedule
     * @throws ApiError
     */
    public static v1SitesSchedulesPartialUpdate2(
        id: number,
        sitePk: number,
        requestBody?: PatchedScheduleRequest,
    ): CancelablePromise<Schedule> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/sites/{site_pk}/schedules/{id}/',
            path: {
                'id': id,
                'site_pk': sitePk,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un planning spécifique
     * @param id
     * @param sitePk
     * @returns void
     * @throws ApiError
     */
    public static v1SitesSchedulesDestroy2(
        id: number,
        sitePk: number,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/sites/{site_pk}/schedules/{id}/',
            path: {
                'id': id,
                'site_pk': sitePk,
            },
        });
    }
    /**
     * Vue pour lister tous les détails d'un planning et en créer de nouveaux
     * @param schedulePk
     * @param sitePk
     * @param page A page number within the paginated result set.
     * @returns PaginatedScheduleDetailList
     * @throws ApiError
     */
    public static v1SitesSchedulesDetailsList(
        schedulePk: number,
        sitePk: number,
        page?: number,
    ): CancelablePromise<PaginatedScheduleDetailList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/{site_pk}/schedules/{schedule_pk}/details/',
            path: {
                'schedule_pk': schedulePk,
                'site_pk': sitePk,
            },
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour lister tous les détails d'un planning et en créer de nouveaux
     * @param schedulePk
     * @param sitePk
     * @param requestBody
     * @returns ScheduleDetail
     * @throws ApiError
     */
    public static v1SitesSchedulesDetailsCreate(
        schedulePk: number,
        sitePk: number,
        requestBody: ScheduleDetailRequest,
    ): CancelablePromise<ScheduleDetail> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sites/{site_pk}/schedules/{schedule_pk}/details/',
            path: {
                'schedule_pk': schedulePk,
                'site_pk': sitePk,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param page A page number within the paginated result set.
     * @returns PaginatedScheduleList
     * @throws ApiError
     */
    public static v1SitesSchedulesList(
        page?: number,
    ): CancelablePromise<PaginatedScheduleList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/schedules/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * @param requestBody
     * @returns Schedule
     * @throws ApiError
     */
    public static v1SitesSchedulesCreate(
        requestBody: ScheduleRequest,
    ): CancelablePromise<Schedule> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sites/schedules/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param id
     * @returns Schedule
     * @throws ApiError
     */
    public static v1SitesSchedulesRetrieve(
        id: number,
    ): CancelablePromise<Schedule> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sites/schedules/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * @param id
     * @param requestBody
     * @returns Schedule
     * @throws ApiError
     */
    public static v1SitesSchedulesUpdate(
        id: number,
        requestBody: ScheduleRequest,
    ): CancelablePromise<Schedule> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/sites/schedules/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param id
     * @param requestBody
     * @returns Schedule
     * @throws ApiError
     */
    public static v1SitesSchedulesPartialUpdate(
        id: number,
        requestBody?: PatchedScheduleRequest,
    ): CancelablePromise<Schedule> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/sites/schedules/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * @param id
     * @returns void
     * @throws ApiError
     */
    public static v1SitesSchedulesDestroy(
        id: number,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/sites/schedules/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour lister les pointages
     * @param page A page number within the paginated result set.
     * @returns PaginatedTimesheetList
     * @throws ApiError
     */
    public static v1TimesheetsList(
        page?: number,
    ): CancelablePromise<PaginatedTimesheetList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/timesheets/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour obtenir et mettre à jour un pointage
     * @param id
     * @returns Timesheet
     * @throws ApiError
     */
    public static v1TimesheetsRetrieve(
        id: number,
    ): CancelablePromise<Timesheet> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/timesheets/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour obtenir et mettre à jour un pointage
     * @param id
     * @param requestBody
     * @returns Timesheet
     * @throws ApiError
     */
    public static v1TimesheetsUpdate(
        id: number,
        requestBody: TimesheetRequest,
    ): CancelablePromise<Timesheet> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/timesheets/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir et mettre à jour un pointage
     * @param id
     * @param requestBody
     * @returns Timesheet
     * @throws ApiError
     */
    public static v1TimesheetsPartialUpdate(
        id: number,
        requestBody?: PatchedTimesheetRequest,
    ): CancelablePromise<Timesheet> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/timesheets/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour lister les anomalies
     * @param page A page number within the paginated result set.
     * @returns PaginatedAnomalyList
     * @throws ApiError
     */
    public static v1TimesheetsAnomaliesList(
        page?: number,
    ): CancelablePromise<PaginatedAnomalyList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/timesheets/anomalies/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour obtenir et mettre à jour une anomalie
     * @param id
     * @returns Anomaly
     * @throws ApiError
     */
    public static v1TimesheetsAnomaliesRetrieve(
        id: number,
    ): CancelablePromise<Anomaly> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/timesheets/anomalies/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour obtenir et mettre à jour une anomalie
     * @param id
     * @param requestBody
     * @returns Anomaly
     * @throws ApiError
     */
    public static v1TimesheetsAnomaliesUpdate(
        id: number,
        requestBody: AnomalyRequest,
    ): CancelablePromise<Anomaly> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/timesheets/anomalies/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir et mettre à jour une anomalie
     * @param id
     * @param requestBody
     * @returns Anomaly
     * @throws ApiError
     */
    public static v1TimesheetsAnomaliesPartialUpdate(
        id: number,
        requestBody?: PatchedAnomalyRequest,
    ): CancelablePromise<Anomaly> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/timesheets/anomalies/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour créer un pointage via l'application mobile
     * @param requestBody
     * @returns TimesheetCreate
     * @throws ApiError
     */
    public static v1TimesheetsCreateCreate(
        requestBody: TimesheetCreateRequest,
    ): CancelablePromise<TimesheetCreate> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/timesheets/create/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour lister les rapports d'employés
     * @param page A page number within the paginated result set.
     * @returns PaginatedEmployeeReportList
     * @throws ApiError
     */
    public static v1TimesheetsReportsList(
        page?: number,
    ): CancelablePromise<PaginatedEmployeeReportList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/timesheets/reports/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour obtenir les détails d'un rapport d'employé
     * @param id
     * @returns EmployeeReport
     * @throws ApiError
     */
    public static v1TimesheetsReportsRetrieve(
        id: number,
    ): CancelablePromise<EmployeeReport> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/timesheets/reports/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour générer un rapport
     * @param requestBody
     * @returns any Rapport généré avec succès
     * @throws ApiError
     */
    public static v1TimesheetsReportsGenerateCreate(
        requestBody: TimesheetReportGenerateRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/timesheets/reports/generate/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `Données invalides`,
            },
        });
    }
    /**
     * Vue pour scanner les anomalies dans les pointages existants
     * @param requestBody
     * @returns any Scan des anomalies effectué avec succès
     * @throws ApiError
     */
    public static v1TimesheetsScanAnomaliesCreate(
        requestBody?: ScanAnomaliesRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/timesheets/scan-anomalies/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `Données invalides`,
            },
        });
    }
    /**
     * Vue pour lister les utilisateurs
     * @param page A page number within the paginated result set.
     * @returns PaginatedUserList
     * @throws ApiError
     */
    public static v1UsersList(
        page?: number,
    ): CancelablePromise<PaginatedUserList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/users/',
            query: {
                'page': page,
            },
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un utilisateur spécifique (admin seulement)
     * @param id
     * @returns User
     * @throws ApiError
     */
    public static v1UsersRetrieve(
        id: number,
    ): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/users/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un utilisateur spécifique (admin seulement)
     * @param id
     * @param requestBody
     * @returns User
     * @throws ApiError
     */
    public static v1UsersUpdate(
        id: number,
        requestBody: UserRequest,
    ): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/users/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un utilisateur spécifique (admin seulement)
     * @param id
     * @param requestBody
     * @returns User
     * @throws ApiError
     */
    public static v1UsersPartialUpdate(
        id: number,
        requestBody?: PatchedUserRequest,
    ): CancelablePromise<User> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/users/{id}/',
            path: {
                'id': id,
            },
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir, mettre à jour et supprimer un utilisateur spécifique (admin seulement)
     * @param id
     * @returns void
     * @throws ApiError
     */
    public static v1UsersDestroy(
        id: number,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/users/{id}/',
            path: {
                'id': id,
            },
        });
    }
    /**
     * Vue pour changer le mot de passe
     * @param requestBody
     * @returns any Mot de passe changé avec succès
     * @throws ApiError
     */
    public static v1UsersChangePasswordCreate(
        requestBody: UserChangePasswordRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/change-password/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `Données invalides`,
            },
        });
    }
    /**
     * Vue pour la connexion des utilisateurs et l'obtention des tokens JWT
     * @param requestBody
     * @returns any No response body
     * @throws ApiError
     */
    public static v1UsersLoginCreate(
        requestBody: CustomTokenObtainPairRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/login/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour la déconnexion
     * @returns any Déconnexion réussie
     * @throws ApiError
     */
    public static v1UsersLogoutCreate(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/logout/',
        });
    }
    /**
     * Vue pour obtenir et mettre à jour le profil de l'utilisateur connecté
     * @returns UserProfile
     * @throws ApiError
     */
    public static v1UsersProfileRetrieve(): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/users/profile/',
        });
    }
    /**
     * Vue pour obtenir et mettre à jour le profil de l'utilisateur connecté
     * @param requestBody
     * @returns UserProfile
     * @throws ApiError
     */
    public static v1UsersProfileUpdate(
        requestBody?: UserProfileRequest,
    ): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/users/profile/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour obtenir et mettre à jour le profil de l'utilisateur connecté
     * @param requestBody
     * @returns UserProfile
     * @throws ApiError
     */
    public static v1UsersProfilePartialUpdate(
        requestBody?: PatchedUserProfileRequest,
    ): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/users/profile/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Vue pour l'enregistrement de nouveaux utilisateurs
     * @param requestBody
     * @returns UserRegister
     * @throws ApiError
     */
    public static v1UsersRegisterCreate(
        requestBody: UserRegisterRequest,
    ): CancelablePromise<UserRegister> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/register/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Takes a refresh type JSON web token and returns an access type JSON web
     * token if the refresh token is valid.
     * @param requestBody
     * @returns TokenRefresh
     * @throws ApiError
     */
    public static v1UsersTokenRefreshCreate(
        requestBody: TokenRefreshRequest,
    ): CancelablePromise<TokenRefresh> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/token/refresh/',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
}
