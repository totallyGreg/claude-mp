/**
 * Preferences Manager Library
 *
 * Hybrid persistence for cached system preferences:
 * - Synced store (authoritative): Task-note JSON in SyncedPreferences plugin project
 * - Local cache (fast reads): Native Preferences API (device-local)
 *
 * The SyncedPreferences plugin (com.KaitlinSalzke.SyncedPrefLibrary) stores data
 * in a task note inside a project named "⚙️ Synced Preferences", itself inside a
 * folder of the same name. Use folderNamed() + folder.projectNamed() to locate it —
 * flattenedProjects.byName() does not match this structure reliably.
 *
 * Read: Preferences API first (cache hit) -> task note (cache miss) -> write back
 * Write: Both simultaneously
 *
 * Security: Strips task names, AI reasoning, recommendations, and internal IDs
 * before persisting. See STRIP_FIELDS and stripNestedField().
 *
 * @version 1.0.1
 */

(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    const TASK_NAME = "Attache System Map";
    const SYNCED_PREFS_NAME = "⚙️ Synced Preferences";
    const CURRENT_SCHEMA = 1;
    const STRIP_FIELDS = ["tasks", "aiReasoning", "recommendations"];

    // Preferences must NOT be constructed at library IIFE top level — doing so disables
    // all plugin actions. Use lazy initialization: construct on first use inside a function.
    // Explicit bundle ID required (new Preferences() without args also throws in library context).
    // Pattern confirmed by Templates.omnifocusjs (new Preferences('com.KaitlinSalzke.Templates')
    // called inside lib methods, never at IIFE scope).
    let _prefs = null;
    function getPrefs() {
        if (!_prefs) _prefs = new Preferences("com.totallytools.omnifocus.attache");
        return _prefs;
    }

    // IIFE closure cache for preference task reference
    let _cachedTask = null;

    /**
     * Locate the ⚙️ Synced Preferences project via folder lookup,
     * matching the SyncedPreferences plugin's actual storage structure.
     * Auto-creates the folder and project if missing.
     *
     * @returns {Project} The synced preferences project
     */
    function getSyncedProject() {
        // @ts-ignore — Folder(name) works at runtime; position defaults to root
        const folder = folderNamed(SYNCED_PREFS_NAME) || new Folder(SYNCED_PREFS_NAME);
        return folder.projectNamed(SYNCED_PREFS_NAME) || new Project(SYNCED_PREFS_NAME, folder);
    }

    /**
     * Locate the preference task. Searches by taskNamed for efficiency.
     * Caches the reference in IIFE closure scope.
     *
     * @returns {Task|null} The preference task or null
     */
    lib.findPreferenceTask = function() {
        if (_cachedTask && _cachedTask.name === TASK_NAME) return _cachedTask;
        const project = getSyncedProject();
        _cachedTask = project.taskNamed(TASK_NAME) || null;
        return _cachedTask;
    };

    /**
     * Read cached preferences using hybrid strategy.
     * @returns {Object|null} Parsed preferences or null if not found/corrupt
     */
    lib.read = function() {
        // Try local cache first (fast, no parse overhead on hit)
        const cached = getPrefs().readString("systemMap");
        if (cached) {
            try { return JSON.parse(cached); } catch {}
        }
        // Fall back to synced task note
        const task = lib.findPreferenceTask();
        if (!task || !task.note) return null;
        try {
            const data = JSON.parse(task.note);
            // Write back to local cache for next time
            getPrefs().write("systemMap", task.note);
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
        getPrefs().write("systemMap", json);
    };

    /**
     * Find or create the preference task, auto-creating the synced project if needed.
     * @returns {Task} The preference task
     */
    lib.getOrCreate = function() {
        const existing = lib.findPreferenceTask();
        if (existing) return existing;

        const task = new Task(TASK_NAME, getSyncedProject());
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
