#!/usr/bin/env node
/**
 * JXA Anti-Pattern Validator
 *
 * Scans JXA source files for known anti-patterns using regex rules
 * defined in jxa-antipatterns.json. Exits 0 if clean, 1 if violations found.
 *
 * Usage:
 *   node validate-jxa-patterns.js <file-or-directory>
 *   node validate-jxa-patterns.js scripts/libraries/jxa/
 *   node validate-jxa-patterns.js scripts/manage_omnifocus.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const configPath = path.join(__dirname, 'jxa-antipatterns.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const allRules = [...config.antipatterns, ...config.blocked_always];

function scanFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    const violations = [];

    lines.forEach((line, i) => {
        const trimmed = line.trim();
        // Skip comments and known-safe infrastructure (loadLibrary's eval)
        if (trimmed.startsWith('//') || trimmed.startsWith('*') || trimmed.startsWith('/*')) return;
        if (trimmed === 'return eval(content.js);') return;

        for (const rule of allRules) {
            const regex = new RegExp(rule.pattern);
            if (regex.test(line)) {
                violations.push({
                    file: filePath,
                    line: i + 1,
                    rule: rule.id,
                    severity: rule.severity,
                    message: rule.message,
                    code: trimmed
                });
            }
        }
    });

    return violations;
}

function collectFiles(target) {
    const stat = fs.statSync(target);
    if (stat.isFile()) return target.endsWith('.js') ? [target] : [];
    if (stat.isDirectory()) {
        return fs.readdirSync(target, { recursive: true })
            .filter(f => f.endsWith('.js'))
            .map(f => path.join(target, f));
    }
    return [];
}

// Main
const target = process.argv[2];
if (!target) {
    console.error('Usage: node validate-jxa-patterns.js <file-or-directory>');
    process.exit(2);
}

const files = collectFiles(target);
let allViolations = [];

for (const file of files) {
    allViolations = allViolations.concat(scanFile(file));
}

if (allViolations.length === 0) {
    console.log(`✅ ${files.length} file(s) scanned — no anti-patterns found`);
    process.exit(0);
} else {
    console.error(`❌ ${allViolations.length} anti-pattern violation(s) found:\n`);
    for (const v of allViolations) {
        console.error(`  ${v.file}:${v.line} [${v.rule}] ${v.message}`);
        console.error(`    > ${v.code}\n`);
    }
    if (process.env.JSON_OUTPUT) {
        console.log(JSON.stringify(allViolations, null, 2));
    }
    process.exit(1);
}
