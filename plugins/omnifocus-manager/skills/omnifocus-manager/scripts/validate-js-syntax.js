#!/usr/bin/env node

/**
 * JavaScript Syntax Validator
 *
 * Uses Node.js to properly validate JavaScript syntax and report errors.
 * Better than grep/regex for actual syntax validation.
 *
 * Usage:
 *   node validate-js-syntax.js <file.js>
 *   node validate-js-syntax.js <directory>  # validates all .js files
 */

const fs = require('fs');
const path = require('path');
const { Script } = require('vm');

function validateJavaScript(filePath, content) {
    const errors = [];

    try {
        // Use Node's VM Script to validate syntax
        new Script(content, { filename: filePath });
        return { valid: true, errors: [] };
    } catch (error) {
        return {
            valid: false,
            errors: [{
                file: filePath,
                line: error.lineNumber || 'unknown',
                column: error.columnNumber || 'unknown',
                message: error.message,
                stack: error.stack
            }]
        };
    }
}

function validateFile(filePath) {
    if (!fs.existsSync(filePath)) {
        console.error(`❌ File not found: ${filePath}`);
        return false;
    }

    const content = fs.readFileSync(filePath, 'utf8');
    const result = validateJavaScript(filePath, content);

    if (result.valid) {
        console.log(`✅ ${filePath} - Valid syntax`);
        return true;
    } else {
        console.log(`❌ ${filePath} - Syntax errors found:`);
        result.errors.forEach(err => {
            console.log(`   Line ${err.line}, Column ${err.column}: ${err.message}`);
        });
        return false;
    }
}

function findJavaScriptFiles(dir) {
    let files = [];
    const items = fs.readdirSync(dir);

    for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
            files = files.concat(findJavaScriptFiles(fullPath));
        } else if (item.endsWith('.js')) {
            files.push(fullPath);
        }
    }

    return files;
}

function main() {
    const target = process.argv[2];

    if (!target) {
        console.log('Usage: node validate-js-syntax.js <file.js|directory>');
        process.exit(1);
    }

    const stat = fs.statSync(target);
    let files = [];

    if (stat.isDirectory()) {
        files = findJavaScriptFiles(target);
        console.log(`Found ${files.length} JavaScript files to validate\n`);
    } else if (target.endsWith('.js')) {
        files = [target];
    } else {
        console.error('Target must be a .js file or directory');
        process.exit(1);
    }

    let allValid = true;

    for (const file of files) {
        const valid = validateFile(file);
        if (!valid) allValid = false;
    }

    console.log('');
    if (allValid) {
        console.log('✅ All files have valid JavaScript syntax');
        process.exit(0);
    } else {
        console.log('❌ Some files have syntax errors');
        process.exit(1);
    }
}

main();
