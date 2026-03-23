/**
 * System Setup - Discover and cache OmniFocus system structure
 *
 * Runs system discovery (rule-based + optional AI enhancement),
 * caches the result via preferencesManager for use by other actions,
 * and displays the cached system map.
 *
 * Replaces discoverSystem for Attache. Adds persistent caching.
 *
 * Requirements:
 * - OmniFocus 4.8+
 * - For AI features: macOS 26+, Apple Silicon (M1 or later)
 */

(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        const discovery = this.plugIn.library("systemDiscovery");
        const prefsManager = this.plugIn.library("preferencesManager");
        const fmUtils = this.plugIn.library("foundationModelsUtils");

        try {
            // Migration advisory: check for absorbed plugins on first run
            const existing = prefsManager.read();
            if (!existing) {
                const absorbedBundleIDs = [
                    "com.totallytools.omnifocus.ai-task-analyzer",
                    "com.totallytools.omnifocus.completed-tasks-summary",
                    "com.totallytools.omnifocus.overview",
                    "com.example.todaystasks"
                ];
                const installed = absorbedBundleIDs.filter(id =>
                    PlugIn.all.some(p => p.identifier === id)
                );
                if (installed.length > 0) {
                    const advisory = new Alert("Migration Advisory",
                        `Attache replaces these installed plugins:\n\n` +
                        installed.map(id => `- ${id}`).join('\n') +
                        `\n\nAfter verifying Attache works, you can remove them ` +
                        `from your OmniFocus Automation folder.`
                    );
                    advisory.addOption("Continue Setup");
                    await advisory.show();
                }
            }

            // Configuration form
            const form = new Form();

            // @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
            const depthField = new Form.Field.Option(
                "depth", "Discovery Depth",
                ["quick", "full"],
                ["Quick (structure + GTD health)", "Full (includes task analysis)"],
                "quick"
            );
            form.addField(depthField);

            if (fmUtils.isAvailable()) {
                form.addField(new Form.Field.Checkbox(
                    "useAI", "Use Apple Intelligence for semantic analysis", true
                ));
            }

            if (existing) {
                form.addField(new Form.Field.Checkbox(
                    "rediscover", "Re-discover system (overwrites cached map)", false
                ));
            }

            const formResult = await form.show("System Setup", existing ? "Update" : "Discover");
            if (!formResult) return;

            const depth = formResult.values["depth"];
            const useAI = formResult.values["useAI"] || false;
            const rediscover = existing ? (formResult.values["rediscover"] || false) : true;

            if (existing && !rediscover) {
                // Show existing cached data
                const summary = discovery.generateSummary(existing);
                let subtitle = "";
                if (existing.lastWritten) {
                    subtitle += `\n\nLast updated: ${new Date(existing.lastWritten).toLocaleString()}`;
                }
                if (existing.lastWrittenDevice) {
                    subtitle += ` (from ${existing.lastWrittenDevice})`;
                }

                const alert = new Alert("Cached System Map", summary + subtitle);
                alert.addOption("Copy to Clipboard");
                alert.addOption("Done");
                const choice = await alert.show();
                if (choice === 0) {
                    Pasteboard.general.string = summary;
                }
                return;
            }

            // Run discovery
            let systemMap = discovery.discoverSystem({ depth: depth });

            // AI enhancement if requested and available
            if (useAI && fmUtils.isAvailable()) {
                try {
                    const session = fmUtils.createSession();
                    const aiInsights = await discovery.discoverWithAI(session, systemMap);
                    systemMap = discovery.mergeAIInsights(systemMap, aiInsights);
                } catch (aiError) {
                    console.error("AI enhancement failed:", aiError);
                }
            }

            // Cache the result
            prefsManager.write(systemMap);

            // Show summary
            const summary = discovery.generateSummary(systemMap);
            const alert = new Alert("Setup",
                summary + "\n\nSystem map cached for future use."
            );
            alert.addOption("Copy to Clipboard");
            alert.addOption("Done");
            const choice = await alert.show();
            if (choice === 0) {
                Pasteboard.general.string = summary;
            }

        } catch (error) {
            console.error("System Setup error:", error);
            const errorAlert = new Alert("System Setup Error", error.message);
            errorAlert.show();
        }
    });

    // Always available — discovery works without AI
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
