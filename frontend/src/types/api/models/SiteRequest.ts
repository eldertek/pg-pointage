/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Serializer pour les sites
 */
export type SiteRequest = {
    name: string;
    address: string;
    postal_code: string;
    city: string;
    country?: string;
    organization: number;
    qr_code?: Blob | null;
    late_margin?: number;
    early_departure_margin?: number;
    ambiguous_margin?: number;
    /**
     * Séparez les emails par des virgules
     */
    alert_emails?: string;
    require_geolocation?: boolean;
    geolocation_radius?: number;
    allow_offline_mode?: boolean;
    max_offline_duration?: number;
    is_active?: boolean;
    activation_start_date?: string;
    activation_end_date?: string;
    manager?: number | null;
};

