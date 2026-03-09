/**
 * Preferences Manager Library
 *
 * Hybrid persistence for cached system preferences:
 * - Synced store (authoritative): Task-note JSON in "Synced Preferences" project
 * - Local cache (fast reads): Native Preferences API (device-local)
 *
 * Read: Preferences API first (cache hit) -> task note (cache miss) -> write back
 * Write: Both simultaneously
 *
 * Security: Strips task names, AI reasoning, recommendations, and internal IDs
 * before persisting. See STRIP_FIELDS and stripNestedField().
 *
 * @version 1.0.0
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    const TASK_NAME = "Attache System Map";
    const CURRENT_SCHEMA = 1;
    const STRIP_FIELDS = ["tasks", "aiReasoning", "recommendations"];

    // IIFE closure cache for preference task reference
    let _cachedTask = null;

    /**
     * Locate the preference task in Synced Preferences project.
     * Searches regardless of completion/dropped status.
     * Caches the reference in IIFE closure scope.
     *
     * @returns {Task|null} The preference task or null
     */
    lib.findPreferenceTask = function() {
        if (_cachedTask && _cachedTask.name === TASK_NAME) return _cachedTask;
        const project = flattenedProjects.byName("Synced Preferences");
        if (!project) return null;
        _cachedTask = project.flattenedTasks.find(t => t.name === TASK_NAME) || null;
        return _cachedTask;
    };

    /**
     * Read cached preferences using hybrid strategy.
     * @returns {Object|null} Parsed preferences or null if not found/corrupt
     */
    lib.read = function() {
        // Try local cache first (fast, no parse overhead on hit)
        const prefs = new Preferences(null);
        const cached = prefs.readString("systemMap");
        if (cached) {
            try { return JSON.parse(cached); } catch {}
        }
        // Fall back to synced task note
        const task = lib.findPreferenceTask();
        if (!task || !task.note) return null;
        try {
            const data = JSON.parse(task.note);
            // Write back to local cache for next time
            prefs.write("systemMap", task.note);
            return data;
        } catch { return null; }
    };

    /**
     * Check if cached preferences exist.
     * @returns {boolean}
     */
    lib.hasPreferences = function() {
        return lib.read() !== null;
    };

    /**
     * Write preferences to both synced and local stores.
     * Strips sensitive fields before persisting.
     *
     * @param {Object} data - System map data to cache
     */
    lib.write = function(data) {
        // Deep copy and strip sensitive fields
        const safe = JSON.parse(JSON.stringify(data));
        STRIP_FIELDS.forEach(field => delete safe[field]);
        stripNestedField(safe, "aiReasoning");
        stripNestedField(safe, "primaryKey");

        // Add metadata
        safe.schemaVersion = CURRENT_SCHEMA;
        safe.lastWritten = new Date().toISOString();
        safe.lastWrittenDevice = Device.current.name;

        const json = JSON.stringify(safe, null, 2);

        // Write to synced task note (authoritative)
        const task = lib.findPreferenceTask() || lib.getOrCreate();
        task.note = json;

        // Write to local cache (fast reads)
        new Preferences(null).write("systemMap", json);
    };

    /**
     * Find or create the preference task in Synced Preferences project.
     * @returns {Task} The preference task
     * @throws {Error} If Synced Preferences project not found
     */
    lib.getOrCreate = function() {
        const existing = lib.findPreferenceTask();
        if (existing) return existing;

        const project = flattenedProjects.byName("Synced Preferences");
        if (!project) {
            throw new Error(
                "Synced Preferences project not found.\n\n" +
                "Please install the SyncedPreferences plugin or create a " +
                "project named \"Synced Preferences\" to enable preference caching."
            );
        }

        const task = new Task(TASK_NAME, project);
        _cachedTask = task;
        return task;
    };

    /**
     * Recursively strip a named field from an object tree.
     * Used to remove aiReasoning and primaryKey before persisting.
     */
    function stripNestedField(obj, field) {
        if (!obj || typeof obj !== "object") return;
        delete obj[field];
        for (const value of Object.values(obj)) {
            if (Array.isArray(value)) {
                value.forEach(item => stripNestedField(item, field));
            } else if (typeof value === "object" && value !== null) {
                stripNestedField(value, field);
            }
        }
    }

    return lib;
})();
