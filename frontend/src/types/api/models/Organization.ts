/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Serializer pour les organisations
 */
export type Organization = {
    readonly id: number;
    name: string;
    /**
     * ID unique de l'organisation sur 3 chiffres
     */
    readonly org_id: string;
    address?: string;
    postal_code?: string;
    city?: string;
    country?: string;
    phone?: string;
    email?: string;
    contact_email?: string;
    siret?: string;
    logo?: string | null;
    notes?: string;
    readonly created_at: string;
    readonly updated_at: string;
    is_active?: boolean;
    activation_start_date?: string;
    activation_end_date?: string;
};

