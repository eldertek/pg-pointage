/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TimesheetReportGenerateReportFormatEnum } from './TimesheetReportGenerateReportFormatEnum';
import type { TimesheetReportGenerateReportTypeEnum } from './TimesheetReportGenerateReportTypeEnum';
/**
 * Serializer pour la génération de rapports de pointage
 */
export type TimesheetReportGenerateRequest = {
    report_type: TimesheetReportGenerateReportTypeEnum;
    report_format: TimesheetReportGenerateReportFormatEnum;
    start_date: string;
    end_date: string;
    site?: number;
};

