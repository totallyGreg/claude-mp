#!/usr/bin/osascript -l JavaScript
/**
 * Perspective Configuration Script for OmniFocus
 *
 * Applies, modifies, and inspects perspective filter rules using the
 * archivedFilterRules API (OmniFocus v4.2+).
 *
 * Usage:
 *     osascript -l JavaScript scripts/perspective-config.js --action <action> [options]
 *
 * Actions:
 *     show                 Show current filter rules for a named perspective
 *     apply                Apply custom filter rules JSON to a perspective
 *     apply-template       Apply a named template to a perspective
 *     list-templates       List available perspective templates
 *
 * Options:
 *     --name <name>        Perspective name (required for show, apply, apply-template)
 *     --rules <json>       JSON array of filter rules (for apply action)
 *     --aggregation <agg>  Filter aggregation: all, any, none (default: all)
 *     --template <name>    Template name (for apply-template action)
 *
 * Examples:
 *     osascript -l JavaScript scripts/perspective-config.js --action show --name "Next Actions"
 *     osascript -l JavaScript scripts/perspective-config.js --action apply-template --name "Next Actions" --template next-actions
 *     osascript -l JavaScript scripts/perspective-config.js --action apply --name "My View" --rules '[{"actionAvailability":"available"}]'
 *     osascript -l JavaScript scripts/perspective-config.js --action list-templates
 *
 * @version 1.0.0
 */

ObjC.import('stdlib');
ObjC.import('Foundation');

// ============================================================================
// Argument Parsing
// ============================================================================

function parseArgs(argv) {
    var args = { action: 'help' };

    for (var i = 0; i < argv.length; i++) {
        var arg = argv[i];
        if (arg === '--action' && i + 1 < argv.length) {
            args.action = argv[++i];
        } else if (arg === '--name' && i + 1 < argv.length) {
            args.name = argv[++i];
        } else if (arg === '--rules' && i + 1 < argv.length) {
            args.rules = argv[++i];
        } else if (arg === '--aggregation' && i + 1 < argv.length) {
            args.aggregation = argv[++i];
        } else if (arg === '--template' && i + 1 < argv.length) {
            args.template = argv[++i];
        }
    }

    return args;
}

// ============================================================================
// Template Definitions
// ============================================================================

/**
 * Canonical GTD perspective templates.
 * Filter rules use the archivedFilterRules format.
 * Tag-based rules use placeholder names resolved at apply time.
 */
var TEMPLATES = {
    'next-actions': {
        description: 'Available next actions in active projects',
        filterRules: [
            { actionAvailability: 'available' },
            { projectStatus: 'active' }
        ],
        aggregation: 'all'
    },
    'waiting-for': {
        description: 'Delegated items tagged with Waiting',
        filterRules: [
            { actionAvailability: 'remaining' },
            { _tagName: 'Waiting' }
        ],
        aggregation: 'all'
    },
    'flagged-available': {
        description: 'Flagged items that are actionable right now',
        filterRules: [
            { actionAvailability: 'available' },
            { actionFlagged: true }
        ],
        aggregation: 'all'
    },
    'stalled-projects': {
        description: 'Active projects with no available next actions',
        filterRules: [
            { projectStatus: 'active' },
            { projectHasNoAvailableActions: true }
        ],
        aggregation: 'all'
    },
    'due-this-week': {
        description: 'Tasks due within 7 days',
        filterRules: [
            { actionAvailability: 'remaining' },
            { actionDueSoon: 7 }
        ],
        aggregation: 'all'
    },
    'someday-maybe': {
        description: 'On-hold projects for periodic review',
        filterRules: [
            { projectStatus: 'onHold' }
        ],
        aggregation: 'all'
    },
    'recently-completed': {
        description: 'Tasks completed in the last 7 days',
        filterRules: [
            { actionCompletedWithinDays: 7 }
        ],
        aggregation: 'all'
    },
    'overdue': {
        description: 'Past-due items needing triage',
        filterRules: [
            { actionAvailability: 'remaining' },
            { actionOverdue: true }
        ],
        aggregation: 'all'
    }
};

// ============================================================================
// Tag Resolution
// ============================================================================

/**
 * Resolve _tagName placeholders in filter rules to actual tag IDs.
 * Rules with { _tagName: "Name" } become { actionHasAnyOfTags: ["tagID"] }.
 * @param {Array} rules - Filter rules array
 * @returns {Array} Rules with tag names resolved to IDs
 */
function resolveTagNames(rules) {
    var app = Application('OmniFocus');
    var doc = app.defaultDocument;

    return rules.map(function(rule) {
        if (rule._tagName) {
            var tagName = rule._tagName;
            var tag = doc.flattenedTags.whose({ name: tagName })[0];
            if (!tag) {
                throw new Error('Tag not found: "' + tagName + '". Create it first in OmniFocus.');
            }
            return { actionHasAnyOfTags: [tag.id()] };
        }
        return rule;
    });
}

// ============================================================================
// Actions
// ============================================================================

