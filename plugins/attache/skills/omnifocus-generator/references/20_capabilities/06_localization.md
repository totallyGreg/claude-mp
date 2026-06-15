# Localization

<!-- DRAFT — review during D2 integration -->

**What this covers:** `.lproj` resource files, `.strings` format, manifest localization, action label localization — the full localization setup required for OmniFocus plugins.

**What this does NOT cover:** Unicode or date formatting classes. See `30_api_reference/omnifocus_api.md` for `Formatter.Date` and `Locale`.

---

## 1. First-Stop Solution: Check `ofoCore`

ofoCore does not handle localization. All localization is done in the plugin's file structure.

---

## 2. Plugin Localization Structure

Every `.omnifocusjs` plugin that should appear with correct labels needs:

```
MyPlugin.omnifocusjs/
├── manifest.json
└── Resources/
    ├── en.lproj/
    │   ├── manifest.strings        ← Plugin submenu label
    │   ├── myAction.strings        ← Action labels (one per action)
    │   └── myOtherAction.strings
    └── (other locales: fr.lproj/, de.lproj/, etc.)
```

---

## 3. manifest.strings — Plugin Submenu Name

The plugin submenu name (shown in OmniFocus Automation menu) comes from `manifest.strings`, NOT from `manifest.json`:

```strings
// Resources/en.lproj/manifest.strings
"com.your.bundle.id" = "My Plugin Name";
```

The key is the plugin's bundle identifier from `manifest.json`.

**⚠️ Common failure:** Plugin shows as `com.your.bundle.id` in menu → `manifest.strings` is missing or has wrong key.

---

## 4. Action .strings — Per-Action Labels

Each action needs its own `.strings` file named `<identifier>.strings` where `<identifier>` matches the action's `identifier` in `manifest.json`:

```strings
// Resources/en.lproj/myAction.strings
"label" = "Do the Thing";
"shortLabel" = "Do It";
"mediumLabel" = "Do the Thing";
"longLabel" = "Do the Thing (Long Description)";
```

**⚠️ Common failure:** Action shows as camelCase identifier (e.g. `myAction`) instead of label → `.strings` file is missing, has wrong filename, or has wrong keys.

The `label` field in `manifest.json` alone is insufficient — the `.strings` file is authoritative.

---

## 5. manifest.json — Required Fields

```json
{
  "type": "com.omnigroup.omnifocus2.action",
  "identifier": "com.yourname.myplugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": "Your Name",
  "label": "My Plugin",
  "actions": [
    {
      "identifier": "myAction",
      "label": "Do the Thing"
    }
  ],
  "libraries": [
    {
      "identifier": "myLibrary"
    }
  ]
}
```

- `identifier` at plugin level: bundle ID (used as key in `manifest.strings`)
- `identifier` at action level: must match the `Resources/myAction.js` filename AND the `Resources/en.lproj/myAction.strings` filename

---

## 6. Validation Check

The D8.4 coherence check in `validate-plugin.sh` verifies:
1. Every action identifier in manifest has a matching `Resources/<identifier>.js`
2. Every action has a `Resources/en.lproj/<identifier>.strings`
3. Every key in `manifest.json` `label` fields exists in the default locale `.strings`
4. `manifest.strings` key matches the plugin bundle identifier

---

## 7. Adding a New Locale

1. Create `Resources/fr.lproj/` (or other locale code)
2. Copy `en.lproj/*.strings` files to `fr.lproj/`
3. Translate the values (not the keys)
4. OmniFocus auto-selects based on system language

---

## 8. Reach-Out Trigger

Localization is not documented on omni-automation.com as a standalone API topic. All guidance comes from this doc and the local `omni_automation_guide.md`. If you have a new localization question, check `omni_automation_guide.md` first (Section: "Plugin Name Shows as Bundle ID").
