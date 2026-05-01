// TypeScript definitions for OmniFocus APIs added after 2021
// Extends omnifocus.d.ts with newer APIs including LanguageModel (OmniFocus 4.8+)
// Generated: 2026-01-02

// ============================================================================
// LanguageModel (Apple Foundation Models / Apple Intelligence)
// Available in OmniFocus 4.8+ with macOS 15.2+ or iOS 18.2+
// Requires Apple Silicon (M1/M2/M3/M4) or iPhone 15 Pro+
// ============================================================================

declare namespace LanguageModel {
    /**
     * Options for controlling language model generation behavior
     * @see https://developer.apple.com/documentation/translation/languagemodelgenerationoptions
     */
    class GenerationOptions {
        constructor();

        /**
         * Maximum number of tokens in the response
         * @see https://developer.apple.com/documentation/translation/languagemodelgenerationoptions/maximumresponsetokens
         */
        maximumResponseTokens: number | null;
    }

    /**
     * Schema for structured responses from language model
     *
     * Guides the structure of language model responses to ensure consistent format.
     * Uses OmniFocus schema format (NOT standard JSON Schema).
     *
     * @example
     * // Array of tasks with priorities
     * const schema = LanguageModel.Schema.fromJSON({
     *     arrayOf: {
     *         name: "task-schema",
     *         properties: [
     *             {name: "title"},
     *             {name: "description", isOptional: true},
     *             {name: "priority", schema: {
     *                 anyOf: [{constant: "high"}, {constant: "low"}]
     *             }}
     *         ]
     *     }
     * });
     *
     * @example
     * // Single object response
     * const schema = LanguageModel.Schema.fromJSON({
     *     name: "analysis-schema",
     *     properties: [
     *         {name: "summary"},
     *         {name: "tags", schema: {arrayOf: {constant: "tag"}}}
     *     ]
     * });
     */
    class Schema {
        /**
         * Create schema from JSON object
         *
         * Schema Structure:
         * - `name` (optional): Schema name for recursive references
         * - `properties`: Array of property definitions
         *   - `{name: "field"}` - Required property
         *   - `{name: "field", isOptional: true}` - Optional property
         *   - `{name: "field", description: "..."}` - With description
         *   - `{name: "field", schema: {...}}` - Nested schema
         * - `arrayOf`: Define array with element schema
         *   - `{arrayOf: {constant: "value"}}` - Array of constant strings
         *   - `{arrayOf: {properties: [...]}}` - Array of objects
         *   - `{arrayOf: {referenceTo: "schema-name"}}` - Recursive reference
         * - `anyOf`: Union type / enumeration
         *   - `{anyOf: [{constant: "a"}, {constant: "b"}]}` - Enum
         * - `constant`: Literal value
         *   - `{constant: "value"}` - String literal
         * - `referenceTo`: Reference to named schema
         *   - `{referenceTo: "schema-name"}` - For recursive structures
         *
         * @param json Schema definition object (OmniFocus format, NOT JSON Schema)
         * @returns LanguageModel.Schema instance
         *
         * @see /references/code_generation_validation.md#rule-5-languagemodelschema-validation
         */
        static fromJSON(json: Object): LanguageModel.Schema;
    }

    /**
     * Session for interacting with language model
     *
     * Maintains conversation context across multiple prompts.
     */
    class Session {
        /**
         * Create new language model session
         * @param instructions Optional system instructions for the session
         */
        constructor(instructions?: string | null);

        /**
         * Get text response to a prompt
         * @param prompt Text prompt for the language model
         * @returns Promise resolving to text response
         */
        respond(prompt: string): Promise<string>;

        /**
         * Get structured JSON response to a prompt
         * @param prompt Text prompt for the language model
         * @param schema Schema defining expected response structure
         * @param generationOptions Optional generation options
         * @returns Promise resolving to JSON string (use JSON.parse() to parse)
         *
         * @example
         * const session = new LanguageModel.Session();
         * const schema = LanguageModel.Schema.fromJSON({
         *     properties: [{name: "summary"}, {name: "priority"}]
         * });
         * const jsonResponse = await session.respondWithSchema("Analyze this task", schema);
         * const data = JSON.parse(jsonResponse);
         * console.log(data.summary, data.priority);
         */
        respondWithSchema(
            prompt: string,
            schema: LanguageModel.Schema,
            generationOptions?: LanguageModel.GenerationOptions | null
        ): Promise<string>;
    }
}

// ============================================================================
// Additional Type Refinements
// ============================================================================

// Note: Selection, MenuItem, and ToolbarItem are already defined in omnifocus.d.ts
// Do not redeclare them here to avoid duplicate identifier errors

// ============================================================================
// Global Variables
// These are available in the OmniFocus Automation environment
// ============================================================================

/** All tasks in the database, flattened */
declare const flattenedTasks: TaskArray;

/** All projects in the database, flattened */
declare const flattenedProjects: ProjectArray;

/** All folders in the database, flattened */
declare const flattenedFolders: FolderArray;

/** All tags in the database, flattened */
declare const flattenedTags: TagArray;

/** Top-level folders */
declare const folders: FolderArray;

/** Top-level tags */
declare const tags: Tags;

/** The inbox */
declare const inbox: Inbox;

/** The library (root of folder hierarchy) */
declare const library: Library;

/** Console for logging (lowercase, not the Console class) */
declare const console: Console;

/** The current application */
declare const app: Application;

// ============================================================================
// URL Extensions
// These methods exist in OmniFocus but aren't in the 2021 type definitions
// ============================================================================

declare interface URL {
    /**
     * Write string content to the URL (file)
     * @param content String content to write
     */
    write(content: string): void;
}

// ============================================================================
// FileSaver Extensions
// Additional properties that exist in newer OmniFocus versions
// ============================================================================

declare interface FileSaver {
    /** Default filename for the save dialog */
    defaultFileName: string;
}