function showPerspective(name) {
    var p = Perspective.Custom.byName(name);
    if (!p) {
        return { success: false, error: 'Perspective not found: "' + name + '". Custom perspectives: ' + Perspective.Custom.all.map(function(c) { return c.name; }).join(', ') };
    }

    var rules = null;
    var aggregation = null;
    try { rules = p.archivedFilterRules; } catch (e) {}
    try { aggregation = p.archivedTopLevelFilterAggregation; } catch (e) {}

    return {
        success: true,
        action: 'show',
        perspective: {
            name: p.name,
            identifier: p.identifier,
            filterRules: rules,
            aggregation: aggregation,
            link: 'omnifocus:///perspective/' + encodeURIComponent(p.name)
        }
    };
}

function applyRules(name, rulesJson, aggregation) {
    var p = Perspective.Custom.byName(name);
    if (!p) {
        return { success: false, error: 'Perspective not found: "' + name + '". Create it first in OmniFocus (Perspectives → +).' };
    }

    var rules;
    try {
        rules = JSON.parse(rulesJson);
    } catch (e) {
        return { success: false, error: 'Invalid JSON rules: ' + e.toString() };
    }

    if (!Array.isArray(rules)) {
        return { success: false, error: 'Rules must be a JSON array of filter objects.' };
    }

    // Resolve any _tagName placeholders
    try {
        rules = resolveTagNames(rules);
    } catch (e) {
        return { success: false, error: e.toString() };
    }

    // Save previous rules for undo reference
    var previousRules = null;
    try { previousRules = p.archivedFilterRules; } catch (e) {}

    // Apply new rules
    p.archivedFilterRules = rules;
    if (aggregation) {
        p.archivedTopLevelFilterAggregation = aggregation;
    }

    return {
        success: true,
        action: 'apply',
        perspective: name,
        appliedRules: rules,
        aggregation: aggregation || null,
        previousRules: previousRules,
        link: 'omnifocus:///perspective/' + encodeURIComponent(name)
    };
}

function applyTemplate(name, templateName) {
    var template = TEMPLATES[templateName];
    if (!template) {
        return { success: false, error: 'Unknown template: "' + templateName + '". Available: ' + Object.keys(TEMPLATES).join(', ') };
    }

    var p = Perspective.Custom.byName(name);
    if (!p) {
        return { success: false, error: 'Perspective not found: "' + name + '". Create it first in OmniFocus (Perspectives → +).' };
    }

    // Resolve tag names and apply
    var rules;
    try {
        rules = resolveTagNames(template.filterRules);
    } catch (e) {
        return { success: false, error: e.toString() };
    }

    // Save previous rules for undo reference
    var previousRules = null;
    try { previousRules = p.archivedFilterRules; } catch (e) {}

    p.archivedFilterRules = rules;
    p.archivedTopLevelFilterAggregation = template.aggregation;

    return {
        success: true,
        action: 'apply-template',
        perspective: name,
        template: templateName,
        description: template.description,
        appliedRules: rules,
        aggregation: template.aggregation,
        previousRules: previousRules,
        link: 'omnifocus:///perspective/' + encodeURIComponent(name)
    };
}

function listTemplates() {
    var templates = [];
    for (var key in TEMPLATES) {
        templates.push({
            name: key,
            description: TEMPLATES[key].description,
            ruleCount: TEMPLATES[key].filterRules.length,
            aggregation: TEMPLATES[key].aggregation
        });
    }

    return {
        success: true,
        action: 'list-templates',
        count: templates.length,
        templates: templates
    };
}

function getHelp() {
    return {
        success: true,
        usage: 'osascript -l JavaScript scripts/perspective-config.js --action <action> [options]',
        actions: {
            'show': 'Show current filter rules for a perspective (--name <name>)',
            'apply': 'Apply custom filter rules to a perspective (--name <name> --rules <json> [--aggregation all|any|none])',
            'apply-template': 'Apply a named template (--name <name> --template <template>)',
            'list-templates': 'List available perspective templates'
        },
        templates: Object.keys(TEMPLATES)
    };
}

// ============================================================================
// Main Entry Point
// ============================================================================

function run(argv) {
    try {
        var args = parseArgs(argv);
        var result;

        switch (args.action) {
            case 'show':
                if (!args.name) return JSON.stringify({ success: false, error: 'Missing --name parameter' }, null, 2);
                result = showPerspective(args.name);
                break;
            case 'apply':
                if (!args.name) return JSON.stringify({ success: false, error: 'Missing --name parameter' }, null, 2);
                if (!args.rules) return JSON.stringify({ success: false, error: 'Missing --rules parameter' }, null, 2);
                result = applyRules(args.name, args.rules, args.aggregation);
                break;
            case 'apply-template':
                if (!args.name) return JSON.stringify({ success: false, error: 'Missing --name parameter' }, null, 2);
                if (!args.template) return JSON.stringify({ success: false, error: 'Missing --template parameter' }, null, 2);
                result = applyTemplate(args.name, args.template);
                break;
            case 'list-templates':
                result = listTemplates();
                break;
            case 'help':
                result = getHelp();
                break;
            default:
                result = { success: false, error: 'Unknown action: ' + args.action + '. Use --action help for usage.' };
        }

        return JSON.stringify(result, null, 2);
    } catch (e) {
        return JSON.stringify({ success: false, error: e.toString() });
    }
}
