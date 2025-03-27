/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EntryTypeEnum } from './EntryTypeEnum';
/**
 * Serializer pour la création de pointages
 */
export type TimesheetCreate = {
    site: number;
    entry_type: EntryTypeEnum;
    timestamp?: string;
};

