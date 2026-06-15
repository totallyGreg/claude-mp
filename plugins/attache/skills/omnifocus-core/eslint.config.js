// ESLint flat config for OmniFocus Omni Automation plugin code.
//
// D8.2 — globals exhaustively cross-referenced against
// ../typescript/omnifocus.d.ts so `no-undef` can be enforced as `error`
// without false positives on legitimate PlugIn API references.
//
// Scope: this config targets PLUGIN code (Resources/*.js inside .omnifocusjs
// bundles and the intermediate compiled output that becomes plugin code).
// It does NOT target the Node.js CLI (ofo-cli.js, build/ofo-cli.js) which
// uses ES module syntax and is validated by tsc strict mode (D8.1) instead.
//
// Rule philosophy:
// - `no-undef: error` — catches typos like `flattenedTaks` at lint time.
//   Highest-ROI single change for generator output safety.
// - `no-unused-vars: warn` — surfaces dead code without erroring on
//   legitimate unused action handler params (`(selection) => {...}`) or
//   catch parameters named `_`.

const pluginGlobals = {
  // === OmniFocus PlugIn API — Classes (per omnifocus.d.ts) ===
  ActiveObject: "readonly",
  Alert: "readonly",
  Application: "readonly",
  ApplyResult: "readonly",
  Calendar: "readonly",
  Color: "readonly",
  ColorSpace: "readonly",
  Console: "readonly",
  ContentTree: "readonly",
  Credentials: "readonly",
  Data: "readonly",
  Database: "readonly",
  DatabaseDocument: "readonly",
  DatabaseObject: "readonly",
  DateComponents: "readonly",
  DatedObject: "readonly",
  DateRange: "readonly",
  Decimal: "readonly",
  Device: "readonly",
  DeviceType: "readonly",
  Document: "readonly",
  DocumentWindow: "readonly",
  Email: "readonly",
  FilePicker: "readonly",
  FileSaver: "readonly",
  FileType: "readonly",
  FileTypes: "readonly",
  FileWrapper: "readonly",
  Folder: "readonly",
  FolderArray: "readonly",
  ForecastDay: "readonly",
  Form: "readonly",
  Formatter: "readonly",
  Image: "readonly",
  Inbox: "readonly",
  LanguageModel: "readonly",
  Library: "readonly",
  LigatureStyle: "readonly",
  Locale: "readonly",
  MenuItem: "readonly",
  NamedStyle: "readonly",
  NamedStylePosition: "readonly",
  ObjectIdentifier: "readonly",
  Pasteboard: "readonly",
  Perspective: "readonly",
  PlugIn: "readonly",
  Preferences: "readonly",
  Project: "readonly",
  ProjectArray: "readonly",
  SectionArray: "readonly",
  Selection: "readonly",
  Settings: "readonly",
  SharePanel: "readonly",
  SidebarTree: "readonly",
  Style: "readonly",
  Tag: "readonly",
  TagArray: "readonly",
  Tags: "readonly",
  Task: "readonly",
  TaskArray: "readonly",
  Text: "readonly",
  TextAlignment: "readonly",
  TextComponent: "readonly",
  Timer: "readonly",
  TimeZone: "readonly",
  ToolbarItem: "readonly",
  Tree: "readonly",
  TreeNode: "readonly",
  TypeIdentifier: "readonly",
  UnderlineAffinity: "readonly",
  UnderlinePattern: "readonly",
  UnderlineStyle: "readonly",
  URL: "readonly",
  Version: "readonly",
  Window: "readonly",

  // === OmniFocus PlugIn API — Database globals (properties on Document/global) ===
  flattenedTasks: "readonly",
  flattenedProjects: "readonly",
  flattenedFolders: "readonly",
  flattenedTags: "readonly",
  folders: "readonly",
  projects: "readonly",
  tags: "readonly",
  inbox: "readonly",
  library: "readonly",
  moveTasks: "readonly",
  moveSections: "readonly",
  deleteObject: "readonly",
  duplicateTasks: "readonly",
  duplicateSections: "readonly",

  // === Convenience finders (top-level globals in Omni Automation; missing from omnifocus.d.ts — track in api_gaps.md) ===
  folderNamed: "readonly",
  projectNamed: "readonly",
  taskNamed: "readonly",
  tagNamed: "readonly",
  app: "readonly",
  document: "readonly",

  // === Standard ES globals legitimately used in plugin code ===
  console: "readonly",
};

const pluginRules = {
  "no-undef": "error",
  "no-unused-vars": [
    "warn",
    {
      argsIgnorePattern: "^_",
      caughtErrorsIgnorePattern: "^_",
      varsIgnorePattern: "^_",
    },
  ],
};

export default [
  // Plugin code — Resources/*.js inside built .omnifocusjs bundles
  {
    files: ["**/*.omnifocusjs/Resources/*.js", "scripts/build/intermediate/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: pluginGlobals,
    },
    rules: pluginRules,
  },
];
