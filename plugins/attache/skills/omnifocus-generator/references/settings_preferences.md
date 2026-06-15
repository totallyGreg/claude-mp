# Settings and Preferences

<!-- DRAFT — review during D2 integration -->

**What this covers:** OmniFocus `Settings` class (database-level preferences), `Preferences` (plugin-level, ephemeral), and SyncedPreferences (cross-device sync). Does NOT cover user convention truth — that lives in the System Map.

**What this does NOT cover:** System Map conventions (`waitingTag`, `somedayFolder`, etc.). See `system_map_dependency.md` and `attache-analyst/references/system_map_schema.md`.

---

## 1. First-Stop Solution: Check `ofoCore`

ofoCore exposes `getSystemMap()` / `ofo system-map` for convention reading. For ephemeral preferences (coaching cadence, last-run timestamp), use `Preferences` directly. For cross-device config, use SyncedPreferences.

**Critical rule:** User convention truth (waiting tag, someday folder) comes from the **System Map**, NOT from Preferences. `preferencesManager` is for ephemeral learning only.

---

## 2. OmniFocus `Settings` (Database Settings)

These are OmniFocus's own settings, stored in the database and synced.

```js
var s = database.settings;

// Enumerate available keys
s.keys.forEach(function(key) { console.log(key); });

// Read a setting
var val = s.objectForKey("com.omnigroup.OmniFocus2.DefaultDeferDate");
var bool = s.boolForKey("com.omnigroup.OmniFocus2.SomeBoolean");
var num = s.integerForKey("com.omnigroup.OmniFocus2.SomeNumber");

// Check if non-default
s.hasNonDefaultObjectForKey("keyName");   // → Boolean

// Get default value
s.defaultObjectForKey("keyName");          // → value | null

// Write a setting
s.setObjectForKey("value", "keyName");
s.setBoolForKey(true, "keyName");
s.setIntegerForKey(42, "keyName");
```

**⚠️ Most Settings keys are internal/undocumented.** Avoid writing to them unless you've confirmed the key and validated the effect. Reading is generally safe.

---

## 3. `Preferences` (Plugin-Level, Ephemeral)

Preferences objects store data locally per-plugin. They do NOT sync across devices.

```js
// Inside a plugin action or library function — NOT at library IIFE top level
var prefs = new Preferences("com.yourname.myplugin");

// Read/write
prefs.readString("lastUsed");          // → String | null
prefs.write("lastUsed", new Date().toISOString());

prefs.readBoolean("enabled");          // → Boolean | null
prefs.write("enabled", true);

prefs.readNumber("count");             // → Number | null
prefs.write("count", 42);

// Remove a key
prefs.remove("lastUsed");
```

**⚠️ DO NOT construct `new Preferences()` at the top level of a library IIFE.** This causes ALL plugin actions to be disabled silently. Always construct inside a function:

```js
// WRONG — will break all actions
(function() {
  var prefs = new Preferences("com.x.y");   // ❌ top-level API call
  var lib = new PlugIn.Library(...);
  lib.getSetting = function() { return prefs.readString("key"); };
  return lib;
})();

// RIGHT — lazy init
(function() {
  var _prefs = null;
  function getPrefs() {
    if (!_prefs) _prefs = new Preferences("com.x.y");
    return _prefs;
  }
  var lib = new PlugIn.Library(...);
  lib.getSetting = function() { return getPrefs().readString("key"); };
  return lib;
})();
```

---

## 4. SyncedPreferences (Cross-Device Config)

SyncedPreferences stores data in an OmniFocus project so it syncs via OmniFocus Sync. Requires the SyncedPreferences community plugin installed.

```js
// Access
var syncedPrefs = PlugIn.find("com.omnigroup.omnifocus2.sharedsettings")
  .library("SyncedPreferences");

// Read/write (key-value, JSON-serializable)
syncedPrefs.write("myPlugin.preference", "value");
var val = syncedPrefs.read("myPlugin.preference");   // → JSON value | null
```

**Location quirk:** The project is named `"⚙️ Synced Preferences"` (with emoji) inside a folder of the same name. When looking up the project directly:

```js
// CORRECT lookup approach
var folder = library.folderNamed("⚙️ Synced Preferences");
var project = folder ? folder.projectNamed("⚙️ Synced Preferences") : null;

// WRONG — byName doesn't match the same way
// flattenedProjects.byName("⚙️ Synced Preferences")  ← may not find it
```

**When to use vs. Preferences:**
- Ephemeral, device-local (last-run date, UI state) → `Preferences`  
- Shared across devices (user config that should survive reinstall) → `SyncedPreferences`  
- Convention truth (waiting tag, someday folder) → **System Map** (via `ofo system-map`)

---

## 5. Reach-Out Trigger

```
WebFetch https://omni-automation.com/omnifocus/settings.html
Prompt: "List all documented Settings keys for OmniFocus with their types and descriptions."
```

For Preferences and SyncedPreferences, the local `omni_automation_guide.md` (section: "Storing Preferences") has the full usage guide. No WebFetch needed.
