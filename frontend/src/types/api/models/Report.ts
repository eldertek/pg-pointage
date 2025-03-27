/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReportFormat } from './ReportFormat';
import type { ReportType } from './ReportType';
/**
 * Serializer pour les rapports
 */
export type Report = {
    readonly id: number;
    organization: number;
    readonly organization_name: string;
    site?: number | null;
    readonly site_name: string;
    report_type: ReportType;
    readonly report_type_display: string;
    report_format?: ReportFormat;
    readonly report_format_display: string;
    start_date: string;
    end_date: string;
    readonly file: string | null;
    readonly created_by: number | null;
    readonly created_by_name: string;
    readonly created_at: string;
};

