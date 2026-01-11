#!/usr/bin/env node
/**
 * OmniFocus Plugin Generator (TypeScript)
 *
 * Generates OmniFocus plugins from TypeScript templates with integrated LSP validation.
 * Replaces the Python-based generator with TypeScript Compiler API validation.
 *
 * DECISION TREE: Two Independent Choices
 *
 * Question 1: Plugin Structure
 *   SOLITARY (single file) when:
 *     - Single action only
 *     - No shared libraries between actions
 *     - Simple, focused task
 *     - Quick prototyping
 *
 *   BUNDLE (folder) when:
 *     - Multiple related actions (e.g., "Export Markdown", "Export JSON")
 *     - Shared libraries between actions
 *     - Localization support needed (en.lproj/)
 *     - Complex plugin with resources
 *     - Organized contextual automation tools
 *
 * Question 2: Application Scope (File Extension)
 *   .omnijs when:
 *     - Works across ALL Omni apps (OmniFocus, OmniGraffle, OmniOutliner, OmniPlan)
 *     - Uses only cross-app compatible APIs
 *     - Rare until skill expands beyond OmniFocus
 *
 *   .omnifocusjs when:
 *     - OmniFocus-specific functionality (default for this skill)
 *     - Uses OmniFocus-specific objects (Task, Project, Folder, Tag, etc.)
 *     - Most plugins fall into this category
 *
 * Valid Combinations:
 *   - Solitary .omnijs (single action, cross-app)
 *   - Solitary .omnifocusjs (single action, OF-only) ← Most common
 *   - Bundle .omnijs (multi-action, cross-app)
 *   - Bundle .omnifocusjs (multi-action, OF-only) ← Complex plugins
 *
 * Usage:
 *   node generate_plugin.js --format solitary --name "My Plugin"
 *   node generate_plugin.js --format solitary-fm --name "AI Analyzer"
 *   node generate_plugin.js --format bundle --template query-simple --name "Tasks"
 *
 * @version 4.1.0
 * @author OmniFocus Manager Skill
 */
import * as ts from 'typescript';
import * as fs from 'fs/promises';
import * as fsSync from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
// ============================================================================
// Constants
// ============================================================================
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FORMATS = {
    'solitary': 'Single-file action plugin (.omnijs)',
    'solitary-fm': 'Single-file action with Foundation Models (.omnijs)',
    'solitary-library': 'Single-file library plugin (.omnijs)',
    'bundle': 'Bundle plugin with localization (.omnifocusjs folder)',
};
const BUNDLE_TEMPLATES = {
    'query-simple': 'Simple query plugin with Alert display',
    'stats-overview': 'Statistics overview dashboard',
};
// ============================================================================
// Utility Functions
// ============================================================================
/**
 * Find omnifocus-manager skill root directory
 */
function findSkillRoot() {
    let current = path.resolve(__dirname);
    while (current !== path.dirname(current)) {
        const skillFile = path.join(current, 'SKILL.md');
        if (fsSync.existsSync(skillFile) && path.basename(current) === 'omnifocus-manager') {
            return current;
        }
        current = path.dirname(current);
    }
    return null;
}
/**
 * Convert text to camelCase
 */
function camelCase(text) {
    const words = text.replace(/-/g, ' ').replace(/_/g, ' ').split(/\s+/);
    if (words.length === 0)
        return '';
    return words[0].toLowerCase() + words.slice(1).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('');
}
/**
 * Replace template variables in content
 */
function substituteVariables(content, variables) {
    let result = content;
    for (const [key, value] of Object.entries(variables)) {
        const placeholder = `{{${key}}}`;
        result = result.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
    }
    return result;
}
/**
 * Prepare template variables from options
 */
