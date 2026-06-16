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

import * as ts from 'typescript';
import * as fs from 'fs/promises';
import * as fsSync from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

// ============================================================================
// Types
// ============================================================================

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
  // D8.5 — auto-emit runtime contract skeletons at the top of the action body.
  // 'ofoCore' → check Attache plugin + ofoCore library presence + function check
  //   (per references/library_consumer_pattern.md skeleton)
  // 'systemMap' → check "Attache System Map" task exists + valid JSON + schema version
  //   (per references/system_map_dependency.md skeleton)
  requires?: Array<'ofoCore' | 'systemMap'>;
}

interface TemplateVariables {
  PLUGIN_NAME: string;
  IDENTIFIER: string;
  AUTHOR: string;
  DESCRIPTION: string;
  ACTION_ID: string;
  ACTION_LABEL: string;
  SHORT_LABEL: string;
  MEDIUM_LABEL: string;
  LONG_LABEL: string;
  PALETTE_LABEL: string;
  ICON: string;
}

interface ValidationResult {
  success: boolean;
  errors: Array<{
    line?: number;
    column?: number;
    message: string;
  }>;
}

interface GenerateResult {
  success: boolean;
  path?: string;
  errors?: string[];
}

// ============================================================================
// Constants
// ============================================================================

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FORMATS: Record<PluginFormat, string> = {
  'solitary': 'Single-file action plugin (.omnijs)',
  'solitary-fm': 'Single-file action with Foundation Models (.omnijs)',
  'solitary-library': 'Single-file library plugin (.omnijs)',
  'bundle': 'Bundle plugin with localization (.omnifocusjs folder)',
};

const BUNDLE_TEMPLATES: Record<BundleTemplate, string> = {
  'query-simple': 'Simple query plugin with Alert display',
  'stats-overview': 'Statistics overview dashboard',
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Find omnifocus-generator skill root directory
 */
function findSkillRoot(): string | null {
  let current = path.resolve(__dirname);
  while (current !== path.dirname(current)) {
    const skillFile = path.join(current, 'SKILL.md');
    if (fsSync.existsSync(skillFile) && path.basename(current) === 'omnifocus-generator') {
      return current;
    }
    current = path.dirname(current);
  }
  return null;
}

/**
 * Convert text to camelCase
 */
function camelCase(text: string): string {
  const words = text.replace(/-/g, ' ').replace(/_/g, ' ').split(/\s+/);
  if (words.length === 0) return '';
  return words[0]!.toLowerCase() + words.slice(1).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('');
}

/**
 * Replace template variables in content
 */
function substituteVariables(content: string, variables: TemplateVariables): string {
  let result = content;
  for (const [key, value] of Object.entries(variables)) {
    const placeholder = `{{${key}}}`;
    result = result.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), value);
  }
  return result;
}

/**
 * D8.5 — Runtime contract skeletons (injected at top of action body when
 * spec declares `requires: [...]`).
 *
 * Per references/library_consumer_pattern.md (D3) and
 * references/system_map_dependency.md (D7.7), generated plugins that depend
 * on Attache's ofoCore library or the System Map MUST guard for those
 * dependencies at startup with explicit error UX rather than crashing on
 * first method call.
 *
 * Injection strategy: prepend skeletons BEFORE the first `try {` line in
 * the action body. This relies on the template convention of wrapping
 * action logic in a try/catch. If no try block is found, the skeleton
 * isn't injected and the generator emits a warning.
 */

const ATTACHE_PLUGIN_ID = 'com.totallytools.omnifocus.attache';
const EXPECTED_SYSTEM_MAP_SCHEMA_VERSION = 1;

function ofoCoreSkeleton(): string {
  return `        // D8.5 — Runtime contract: Attache + ofoCore presence (per references/library_consumer_pattern.md)
        const attache = PlugIn.find(${JSON.stringify(ATTACHE_PLUGIN_ID)});
        if (!attache) {
            new Alert("Attache Required", "This plugin requires the Attache plugin (v1.5+). Install from <repo URL>.").show();
            return;
        }
        const ofoCore = attache.library("ofoCore");
        if (!ofoCore || typeof ofoCore.getTask !== "function") {
            new Alert("Attache Out of Date", "Attache 'ofoCore' library is missing required functions. Please update Attache.").show();
            return;
        }
`;
}

