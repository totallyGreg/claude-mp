/**
 * Date Utilities for OmniFocus JXA
 *
 * Provides date parsing and formatting functions for OmniFocus automation.
 *
 * Usage (load in JXA script):
 *   ObjC.import('Foundation');
 *   const dateUtils = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
 *       'libraries/jxa/dateUtils.js', $.NSUTF8StringEncoding, null
 *   ).js);
 *
 *   const date = dateUtils.parseDate('2025-12-30');
 *   const minutes = dateUtils.parseEstimate('2h30m');
 */

(() => {
    const dateUtils = {};

    /**
     * Parse ISO date string to Date object
     * @param {string} dateStr - ISO 8601 date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
     * @returns {Date} Parsed date object
     * @throws {Error} If date format is invalid
     */
    dateUtils.parseDate = function(dateStr) {
        // Try parsing ISO date: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
        const date = new Date(dateStr);

        if (isNaN(date.getTime())) {
            throw new Error(`Invalid date format: ${dateStr}. Use ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)`);
        }

        return date;
    };

    /**
     * Parse time estimate string to minutes
     * @param {string} estimateStr - Time estimate string (e.g., "30m", "2h", "1h30m")
     * @returns {number} Total minutes
     */
    dateUtils.parseEstimate = function(estimateStr) {
        // Format: 30m, 2h, 1h30m
        const hoursMatch = estimateStr.match(/(\d+)h/);
        const minutesMatch = estimateStr.match(/(\d+)m/);

        let totalMinutes = 0;

        if (hoursMatch) {
            totalMinutes += parseInt(hoursMatch[1]) * 60;
        }

        if (minutesMatch) {
            totalMinutes += parseInt(minutesMatch[1]);
        }

        return totalMinutes;
    };

    /**
     * Format Date object to ISO string
     * @param {Date} date - Date to format
     * @returns {string} ISO 8601 formatted date string
     */
    dateUtils.formatDate = function(date) {
        if (!date || !(date instanceof Date)) {
            return null;
        }
        return date.toISOString();
    };

    /**
     * Check if a date is today
     * @param {Date} date - Date to check
     * @returns {boolean} True if date is today
     */
    dateUtils.isToday = function(date) {
        if (!date) return false;

        const today = new Date();
        return date.getFullYear() === today.getFullYear() &&
               date.getMonth() === today.getMonth() &&
               date.getDate() === today.getDate();
    };

    /**
     * Check if a date is between two dates
     * @param {Date} date - Date to check
     * @param {Date} start - Start date (inclusive)
     * @param {Date} end - End date (inclusive)
     * @returns {boolean} True if date is between start and end
     */
    dateUtils.isBetween = function(date, start, end) {
        if (!date) return false;
        return date >= start && date <= end;
    };

    return dateUtils;
})();
