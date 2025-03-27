/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RoleEnum } from './RoleEnum';
/**
 * Serializer pour le profil utilisateur
 */
export type UserProfile = {
    readonly id: number;
    /**
     * Requis. 150 caractères maximum. Uniquement des lettres, nombres et les caractères « @ », « . », « + », « - » et « _ ».
     */
    readonly username: string;
    readonly email: string;
    first_name?: string;
    last_name?: string;
    readonly role: RoleEnum;
    readonly organization: number | null;
    readonly organization_name: string;
    is_active?: boolean;
};

