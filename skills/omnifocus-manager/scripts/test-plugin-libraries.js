#!/usr/bin/osascript -l JavaScript

/**
 * Plugin Library Testing Script
 *
 * Tests that plugin libraries can be loaded before installation in OmniFocus.
 * This simulates library loading to catch issues early.
 *
 * Usage:
 *   osascript -l JavaScript test-plugin-libraries.js /path/to/Plugin.omnifocusjs
 *
 * Note: This tests loading only. Full runtime testing requires actual OmniFocus installation.
 */

ObjC.import('Foundation');

function run(argv) {
    try {
        if (argv.length === 0) {
            console.log("Usage: osascript -l JavaScript test-plugin-libraries.js <path-to-plugin.omnifocusjs>");
            console.log("Example: osascript -l JavaScript test-plugin-libraries.js MyPlugin.omnifocusjs");
            return "USAGE_ERROR";
        }

        const pluginPath = argv[0];
        console.log("=== Testing Plugin Libraries ===\n");
        console.log("Plugin: " + pluginPath + "\n");

        // Read manifest.json
        const manifestPath = pluginPath + "/manifest.json";
        const manifestContent = $.NSString.stringWithContentsOfFileEncodingError(
            $(manifestPath),
            $.NSUTF8StringEncoding,
            null
        );

        if (!manifestContent) {
            console.log("❌ ERROR: Could not read manifest.json from " + manifestPath);
            return "FAILED";
        }

        const manifest = JSON.parse(manifestContent.js);

        // Check if plugin has libraries
        if (!manifest.libraries || manifest.libraries.length === 0) {
            console.log("ℹ️  Plugin has no libraries declared in manifest.json");
            console.log("✅ Nothing to test\n");
            return "SUCCESS";
        }

        console.log("Found " + manifest.libraries.length + " library declaration(s)\n");

        let allTestsPassed = true;

        // Test each library
        manifest.libraries.forEach((lib, index) => {
            const libraryId = lib.identifier;
            console.log("Test " + (index + 1) + ": Loading '" + libraryId + "' library...");

            const libraryPath = pluginPath + "/Resources/" + libraryId + ".js";

            // Read library file
            const libraryContent = $.NSString.stringWithContentsOfFileEncodingError(
                $(libraryPath),
                $.NSUTF8StringEncoding,
                null
            );

            if (!libraryContent) {
                console.log("❌ FAILED: Could not read library file: " + libraryPath);
                allTestsPassed = false;
                return;
            }

            // Try to evaluate library
            try {
                const library = eval(libraryContent.js);

                if (!library) {
                    console.log("❌ FAILED: Library returned null or undefined");
                    allTestsPassed = false;
                    return;
                }

                if (typeof library !== 'object') {
                    console.log("❌ FAILED: Library did not return an object (got: " + typeof library + ")");
                    allTestsPassed = false;
                    return;
                }

                // Get library functions
                const functions = Object.keys(library).filter(key => typeof library[key] === 'function');

                if (functions.length === 0) {
                    console.log("⚠️  WARNING: Library has no functions");
                } else {
                    console.log("✅ " + libraryId + " library loaded successfully");
                    console.log("   Functions: " + functions.join(', '));
                }

            } catch (error) {
                console.log("❌ FAILED: Error evaluating library: " + error.message);
                if (error.stack) {
                    console.log("   Stack: " + error.stack);
                }
                allTestsPassed = false;
                return;
            }

            console.log("");
        });

        // Summary
        if (allTestsPassed) {
            console.log("=== All Tests Passed! ===\n");
            console.log("Next Steps:");
            console.log("1. Install plugin in OmniFocus:");
            console.log("   open " + pluginPath);
            console.log("");
            console.log("2. Test in OmniFocus Automation Console (Cmd+Opt+Ctrl+C):");
            console.log("   const plugin = PlugIn.find('" + manifest.identifier + "');");
            console.log("   const library = plugin.library('libraryName');");
            console.log("   console.log('Library loaded:', library !== null);");
            console.log("");
            return "SUCCESS";
        } else {
            console.log("=== Tests Failed ===\n");
            console.log("Fix the errors above and try again.\n");
            return "FAILED";
        }

    } catch (error) {
        console.log("\n❌ FATAL ERROR: " + error.message);
        if (error.stack) {
            console.log(error.stack);
        }
        return "FAILED";
    }
}
