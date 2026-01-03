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

/**
 * Selection object passed to plugin actions
 *
 * Note: Full definition should be in omnifocus.d.ts
 * Added here for template type-safety if missing from base definitions
 */
declare class Selection {
    readonly tasks: Array<Task>;
    readonly projects: Array<Project>;
    readonly folders: Array<Folder>;
    readonly tags: Array<Tag>;
    readonly document: Document;
}

/**
 * Menu item sender for plugin actions
 *
 * Note: Full definition should be in omnifocus.d.ts
 * Added here for template type-safety if missing from base definitions
 */
declare class MenuItem {
    readonly title: string;
}

/**
 * Toolbar item sender for plugin actions
 *
 * Note: Full definition should be in omnifocus.d.ts
 * Added here for template type-safety if missing from base definitions
 */
declare class ToolbarItem {
    readonly label: string;
    readonly image: string | null;
}