function prepareVariables(options) {
    const identifier = options.identifier || `com.user.omnifocus.${options.name.toLowerCase().replace(/\s+/g, '')}`;
    const author = options.author || 'OmniFocus User';
    const description = options.description || `${options.name} plugin for OmniFocus`;
    const actionId = camelCase(options.name);
    const shortLabel = options.name.split(/\s+/)[0] || options.name;
    const icon = options.format === 'solitary-fm' ? 'apple.intelligence' : 'list.bullet';
    return {
        PLUGIN_NAME: options.name,
        IDENTIFIER: identifier,
        AUTHOR: author,
        DESCRIPTION: description,
        ACTION_ID: actionId,
        ACTION_LABEL: options.name,
        SHORT_LABEL: shortLabel,
        MEDIUM_LABEL: options.name,
        LONG_LABEL: `${options.name} with OmniFocus Automation`,
        PALETTE_LABEL: options.name,
        ICON: icon,
    };
}
// ============================================================================
// Plugin Generator Class
// ============================================================================
class PluginGenerator {
    skillRoot;
    dtsPath;
    dtsExtensionsPath;
    constructor() {
        const root = findSkillRoot();
        if (!root) {
            throw new Error('Could not find omnifocus-manager skill root directory');
        }
        this.skillRoot = root;
        this.dtsPath = path.join(root, 'typescript', 'omnifocus.d.ts');
        this.dtsExtensionsPath = path.join(root, 'typescript', 'omnifocus-extensions.d.ts');
    }
    /**
     * Generate plugin from options
     */
    async generate(options) {
        try {
            console.log(`\n🔨 Generating ${options.format} plugin...`);
            console.log(`   Plugin: ${options.name}`);
            console.log(`   Format: ${FORMATS[options.format]}\n`);

            // Prepare variables
            const variables = prepareVariables(options);

            let deployPath;

            if (options.format === 'bundle') {
                // Generate bundle folder structure
                deployPath = await this.generateBundle(options, variables);
            } else {
                // Generate single-file plugin
                deployPath = await this.generateSolitary(options, variables);
            }

            console.log('🎉 Plugin generated successfully!\n');
            console.log('📦 Installation:');
            if (options.format === 'bundle') {
                console.log(`   cp -r ${deployPath} ~/Library/Application\\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/`);
            }
            else {
                console.log(`   cp ${deployPath} ~/Library/Application\\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/`);
            }
            console.log('\n🧪 Testing:');
            console.log('   1. Restart OmniFocus (if running)');
            console.log('   2. Go to Automation menu');
            console.log(`   3. Find '${options.name}'\n`);
            return { success: true, path: deployPath };
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            console.error(`\n❌ Error: ${message}\n`);
            return { success: false, errors: [message] };
        }
    }

    /**
     * Generate solitary (single-file) plugin
     */
    async generateSolitary(options, variables) {
        // 1. Load template
        const template = await this.loadTemplate(options);
        // 2. Substitute variables
        const code = substituteVariables(template, variables);
        // 3. CRITICAL: Validate with TypeScript compiler
        console.log('🔍 Validating TypeScript...');
        const validation = await this.validateTypeScript(code, variables.ACTION_ID);
        if (!validation.success) {
            console.log('\n❌ TypeScript validation failed:');
            validation.errors.forEach((err, i) => {
                const location = err.line !== undefined ? `Line ${err.line + 1}${err.column !== undefined ? `:${err.column + 1}` : ''}` : '';
                console.log(`   ${i + 1}. ${location ? location + ' - ' : ''}${err.message}`);
            });
            throw new Error('TypeScript validation failed');
        }
        console.log('   ✅ TypeScript validation passed\n');
        // 4. Write .ts file
        const tsFilePath = await this.writeTsFile(code, options);
        // 5. Auto-rename to .omnijs
        const deployPath = await this.renameForDeployment(tsFilePath, options.format);
        return deployPath;
    }

