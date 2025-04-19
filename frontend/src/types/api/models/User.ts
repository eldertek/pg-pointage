/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BlankEnum } from './BlankEnum';
import type { NullEnum } from './NullEnum';
import type { RoleEnum } from './RoleEnum';
import type { ScanPreferenceEnum } from './ScanPreferenceEnum';
/**
 * Serializer pour les utilisateurs (admin)
 */
export interface User {
    id: number;
    /**
     * Requis. 150 caractères maximum. Uniquement des lettres, nombres et les caractères « @ », « . », « + », « - » et « _ ».
     */
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    role: 'SUPER_ADMIN' | 'ADMIN' | 'MANAGER' | 'EMPLOYEE';
    organizations: {
        id: number;
        name: string;
    }[];
    organizations_names: string[];
    phone_number?: string;
    is_active: boolean;
    activation_start_date?: string;
    activation_end_date?: string;
    employee_id?: string;
    scan_preference?: 'BOTH' | 'NFC_ONLY' | 'QR_ONLY';
    simplified_mobile_view?: boolean;
    date_joined: string;
    sites?: {
        id: number;
        name: string;
    }[];
}

