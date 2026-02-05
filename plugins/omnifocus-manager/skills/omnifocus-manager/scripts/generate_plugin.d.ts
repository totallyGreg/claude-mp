#!/usr/bin/env node
/**
 * OmniFocus Plugin Generator (TypeScript)
 *
 * Generates OmniFocus plugins from TypeScript templates with integrated LSP validation.
 * Replaces the Python-based generator with TypeScript Compiler API validation.
 *
 * Usage:
 *   node generate_plugin.js --format solitary --name "My Plugin"
 *   node generate_plugin.js --format solitary-fm --name "AI Analyzer"
 *   node generate_plugin.js --format bundle --template query-simple --name "Tasks"
 *
 * @version 4.0.0
 * @author OmniFocus Manager Skill
 */
type PluginFormat = 'solitary' | 'solitary-fm' | 'solitary-library' | 'bundle';
type BundleTemplate = 'query-simple' | 'stats-overview';
interface PluginOptions {
    format: PluginFormat;
    template?: BundleTemplate;
    name: string;
    identifier?: string;
    author?: string;
    description?: string;
    outputDir?: string;
}
interface GenerateResult {
    success: boolean;
    path?: string;
    errors?: string[];
}
declare class PluginGenerator {
    private skillRoot;
    private dtsPath;
    private dtsExtensionsPath;
    constructor();
    /**
     * Generate plugin from options
     */
    generate(options: PluginOptions): Promise<GenerateResult>;
    /**
     * Load template based on format
     */
    private loadTemplate;
    /**
     * Validate TypeScript code using TypeScript Compiler API
     *
     * Note: This is a simplified validation that checks for OmniFocus API usage.
     * We skip full TypeScript lib validation and focus on OmniFocus-specific errors.
     */
    private validateTypeScript;
    /**
     * Check if source file has syntax errors
     */
    private hasSyntaxErrors;
    /**
     * Write TypeScript file
     */
    private writeTsFile;
    /**
     * Rename .ts file to deployment format (.omnijs or .omnifocusjs)
     */
    private renameForDeployment;
}
export { PluginGenerator, type PluginOptions, type GenerateResult };
//# sourceMappingURL=generate_plugin.d.ts.map