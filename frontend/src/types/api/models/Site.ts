/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Schedule } from './Schedule';
/**
 * Serializer pour les sites
 */
export type Site = {
    readonly id: number;
    name: string;
    address: string;
    postal_code: string;
    city: string;
    country?: string;
    organization: number;
    readonly organization_name: string;
    /**
     * Format: FFF-Sxxxx où FFF est l'ID de l'organisation et xxxx est un nombre entre 0001 et 9999
     */
    readonly nfc_id: string;
    qr_code?: string | null;
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
    readonly created_at: string;
    readonly updated_at: string;
    is_active?: boolean;
    readonly schedules: Array<Schedule>;
    manager?: number | null;
    readonly manager_name: string;
};

