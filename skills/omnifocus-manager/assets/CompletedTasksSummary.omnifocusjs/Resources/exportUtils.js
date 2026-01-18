/**
 * Export Utilities Library for OmniFocus
 *
 * Reusable functions for exporting data to various formats.
 * Supports JSON, CSV, Markdown, HTML and clipboard/file exports.
 *
 * Usage (in OmniFocus plugin):
 *   // In manifest.json, declare as library:
 *   "libraries": ["exportUtils"]
 *
 *   // In action script:
 *   const exporter = this.plugIn.library("exportUtils");
 *   await exporter.toClipboard(data, { format: 'json' 
 *
 * Usage (in Omni Automation console):
 *   // Load library code and evaluate
 *   const exporter = <paste this code>;
 *   await exporter.toFile(data, { format: 'markdown' 
 *
 * @version 3.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

        /**
         * Copy data to system clipboard
         * @param {*} data - Data to copy
         * @param {Object} options - Export options
         * @param {string} options.format - Format: 'json', 'csv', 'markdown', 'html' (default: 'json')
         * @param {boolean} options.pretty - Pretty print JSON (default: true)
         * @returns {boolean} Success status
         */
        lib.toClipboard = function(data, options = {}) {
            try {
                const format = options.format || 'json';
                let output;

                switch (format) {
                    case 'json':
                        output = this.toJSON(data, options.pretty !== false);
                        break;
                    case 'csv':
                        output = this.toCSV(data);
                        break;
                    case 'markdown':
                        output = this.toMarkdown(data, options);
                        break;
                    case 'html':
                        output = this.toHTML(data, options);
                        break;
                    default:
                        throw new Error(`Unknown format: ${format}`);
                }

                Pasteboard.general.string = output;
                return true;
            } catch (error) {
                console.error("Export to clipboard failed:", error);
                return false;
            }
        };

        /**
         * Save data to file
         * @param {*} data - Data to save
         * @param {Object} options - Export options
         * @param {string} options.format - Format: 'json', 'csv', 'markdown', 'html'
         * @param {string} options.filename - Suggested filename
         * @param {boolean} options.pretty - Pretty print JSON
         * @returns {Promise<boolean>} Success status
         */
        lib.toFile = async function(data, options = {}) {
            try {
                const format = options.format || 'json';
                let output, extension, mimeType;

                switch (format) {
                    case 'json':
                        output = this.toJSON(data, options.pretty !== false);
                        extension = 'json';
                        mimeType = 'application/json';
                        break;
                    case 'csv':
                        output = this.toCSV(data);
                        extension = 'csv';
                        mimeType = 'text/csv';
                        break;
                    case 'markdown':
                        output = this.toMarkdown(data, options);
                        extension = 'md';
                        mimeType = 'text/markdown';
                        break;
                    case 'html':
                        output = this.toHTML(data, options);
                        extension = 'html';
                        mimeType = 'text/html';
                        break;
                    default:
                        throw new Error(`Unknown format: ${format}`);
                }

                const filename = options.filename ||
                    `omnifocus-export-${new Date().toISOString().split('T')[0]}.${extension}`;

                const fileSaver = new FileSaver();
                fileSaver.nameLabel = "Save Export";
                fileSaver.types = [FileType.fromExtension(extension)];
                fileSaver.defaultFileName = filename;

                const url = await fileSaver.show();
                if (url) {
                    const wrapper = FileWrapper.fromString(url.toString(), output);
                    wrapper.write(url);
                    return true;
                }

                return false;
            } catch (error) {
                console.error("Export to file failed:", error);
                return false;
            }
        };

        /**
         * Format data as JSON string
         * @param {*} data - Data to format
         * @param {boolean} pretty - Pretty print (default: true)
         * @returns {string} JSON string
         */
        lib.toJSON = function(data, pretty = true) {
            return JSON.stringify(data, null, pretty ? 2 : 0);
        };

        /**
         * Format array of objects as CSV
         * @param {Array} data - Array of objects to format
         * @param {Array} customHeaders - Optional custom header names
         * @returns {string} CSV string
         */
        lib.toCSV = function(data, customHeaders = null) {
            if (!Array.isArray(data) || data.length === 0) {
                return "";
            }

            // Get headers from first object or use custom
            const firstItem = data[0];
            const headers = customHeaders || Object.keys(firstItem);

            const rows = [headers.join(",")];

            data.forEach(item => {
                const values = headers.map(header => {
                    const value = item[header];
                    return this.formatCSVValue(value);
                
                rows.push(values.join(","));
            

            return rows.join("\n");
        };

        /**
         * Format value for CSV
         * @param {*} value - Value to format
         * @returns {string} Formatted value
         * @private
         */
        lib.formatCSVValue = function(value) {
            if (value === null || value === undefined) {
                return "";
            }

            if (Array.isArray(value)) {
                value = value.join("; ");
            } else if (value instanceof Date) {
                value = value.toISOString();
            } else if (typeof value === 'object') {
                value = JSON.stringify(value);
            } else {
                value = String(value);
            }

            // Escape if contains comma, quote, or newline
            if (value.includes(",") || value.includes('"') || value.includes("\n")) {
                return '"' + value.replace(/"/g, '""') + '"';
            }

            return value;
        };

        /**
         * Format data as Markdown
         * @param {*} data - Data to format
         * @param {Object} options - Format options
         * @param {boolean} options.includeStats - Include summary stats
         * @param {string} options.title - Document title
         * @returns {string} Markdown string
         */
        lib.toMarkdown = function(data, options = {}) {
            let md = "";

            // Add title if provided
            if (options.title) {
                md += `# ${options.title}\n\n`;
            }

            // Add timestamp
            md += `**Generated:** ${new Date().toLocaleString()}\n\n`;

            // Format based on data type
            if (Array.isArray(data)) {
                md += this.formatArrayAsMarkdown(data);
            } else if (typeof data === 'object') {
                md += this.formatObjectAsMarkdown(data, options);
            } else {
                md += String(data);
            }

            return md;
        };

        /**
         * Format array as Markdown table or list
         * @param {Array} arr - Array to format
         * @returns {string} Markdown content
         * @private
         */
        lib.formatArrayAsMarkdown = function(arr) {
            if (arr.length === 0) return "No data\n";

            // Check if array of objects (for table formatting)
            if (typeof arr[0] === 'object' && arr[0] !== null && !Array.isArray(arr[0])) {
                return this.formatTableAsMarkdown(arr);
            }

            // Simple list
            return arr.map(item => `- ${item}`).join("\n") + "\n";
        };

        /**
         * Format array of objects as Markdown table
         * @param {Array} data - Array of objects
         * @returns {string} Markdown table
         * @private
         */
        lib.formatTableAsMarkdown = function(data) {
            if (data.length === 0) return "No data\n";

            const headers = Object.keys(data[0]);
            let md = "| " + headers.join(" | ") + " |\n";
            md += "|" + headers.map(() => "---").join("|") + "|\n";

            data.forEach(row => {
                const values = headers.map(h => {
                    const val = row[h];
                    if (val === null || val === undefined) return "";
                    if (Array.isArray(val)) return val.join(", ");
                    if (val instanceof Date) return val.toLocaleDateString();
                    return String(val).replace(/\|/g, "\\|");
                
                md += "| " + values.join(" | ") + " |\n";
            

            return md;
        };

        /**
         * Format object as Markdown sections
         * @param {Object} obj - Object to format
         * @param {Object} options - Format options
         * @returns {string} Markdown string
         * @private
         */
        lib.formatObjectAsMarkdown = function(obj, options = {}) {
            let md = "";

            for (const [key, value] of Object.entries(obj)) {
                md += `## ${key}\n\n`;

                if (Array.isArray(value)) {
                    md += this.formatArrayAsMarkdown(value);
                } else if (typeof value === 'object' && value !== null) {
                    md += this.formatObjectAsMarkdown(value, options);
                } else {
                    md += `${value}\n`;
                }

                md += "\n";
            }

            return md;
        };

        /**
         * Format data as HTML table
         * @param {Array} data - Array of objects
         * @param {Object} options - Format options
         * @returns {string} HTML string
         */
        lib.toHTML = function(data, options = {}) {
            if (!Array.isArray(data) || data.length === 0) {
                return "<p>No data</p>";
            }

            const headers = Object.keys(data[0]);

            let html = "<table>\n<thead>\n<tr>\n";
            headers.forEach(h => {
                html += `<th>${this.escapeHTML(h)}</th>\n`;
            
            html += "</tr>\n</thead>\n<tbody>\n";

            data.forEach(row => {
                html += "<tr>\n";
                headers.forEach(h => {
                    const val = row[h];
                    const formatted = val === null || val === undefined ? ""
                        : Array.isArray(val) ? val.join(", ")
                        : val instanceof Date ? val.toLocaleDateString()
                        : String(val);
                    html += `<td>${this.escapeHTML(formatted)}</td>\n`;
                
                html += "</tr>\n";
            

            html += "</tbody>\n</table>";
            return html;
        };

        /**
         * Escape HTML special characters
         * @param {string} str - String to escape
         * @returns {string} Escaped string
         * @private
         */
        lib.escapeHTML = function(str) {
            if (!str) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        };

    

    return lib;
})();
