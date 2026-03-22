/*
 * Phase 0 verification test: cross-plugin library loading
 *
 * Tests whether PlugIn.find("com.totally-tools.ofo-core").library("ofoCore")
 * resolves correctly when called from INSIDE an installed plugin action
 * (as opposed to from an external omnijs-run script like ofo-stub.js).
 *
 * Expected result on success:
 *   Alert showing flagged task count and first task name (or "inbox empty").
 *
 * Expected result on failure:
 *   Alert showing which step failed and why.
 */
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        var report = [];

        // Step 1: find the ofo-core plugin by bundle identifier
        var corePlugin = PlugIn.find("com.totally-tools.ofo-core");
        if (!corePlugin) {
            report.push("FAIL step 1: PlugIn.find() returned null.");
            report.push("ofo-core.omnifocusjs is not installed.");
            new Alert("ofoCore Test: FAILED", report.join("\n")).show();
            return;
        }
        report.push("PASS step 1: PlugIn.find() resolved ofo-core.");

        // Step 2: load the ofoCore library from the found plugin
        var ofoCore;
        try {
            ofoCore = corePlugin.library("ofoCore");
        } catch (e) {
            report.push("FAIL step 2: corePlugin.library('ofoCore') threw: " + e.message);
            new Alert("ofoCore Test: FAILED", report.join("\n")).show();
            return;
        }
        if (!ofoCore) {
            report.push("FAIL step 2: corePlugin.library('ofoCore') returned null.");
            new Alert("ofoCore Test: FAILED", report.join("\n")).show();
            return;
        }
        report.push("PASS step 2: library('ofoCore') loaded.");

        // Step 3: call dispatch() with a known action
        var result;
        try {
            result = ofoCore.dispatch({ action: "ofo-list", filter: "flagged" });
        } catch (e) {
            report.push("FAIL step 3: ofoCore.dispatch() threw: " + e.message);
            new Alert("ofoCore Test: FAILED", report.join("\n")).show();
            return;
        }
        if (!result || result.success === false) {
            report.push("FAIL step 3: dispatch returned error: " + JSON.stringify(result));
            new Alert("ofoCore Test: FAILED", report.join("\n")).show();
            return;
        }
        report.push("PASS step 3: dispatch() returned success.");

        // Report
        var tasks = result.tasks || [];
        report.push("Flagged task count: " + tasks.length);
        if (tasks.length > 0) {
            report.push("First task: " + tasks[0].name);
        }
        report.push("\nPlatform: " + (typeof Device !== 'undefined' ? Device.current.type : 'unknown'));

        new Alert("ofoCore Test: ALL PASSED ✓", report.join("\n")).show();
    });

    action.validate = function(selection) {
        return true;
    };

    return action;
})();
