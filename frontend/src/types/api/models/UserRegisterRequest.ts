/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Serializer pour l'enregistrement de nouveaux utilisateurs
 */
export type UserRegisterRequest = {
    /**
     * Requis. 150 caractères maximum. Uniquement des lettres, nombres et les caractères « @ », « . », « + », « - » et « _ ».
     */
    username: string;
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    is_active?: boolean;
};

