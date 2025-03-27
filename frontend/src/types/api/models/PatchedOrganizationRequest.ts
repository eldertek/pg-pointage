/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Serializer pour les organisations
 */
export type PatchedOrganizationRequest = {
    name?: string;
    address?: string;
    postal_code?: string;
    city?: string;
    country?: string;
    phone?: string;
    email?: string;
    contact_email?: string;
    siret?: string;
    logo?: Blob | null;
    notes?: string;
    is_active?: boolean;
};

