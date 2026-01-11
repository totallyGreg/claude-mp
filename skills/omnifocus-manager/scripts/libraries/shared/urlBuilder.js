/**
 * URL Builder for OmniFocus URL Scheme
 *
 * Cross-platform utility for building valid omnifocus:// URLs.
 * Works in both JXA and Omni Automation environments.
 *
 * Usage (in JXA):
 *   ObjC.import('Foundation');
 *   const urlBuilder = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
 *       'libraries/shared/urlBuilder.js', $.NSUTF8StringEncoding, null
 *   ).js);
 *   const url = urlBuilder.buildTaskURL({ name: "Test task" });
 *
 * Usage (in Omni Automation):
 *   // Load library code and evaluate
 *   const urlBuilder = <paste this code>;
 *   const url = urlBuilder.buildTaskURL({ name: "Test task" });
 *
 * @version 1.0.0
 */

(() => {
    const urlBuilder = {};

    /**
     * Build URL for adding a task to OmniFocus
     * @param {Object} params - Task parameters
     * @param {string} params.name - Task name (required)
     * @param {string} params.note - Task note/description
     * @param {string} params.project - Project name
     * @param {string|Array<string>} params.tags - Tag names (comma-separated string or array)
     * @param {string} params.folder - Folder name for the project
     * @param {string|Date} params.due - Due date (ISO8601 string or Date object)
     * @param {string|Date} params.defer - Defer date (ISO8601 string or Date object)
     * @param {string|number} params.estimate - Time estimate ("30m", "2h", "1h30m", or minutes)
     * @param {boolean} params.flagged - Flag the task
     * @param {boolean} params.autosave - Save without confirmation
     * @param {string} params.attach - File path or URL to attach
     * @returns {string} Complete omnifocus:// URL
     */
    urlBuilder.buildTaskURL = function(params) {
        if (!params.name) {
            throw new Error("Task name is required");
        }

        const queryParams = {};

        // Required parameter
        queryParams.name = params.name;

        // Optional parameters
        if (params.note) queryParams.note = params.note;
        if (params.project) queryParams.project = params.project;
        if (params.folder) queryParams.folder = params.folder;

        // Tags (handle both array and string)
        if (params.tags) {
            if (Array.isArray(params.tags)) {
                queryParams.tags = params.tags.join(',');
            } else {
                queryParams.tags = params.tags;
            }
        }

        // Dates (convert Date objects to ISO8601 strings)
        if (params.due) {
            queryParams.due = this.formatDate(params.due);
        }
        if (params.defer) {
            queryParams.defer = this.formatDate(params.defer);
        }

        // Time estimate (convert number to string format if needed)
        if (params.estimate !== undefined) {
            if (typeof params.estimate === 'number') {
                queryParams.estimate = this.formatEstimate(params.estimate);
            } else {
                queryParams.estimate = params.estimate;
            }
        }

        // Boolean parameters
        if (params.flagged) queryParams.flagged = 'true';
        if (params.autosave) queryParams.autosave = 'true';

        // Attachment
        if (params.attach) queryParams.attach = params.attach;

        return this.buildURL('add', queryParams);
    };

    /**
     * Build URL for pasting text into OmniFocus (creates tasks from text)
     * @param {string} text - Text to paste (each line becomes a task)
     * @param {Object} options - Paste options
     * @param {string} options.project - Target project
     * @param {string|Array<string>} options.tags - Tags to apply to all tasks
     * @returns {string} Complete omnifocus:// URL
     */
    urlBuilder.buildPasteURL = function(text, options = {}) {
        const queryParams = { content: text };

        if (options.project) queryParams.project = options.project;
        if (options.tags) {
            if (Array.isArray(options.tags)) {
                queryParams.tags = options.tags.join(',');
            } else {
                queryParams.tags = options.tags;
            }
        }

        return this.buildURL('paste', queryParams);
    };

    /**
     * Build URL for opening a perspective
     * @param {string} perspectiveName - Name of perspective to open
     * @returns {string} Complete omnifocus:// URL
     */
    urlBuilder.buildPerspectiveURL = function(perspectiveName) {
        return this.buildURL('perspective', { name: perspectiveName });
    };

    /**
     * Build URL for performing a search
     * @param {string} query - Search query
     * @returns {string} Complete omnifocus:// URL
     */
    urlBuilder.buildSearchURL = function(query) {
        return this.buildURL('search', { q: query });
    };

    /**
     * Build URL for showing a specific task
     * @param {string} taskId - Task ID (persistentIdentifier)
     * @returns {string} Complete omnifocus:// URL
     */
    urlBuilder.buildTaskShowURL = function(taskId) {
        return `omnifocus:///task/${this.encodeParam(taskId)}`;
    };

    /**
     * Build URL for showing a specific project
     * @param {string} projectId - Project ID (persistentIdentifier)
     * @returns {string} Complete omnifocus:// URL
     */
    urlBuilder.buildProjectShowURL = function(projectId) {
        return `omnifocus:///project/${this.encodeParam(projectId)}`;
    };

    /**
     * Build markdown link for a task
     * @param {string} taskName - Task name for link text
     * @param {Object} params - Task parameters (same as buildTaskURL)
     * @returns {string} Markdown link
     */
    urlBuilder.buildMarkdownLink = function(taskName, params) {
        const url = this.buildTaskURL(params);
        return `[${taskName}](${url})`;
    };

    /**
     * Build base URL with action and query parameters
     * @param {string} action - Action name (add, paste, perspective, search)
     * @param {Object} params - Query parameters
     * @returns {string} Complete omnifocus:// URL
     * @private
     */
    urlBuilder.buildURL = function(action, params) {
        const queryString = Object.keys(params)
            .map(key => `${key}=${this.encodeParam(params[key])}`)
            .join('&');

        return `omnifocus:///${action}?${queryString}`;
    };

    /**
     * Encode parameter for URL
     * @param {string} value - Value to encode
     * @returns {string} URL-encoded value
     */
    urlBuilder.encodeParam = function(value) {
        if (value === undefined || value === null) {
            return '';
        }

        // Convert to string
        value = String(value);

        // Use built-in encoding if available
        if (typeof encodeURIComponent !== 'undefined') {
            return encodeURIComponent(value);
        }

        // Fallback manual encoding (for environments without encodeURIComponent)
        return value
            .replace(/%/g, '%25')  // % must be first
            .replace(/ /g, '%20')
            .replace(/!/g, '%21')
            .replace(/"/g, '%22')
            .replace(/#/g, '%23')
            .replace(/\$/g, '%24')
            .replace(/&/g, '%26')
            .replace(/'/g, '%27')
            .replace(/\(/g, '%28')
            .replace(/\)/g, '%29')
            .replace(/\*/g, '%2A')
            .replace(/\+/g, '%2B')
            .replace(/,/g, '%2C')
            .replace(/\//g, '%2F')
            .replace(/:/g, '%3A')
            .replace(/;/g, '%3B')
            .replace(/=/g, '%3D')
            .replace(/\?/g, '%3F')
            .replace(/@/g, '%40')
            .replace(/\[/g, '%5B')
            .replace(/\]/g, '%5D')
            .replace(/\n/g, '%0A')
            .replace(/\r/g, '%0D')
            .replace(/\t/g, '%09');
    };

    /**
     * Format date for URL (ISO8601)
     * @param {string|Date} date - Date to format
     * @returns {string} ISO8601 formatted date
     * @private
     */
    urlBuilder.formatDate = function(date) {
        if (typeof date === 'string') {
            return date; // Assume already formatted
        }

        if (date instanceof Date) {
            // Format as YYYY-MM-DDTHH:MM:SS
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');

            // If time is midnight, return date only
            if (hours === '00' && minutes === '00' && seconds === '00') {
                return `${year}-${month}-${day}`;
            }

            return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
        }

        return String(date);
    };

    /**
     * Format time estimate from minutes to string format
     * @param {number} minutes - Time in minutes
     * @returns {string} Formatted estimate ("30m", "1h30m", etc.)
     * @private
     */
    urlBuilder.formatEstimate = function(minutes) {
        if (minutes < 60) {
            return `${minutes}m`;
        }

        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;

        if (remainingMinutes === 0) {
            return `${hours}h`;
        }

        return `${hours}h${remainingMinutes}m`;
    };

    /**
     * Parse omnifocus:// URL into components
     * @param {string} url - OmniFocus URL to parse
     * @returns {Object} Parsed URL components
     */
    urlBuilder.parseURL = function(url) {
        if (!url.startsWith('omnifocus:///')) {
            throw new Error('Invalid OmniFocus URL');
        }

        // Remove omnifocus:/// prefix
        const remainder = url.substring(13);

        // Split action and query
        const questionMarkIndex = remainder.indexOf('?');
        let action, queryString;

        if (questionMarkIndex === -1) {
            action = remainder;
            queryString = '';
        } else {
            action = remainder.substring(0, questionMarkIndex);
            queryString = remainder.substring(questionMarkIndex + 1);
        }

        // Parse query parameters
        const params = {};
        if (queryString) {
            queryString.split('&').forEach(pair => {
                const [key, value] = pair.split('=');
                params[key] = decodeURIComponent(value || '');
            });
        }

        return {
            action: action,
            params: params
        };
    };

    /**
     * Validate task parameters
     * @param {Object} params - Task parameters to validate
     * @returns {Object} Validation result
     */
    urlBuilder.validateParams = function(params) {
        const errors = [];
        const warnings = [];

        // Required parameters
        if (!params.name) {
            errors.push('Task name is required');
        }

        // Date format validation
        if (params.due && !this.isValidDateFormat(params.due)) {
            errors.push('Invalid due date format (use ISO8601: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)');
        }
        if (params.defer && !this.isValidDateFormat(params.defer)) {
            errors.push('Invalid defer date format (use ISO8601: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)');
        }

        // Estimate format validation
        if (params.estimate && typeof params.estimate === 'string') {
            if (!/^\d+[hm](\d+m)?$/.test(params.estimate)) {
                errors.push('Invalid estimate format (use: 30m, 2h, 1h30m)');
            }
        }

        // Warnings
        if (params.name && params.name.length > 100) {
            warnings.push('Task name is very long (>100 characters)');
        }

        return {
            valid: errors.length === 0,
            errors: errors,
            warnings: warnings
        };
    };

    /**
     * Check if date format is valid
     * @param {string|Date} date - Date to check
     * @returns {boolean} True if valid
     * @private
     */
    urlBuilder.isValidDateFormat = function(date) {
        if (date instanceof Date) {
            return !isNaN(date.getTime());
        }

        if (typeof date !== 'string') {
            return false;
        }

        // Check ISO8601 formats: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
        const dateOnlyPattern = /^\d{4}-\d{2}-\d{2}$/;
        const dateTimePattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/;

        return dateOnlyPattern.test(date) || dateTimePattern.test(date);
    };

    return urlBuilder;
})();