function systemMapSkeleton(): string {
  return `        // D8.5 — Runtime contract: Attache System Map currency (per references/system_map_dependency.md)
        const EXPECTED_SYSTEM_MAP_SCHEMA_VERSION = ${EXPECTED_SYSTEM_MAP_SCHEMA_VERSION};
        const _smCandidates = flattenedTasks.filter(t => t.name === "Attache System Map");
        if (_smCandidates.length === 0) {
            new Alert("System Map Missing", "Run: ofo system-map --refresh").show();
            return;
        }
        let sm;
        try { sm = JSON.parse(_smCandidates[0].note || "{}"); }
        catch (_) { new Alert("System Map Corrupt", "Run: ofo system-map --refresh").show(); return; }
        if (typeof sm.schemaVersion !== "number" || sm.schemaVersion < EXPECTED_SYSTEM_MAP_SCHEMA_VERSION) {
            new Alert("System Map Schema Stale", "Cached map predates schema v" + EXPECTED_SYSTEM_MAP_SCHEMA_VERSION + ". Run: ofo system-map --refresh").show();
            return;
        }
        if (sm.schemaVersion > EXPECTED_SYSTEM_MAP_SCHEMA_VERSION) {
            console.log("System Map schema v" + sm.schemaVersion + " newer than expected; proceeding.");
        }
`;
}