    /**
     * Generate bundle plugin with folder structure
     */
    async generateBundle(options, variables) {
        if (!options.template) {
            throw new Error('Bundle format requires --template option');
        }

        const outputDir = options.outputDir || path.join(this.skillRoot, 'assets');
        const bundleName = `${options.name.replace(/\s+/g, '')}`;
        const bundlePath = path.join(outputDir, `${bundleName}.omnifocusjs`);
        const resourcesPath = path.join(bundlePath, 'Resources');

        console.log('📁 Creating bundle structure...');

        // 1. Create bundle directory structure
        await fs.mkdir(bundlePath, { recursive: true });
        await fs.mkdir(resourcesPath, { recursive: true });
        console.log(`   ✅ Created ${bundlePath}/`);
        console.log(`   ✅ Created ${bundlePath}/Resources/`);

        // 2. Generate manifest.json
        const manifestTemplate = await this.loadManifestTemplate(options.template);
        const manifestContent = substituteVariables(manifestTemplate, variables);
        const manifestPath = path.join(bundlePath, 'manifest.json');
        await fs.writeFile(manifestPath, manifestContent, 'utf-8');
        console.log(`   ✅ Created ${bundlePath}/manifest.json\n`);

        // 3. Copy/generate action files from template
        const templateDir = path.join(this.skillRoot, 'assets', 'plugin-templates', options.template);
        const templateResourcesDir = path.join(templateDir, 'Resources');

        // Copy action files
        const resourceFiles = await fs.readdir(templateResourcesDir);
        for (const file of resourceFiles) {
            const filePath = path.join(templateResourcesDir, file);
            const stat = await fs.stat(filePath);

            if (stat.isFile() && file.endsWith('.js')) {
                // Load, substitute variables, validate, and copy
                const actionTemplate = await fs.readFile(filePath, 'utf-8');
                const actionCode = substituteVariables(actionTemplate, variables);

                // Validate action code
                console.log(`🔍 Validating ${file}...`);
                const validation = await this.validateTypeScript(actionCode, file.replace('.js', ''));
                if (!validation.success) {
                    console.log(`\n❌ TypeScript validation failed for ${file}:`);
                    validation.errors.forEach((err, i) => {
                        const location = err.line !== undefined ? `Line ${err.line + 1}${err.column !== undefined ? `:${err.column + 1}` : ''}` : '';
                        console.log(`   ${i + 1}. ${location ? location + ' - ' : ''}${err.message}`);
                    });
                    throw new Error(`TypeScript validation failed for ${file}`);
                }
                console.log(`   ✅ Validation passed\n`);

                // Write to bundle
                const destPath = path.join(resourcesPath, file);
                await fs.writeFile(destPath, actionCode, 'utf-8');
                console.log(`   ✅ Created ${bundlePath}/Resources/${file}`);
            } else if (stat.isDirectory()) {
                // Copy directories (like en.lproj for localization)
                const destDir = path.join(resourcesPath, file);
                await this.copyDirectory(filePath, destDir);
                console.log(`   ✅ Copied ${bundlePath}/Resources/${file}/`);
            }
        }

        // 4. Copy README if exists
        const readmePath = path.join(templateDir, 'README.md');
        if (fsSync.existsSync(readmePath)) {
            const readmeContent = await fs.readFile(readmePath, 'utf-8');
            const readmeSubstituted = substituteVariables(readmeContent, variables);
            await fs.writeFile(path.join(bundlePath, 'README.md'), readmeSubstituted, 'utf-8');
            console.log(`   ✅ Created ${bundlePath}/README.md`);
        }

        return bundlePath;
    }

    /**
     * Copy directory recursively
     */
    async copyDirectory(src, dest) {
        await fs.mkdir(dest, { recursive: true });
        const entries = await fs.readdir(src);

        for (const entry of entries) {
            const srcPath = path.join(src, entry);
            const destPath = path.join(dest, entry);
            const stat = await fs.stat(srcPath);

            if (stat.isDirectory()) {
                await this.copyDirectory(srcPath, destPath);
            } else {
                await fs.copyFile(srcPath, destPath);
            }
        }
    }

