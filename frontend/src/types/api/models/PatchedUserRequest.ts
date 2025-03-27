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
export type PatchedUserRequest = {
    /**
     * Requis. 150 caractères maximum. Uniquement des lettres, nombres et les caractères « @ », « . », « + », « - » et « _ ».
     */
    username?: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    role?: RoleEnum;
    organization?: number | null;
    phone_number?: string;
    is_active?: boolean;
    employee_id?: string;
    password?: string;
    /**
     * Uniquement pour les employés
     *
     * * `BOTH` - NFC et QR Code
     * * `NFC_ONLY` - NFC uniquement
     * * `QR_ONLY` - QR Code uniquement
     */
    scan_preference?: (ScanPreferenceEnum | BlankEnum | NullEnum) | null;
    /**
     * Si activé, affiche uniquement le bouton de pointage sur mobile
     */
    simplified_mobile_view?: boolean;
};

