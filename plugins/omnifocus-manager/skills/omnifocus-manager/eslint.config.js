export default [
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: {
        // OmniFocus Omni Automation globals - Classes
        Document: "readonly",
        PlugIn: "readonly",
        Version: "readonly",
        Alert: "readonly",
        Form: "readonly",
        FileSaver: "readonly",
        FileWrapper: "readonly",
        FileType: "readonly",
        FileTypes: "readonly",
        Data: "readonly",
        Pasteboard: "readonly",
        Task: "readonly",
        Project: "readonly",
        Folder: "readonly",
        Tag: "readonly",
        LanguageModel: "readonly",
        Calendar: "readonly",
        Formatter: "readonly",
        DateComponents: "readonly",
        console: "readonly",

        // OmniFocus Database globals - Properties
        flattenedTasks: "readonly",
        flattenedProjects: "readonly",
        flattenedFolders: "readonly",
        flattenedTags: "readonly",
        folders: "readonly",
        projects: "readonly",
        tags: "readonly",
        inbox: "readonly",
        library: "readonly"
      }
    },
    rules: {
      "no-undef": "off",
      "no-unused-vars": "off"
    }
  }
];