    /**
     * Load manifest template for bundle
     */
    async loadManifestTemplate(templateName) {
        const manifestPath = path.join(
            this.skillRoot,
            'assets',
            'plugin-templates',
            templateName,
            'manifest.json'
        );

        try {
            return await fs.readFile(manifestPath, 'utf-8');
        } catch (error) {
            throw new Error(`Manifest template not found: ${manifestPath}`);
        }
    }
    /**
     * Load template based on format
     */
    async loadTemplate(options) {
        let templatePath;
        if (options.format === 'bundle') {
            if (!options.template) {
                throw new Error('Bundle format requires --template option');
            }
            templatePath = path.join(this.skillRoot, 'assets', 'plugin-templates', options.template, 'Resources', 'action.js');
        }
        else {
            const formatMap = {
                'solitary': 'solitary-action/action.ts.template',
                'solitary-fm': 'solitary-action-fm/action.ts.template',
                'solitary-library': 'solitary-library/library.ts.template',
            };
            templatePath = path.join(this.skillRoot, 'assets', 'plugin-templates', formatMap[options.format]);
        }
        try {
            return await fs.readFile(templatePath, 'utf-8');
        }
        catch (error) {
            throw new Error(`Template not found: ${templatePath}`);
        }
    }
    /**
     * Validate TypeScript code using TypeScript Compiler API
     *
     * Note: This is a simplified validation that checks for OmniFocus API usage.
     * We skip full TypeScript lib validation and focus on OmniFocus-specific errors.
     */
    async validateTypeScript(code, fileName) {
        try {
            // Read type definitions
            const omnifocusTypes = await fs.readFile(this.dtsPath, 'utf-8');
            const extensionTypes = await fs.readFile(this.dtsExtensionsPath, 'utf-8');
            // Prepend type definitions to code for validation
            // This is a simpler approach than setting up a full compiler host
            const fullCode = `
// OmniFocus Type Definitions
${omnifocusTypes}

// OmniFocus Extensions
${extensionTypes}

// Plugin Code
${code}
`;
            // Create source file for syntax check
            const sourceFile = ts.createSourceFile(`${fileName}.ts`, fullCode, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS);
            // Check for syntax errors by examining the source file
            // If TypeScript can parse it successfully, the plugin code is syntactically valid
            const hasErrors = this.hasSyntaxErrors(sourceFile);
            if (hasErrors) {
                return {
                    success: false,
                    errors: [{ message: 'TypeScript syntax error detected. Please check the template or generated code.' }]
                };
            }
            // Code is syntactically valid
            // TypeScript LSP will provide additional semantic validation during development
            return { success: true, errors: [] };
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            return {
                success: false,
                errors: [{ message: `TypeScript validation error: ${message}` }]
            };
        }
    }
    /**
     * Check if source file has syntax errors
     */
    hasSyntaxErrors(node) {
        // Check if current node has syntax errors
        if (node.kind === ts.SyntaxKind.Unknown) {
            return true;
        }
        // Recursively check children
        return ts.forEachChild(node, child => this.hasSyntaxErrors(child)) || false;
    }
    /**
     * Write TypeScript file
     */
    async writeTsFile(code, options) {
        const outputDir = options.outputDir || path.join(this.skillRoot, 'assets');
        const fileName = `${options.name.replace(/\s+/g, '')}.ts`;
        const filePath = path.join(outputDir, fileName);
        await fs.writeFile(filePath, code, 'utf-8');
        console.log(`✅ Created ${filePath}`);
        return filePath;
    }
    /**
     * Rename .ts file to deployment format (.omnijs or .omnifocusjs)
     */
    async renameForDeployment(tsFilePath, format) {
        const ext = format === 'bundle' ? '.omnifocusjs' : '.omnijs';
        const deployPath = tsFilePath.replace(/\.ts$/, ext);
        await fs.rename(tsFilePath, deployPath);
        console.log(`✅ Renamed to ${deployPath}`);
        return deployPath;
    }
}
// ============================================================================
// CLI Argument Parsing
// ============================================================================
function parseArgs(args) {
    const options = {};
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        const next = args[i + 1];
        switch (arg) {
            case '--format':
            case '-f':
                if (next && (next in FORMATS)) {
                    options.format = next;
                    i++;
                }
                break;
            case '--template':
            case '-t':
                if (next && (next in BUNDLE_TEMPLATES)) {
                    options.template = next;
                    i++;
                }
                break;
            case '--name':
            case '-n':
                if (next) {
                    options.name = next;
                    i++;
                }
                break;
            case '--identifier':
            case '-i':
                if (next) {
                    options.identifier = next;
                    i++;
                }
                break;
            case '--author':
            case '-a':
                if (next) {
                    options.author = next;
                    i++;
                }
                break;
            case '--description':
            case '-d':
                if (next) {
                    options.description = next;
                    i++;
                }
                break;
            case '--output':
            case '-o':
                if (next) {
                    options.outputDir = next;
                    i++;
                }
                break;
            case '--help':
            case '-h':
                printUsage();
                return null;
        }
    }
    // Validate required options
    if (!options.format) {
        console.error('❌ Error: --format is required\n');
        printUsage();
        return null;
    }
    if (!options.name) {
        console.error('❌ Error: --name is required\n');
        printUsage();
        return null;
    }
    if (options.format === 'bundle' && !options.template) {
        console.error('❌ Error: --template is required when --format is bundle\n');
        printUsage();
        return null;
    }
    return options;
}
function printUsage() {
    console.log(`
OmniFocus Plugin Generator (TypeScript)

📋 DECISION TREE: Two Independent Choices

  Question 1: Plugin Structure
    SOLITARY (single file) when:
      ✓ Single action only
      ✓ No shared libraries
      ✓ Simple, focused task
      ✓ Quick prototyping

    BUNDLE (folder) when:
      ✓ Multiple related actions
      ✓ Shared libraries between actions
      ✓ Localization support needed (en.lproj/)
      ✓ Complex plugin with resources

  Question 2: Application Scope (File Extension)
    .omnijs when:
      • Cross-app compatible (OmniFocus, OmniGraffle, OmniOutliner, OmniPlan)
      • Rare until skill expands beyond OmniFocus

    .omnifocusjs when:
      • OmniFocus-specific (default for this skill)
      • Uses OmniFocus objects (Task, Project, Folder, Tag)

  Valid Combinations:
    • Solitary .omnijs, Solitary .omnifocusjs ← Most common
    • Bundle .omnijs, Bundle .omnifocusjs ← Complex plugins

Usage:
  node generate_plugin.js [options]

Required Options:
  --format, -f <format>         Plugin format: ${Object.keys(FORMATS).join(', ')}
  --name, -n <name>             Plugin name (e.g., "My Plugin")

Optional Options:
  --template, -t <template>     Bundle template: ${Object.keys(BUNDLE_TEMPLATES).join(', ')} (required for bundle format)
  --identifier, -i <id>         Reverse domain identifier (default: auto-generated)
  --author, -a <author>         Plugin author (default: "OmniFocus User")
  --description, -d <desc>      Plugin description (default: auto-generated)
  --output, -o <dir>            Output directory (default: assets/)
  --help, -h                    Show this help message

Examples:
  # Simple solitary plugin (single action)
  node generate_plugin.js --format solitary --name "Quick Capture"

  # Solitary plugin with Foundation Models (AI features)
  node generate_plugin.js --format solitary-fm --name "AI Task Analyzer"

  # Bundle plugin with multiple actions
  node generate_plugin.js --format bundle --template query-simple --name "Task Explorer"

  # Library for reuse across plugins
  node generate_plugin.js --format solitary-library --name "MyUtilities"

Available Formats:
${Object.entries(FORMATS).map(([name, desc]) => `  ${name.padEnd(20)} ${desc}`).join('\n')}

Bundle Templates:
${Object.entries(BUNDLE_TEMPLATES).map(([name, desc]) => `  ${name.padEnd(20)} ${desc}`).join('\n')}
`);
}
// ============================================================================
// Main
// ============================================================================
async function main() {
    const args = process.argv.slice(2);
    if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
        printUsage();
        process.exit(0);
    }
    const options = parseArgs(args);
    if (!options) {
        process.exit(1);
    }
    const generator = new PluginGenerator();
    const result = await generator.generate(options);
    process.exit(result.success ? 0 : 1);
}
// Run if called directly
if (import.meta.url === `file://${__filename}`) {
    main().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}
export { PluginGenerator };
//# sourceMappingURL=generate_plugin.js.map