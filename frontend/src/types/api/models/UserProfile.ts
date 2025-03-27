/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BlankEnum } from './BlankEnum';
import type { NullEnum } from './NullEnum';
import type { RoleEnum } from './RoleEnum';
import type { ScanPreferenceEnum } from './ScanPreferenceEnum';
/**
 * Serializer pour le profil utilisateur (utilisateur connecté)
 */
export type UserProfile = {
    readonly id: number;
    /**
     * Requis. 150 caractères maximum. Uniquement des lettres, nombres et les caractères « @ », « . », « + », « - » et « _ ».
     */
    username: string;
    email: string;
    first_name?: string;
    last_name?: string;
    readonly role: RoleEnum;
    readonly organization: number | null;
    readonly organization_name: string;
    phone_number?: string;
    readonly employee_id: string;
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