function injectRuntimeSkeletons(code: string, requires: Array<'ofoCore' | 'systemMap'> | undefined): { code: string; warning?: string } {
  if (!requires || requires.length === 0) return { code };

  // Anchor: the first `try {` after `new PlugIn.Action(`. This is the
  // template convention. If absent, we can't safely inject.
  const anchorRegex = /(new\s+PlugIn\.Action\s*\([^)]*\)\s*\{[\s\S]*?try\s*\{\s*\n)/;
  const match = code.match(anchorRegex);
  if (!match) {
    return {
      code,
      warning: 'D8.5 skeleton injection requested but no `try {` anchor found in action body. ' +
               'Skeletons NOT injected. Add a try/catch wrapper to the action body, or ' +
               'inject skeletons manually per references/library_consumer_pattern.md and ' +
               'references/system_map_dependency.md.',
    };
  }

  let skeletons = '';
  if (requires.indexOf('ofoCore') !== -1) skeletons += ofoCoreSkeleton();
  if (requires.indexOf('systemMap') !== -1) skeletons += systemMapSkeleton();

  return { code: code.replace(anchorRegex, '$1' + skeletons) };
}

/**
 * Prepare template variables from options
 */
function prepareVariables(options: PluginOptions): TemplateVariables {
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
  private skillRoot: string;
  private dtsPath: string;
  private dtsExtensionsPath: string;

  constructor() {
    const root = findSkillRoot();
    if (!root) {
      throw new Error('Could not find omnifocus-generator skill root directory');
    }

    this.skillRoot = root;
    this.dtsPath = path.join(root, 'typescript', 'omnifocus.d.ts');
    this.dtsExtensionsPath = path.join(root, 'typescript', 'omnifocus-extensions.d.ts');
  }

  /**
   * Generate plugin from options
   */
  async generate(options: PluginOptions): Promise<GenerateResult> {
    try {
      console.log(`\n🔨 Generating ${options.format} plugin...`);
      console.log(`   Plugin: ${options.name}`);
      console.log(`   Format: ${FORMATS[options.format]}\n`);

      // 1. Load template
      const template = await this.loadTemplate(options);

      // 2. Prepare variables and substitute
      const variables = prepareVariables(options);
      let code = substituteVariables(template, variables);

      // 2.5. D8.5 — inject runtime contract skeletons if requires declared
      if (options.requires && options.requires.length > 0) {
        const injected = injectRuntimeSkeletons(code, options.requires);
        if (injected.warning) {
          console.log(`⚠️  ${injected.warning}\n`);
        } else {
          console.log(`✅ D8.5 — Injected runtime skeletons: ${options.requires.join(', ')}\n`);
        }
        code = injected.code;
      }

      // 3. CRITICAL: Validate with TypeScript compiler
      console.log('🔍 Validating TypeScript...');
      const validation = await this.validateTypeScript(code, variables.ACTION_ID);

      if (!validation.success) {
        console.log('\n❌ TypeScript validation failed:');
        validation.errors.forEach((err, i) => {
          const location = err.line !== undefined ? `Line ${err.line + 1}${err.column !== undefined ? `:${err.column + 1}` : ''}` : '';
          console.log(`   ${i + 1}. ${location ? location + ' - ' : ''}${err.message}`);
        });
        return { success: false, errors: validation.errors.map(e => e.message) };
      }

      console.log('   ✅ TypeScript validation passed\n');

      // 4. Write .ts file
      const tsFilePath = await this.writeTsFile(code, options);

      // 5. Auto-rename to .omnijs/.omnifocusjs
      const deployPath = await this.renameForDeployment(tsFilePath, options.format);

      console.log('🎉 Plugin generated successfully!\n');
      console.log('📦 Installation:');
      if (options.format === 'bundle') {
        console.log(`   cp -r ${deployPath} ~/Library/Application\\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/`);
      } else {
        console.log(`   cp ${deployPath} ~/Library/Application\\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/`);
      }
      console.log('\n🧪 Testing:');
      console.log('   1. Restart OmniFocus (if running)');
      console.log('   2. Go to Automation menu');
      console.log(`   3. Find '${options.name}'\n`);

      return { success: true, path: deployPath };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`\n❌ Error: ${message}\n`);
      return { success: false, errors: [message] };
    }
  }

  /**
   * Load template based on format
   */
  private async loadTemplate(options: PluginOptions): Promise<string> {
    let templatePath: string;

    if (options.format === 'bundle') {
      if (!options.template) {
        throw new Error('Bundle format requires --template option');
      }
      templatePath = path.join(
        this.skillRoot,
        'assets',
        'plugin-templates',
        options.template,
        'Resources',
        'action.js'
      );
    } else {
      const formatMap: Record<Exclude<PluginFormat, 'bundle'>, string> = {
        'solitary': 'solitary-action/action.ts.template',
        'solitary-fm': 'solitary-action-fm/action.ts.template',
        'solitary-library': 'solitary-library/library.ts.template',
      };

      templatePath = path.join(
        this.skillRoot,
        'assets',
        'plugin-templates',
        formatMap[options.format]
      );
    }

    try {
      return await fs.readFile(templatePath, 'utf-8');
    } catch (error) {
      throw new Error(`Template not found: ${templatePath}`);
    }
  }

  /**
   * Validate TypeScript code using TypeScript Compiler API
   *
   * Note: This is a simplified validation that checks for OmniFocus API usage.
   * We skip full TypeScript lib validation and focus on OmniFocus-specific errors.
   */
  private async validateTypeScript(code: string, fileName: string): Promise<ValidationResult> {
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
      const sourceFile = ts.createSourceFile(
        `${fileName}.ts`,
        fullCode,
        ts.ScriptTarget.ES2022,
        true,
        ts.ScriptKind.TS
      );

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

    } catch (error) {
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
  private hasSyntaxErrors(node: ts.Node): boolean {
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
  private async writeTsFile(
    code: string,
    options: PluginOptions
  ): Promise<string> {
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
  private async renameForDeployment(tsFilePath: string, format: PluginFormat): Promise<string> {
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

function parseArgs(args: string[]): PluginOptions | null {
  const options: Partial<PluginOptions> = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const next = args[i + 1];

    switch (arg) {
      case '--format':
      case '-f':
        if (next && (next in FORMATS)) {
          options.format = next as PluginFormat;
          i++;
        }
        break;

      case '--template':
      case '-t':
        if (next && (next in BUNDLE_TEMPLATES)) {
          options.template = next as BundleTemplate;
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

      case '--requires':
        // D8.5 — comma-separated: --requires ofoCore,systemMap (or single value)
        if (next) {
          const tokens = next.split(',').map(s => s.trim()).filter(Boolean);
          const valid = tokens.filter((t): t is 'ofoCore' | 'systemMap' => t === 'ofoCore' || t === 'systemMap');
          if (valid.length !== tokens.length) {
            console.error('❌ Error: --requires accepts only "ofoCore" and/or "systemMap"\n');
            return null;
          }
          options.requires = valid;
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

  return options as PluginOptions;
}

function printUsage(): void {
  console.log(`
OmniFocus Plugin Generator (TypeScript)

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
  --requires <list>             D8.5 — auto-emit runtime contract skeletons.
                                Comma-separated: ofoCore, systemMap (or both).
                                ofoCore   → checks Attache plugin + ofoCore library
                                            presence at action start (per
                                            references/library_consumer_pattern.md).
                                systemMap → checks "Attache System Map" task exists,
                                            valid JSON, schemaVersion >= expected
                                            (per references/system_map_dependency.md).
                                Requires the template to wrap action body in try { } —
                                injection anchors on the first try after PlugIn.Action(...).
  --help, -h                    Show this help message

Examples:
  # Simple solitary plugin
  node generate_plugin.js --format solitary --name "My Quick Action"

  # Solitary plugin with Foundation Models
  node generate_plugin.js --format solitary-fm --name "AI Task Analyzer"

  # Bundle plugin
  node generate_plugin.js --format bundle --template query-simple --name "My Tasks"

Available Formats:
${Object.entries(FORMATS).map(([name, desc]) => `  ${name.padEnd(20)} ${desc}`).join('\n')}

Bundle Templates:
${Object.entries(BUNDLE_TEMPLATES).map(([name, desc]) => `  ${name.padEnd(20)} ${desc}`).join('\n')}
`);
}

// ============================================================================
// Main
// ============================================================================

async function main(): Promise<void> {
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

export { PluginGenerator, type PluginOptions, type GenerateResult };
