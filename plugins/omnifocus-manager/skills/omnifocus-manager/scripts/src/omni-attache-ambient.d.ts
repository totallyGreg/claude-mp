/**
 * omni-attache-ambient.d.ts — Attache @ts-check ambient patches.
 *
 * The official omnifocus.d.ts was generated from an older API snapshot and
 * has several parameter signatures that don't match OmniFocus 4 runtime
 * behaviour.  These interface augmentations fix them without modifying the
 * upstream declaration file.
 *
 * Consumed only by tsconfig.attache.json.
 */

// ─── Console ────────────────────────────────────────────────────────────────
// Runtime: console.log("msg") is valid; the type requires two args.
interface Console {
  log(message: Object, additional?: Array<Object | null>): void;
  error(message: Object, additional?: Array<Object | null>): void;
  info(message: Object, additional?: Array<Object | null>): void;
  warn(message: Object, additional?: Array<Object | null>): void;
}

// ─── Alert ───────────────────────────────────────────────────────────────────
// Runtime: alert.show() and alert.show(null) both work with 0 args.
interface Alert {
  show(callback?: Function | null): Promise<number>;
}

// ─── Form ────────────────────────────────────────────────────────────────────
// Runtime: form.addField(field) — index is optional (appends to end).
// Runtime: await form.show() — both title/confirm args are optional.
interface Form {
  addField(field: Form.Field, index?: number | null): void;
  show(title?: string, confirmTitle?: string): Promise<Form>;
}

// ─── PlugIn.Library ──────────────────────────────────────────────────────────
// Attache loads library plugins dynamically via plugIn.library("name") and
// then calls methods on the returned Library object.  The static Library type
// has no knowledge of those methods.  An index signature lets tsc accept
// any property access without a per-method declaration.
declare namespace PlugIn {
  interface Library {
    [key: string]: any;
  }
}

// ─── Status objects ───────────────────────────────────────────────────────────
// OmniFocus Status values expose a .name string at runtime (e.g. "active").
// The generated type stubs are empty classes without this property.
declare namespace Project {
  interface Status {
    readonly name: string;
  }
}

declare namespace Folder {
  interface Status {
    readonly name: string;
  }
}

declare namespace Task {
  interface Status {
    readonly name: string;
  }
}

// ─── Task extras ─────────────────────────────────────────────────────────────
// Task.dropped is used in Attache JS but missing from the generated types.
interface Task {
  readonly dropped: boolean;
}

// ─── Project extras ───────────────────────────────────────────────────────────
// Project extends DatabaseObject in the type stubs, skipping DatedObject, so
// 'added' (creation date) is missing.  lastReviewedDate is an Attache code typo
// for the canonical lastReviewDate — declare both so tsc accepts both spellings.
interface Project {
  readonly added: Date | null;
  readonly lastReviewedDate: Date | null;
}

// ─── Folder extras ────────────────────────────────────────────────────────────
// Folder.flattenedTasks is used in Attache but absent from the 2021 stubs.
interface Folder {
  readonly flattenedTasks: TaskArray;
}

// ─── Device extras ────────────────────────────────────────────────────────────
// Device.name used in preferencesManager.js for device identification.
// Device.current.name → Device has no 'name' in the 2021 stubs.
interface Device {
  readonly name: string;
}

// ─── FileSaver overload ───────────────────────────────────────────────────────
// Attache calls fileSaver.show() with no args (shows dialog, user picks path).
interface FileSaver {
  show(): Promise<URL>;
}

// ─── FileWrapper extras ───────────────────────────────────────────────────────
// FileWrapper.fromString(name, content) and .write(url) used in exportUtils.js.
declare namespace FileWrapper {
  function fromString(name: string, content: string): FileWrapper;
}
interface FileWrapper {
  write(url: URL): void;
}

// ─── FileType ────────────────────────────────────────────────────────────────
// FileType.fromExtension() used in exportUtils.js.  Maps to TypeIdentifier
// at runtime (OmniFocus's actual file type system).
declare class FileType {
  static fromExtension(ext: string): TypeIdentifier;
}

// ─── Global folderNamed ──────────────────────────────────────────────────────
// OmniFocus exposes folderNamed() as a global shorthand for searching root
// folders by name.
declare function folderNamed(name: string): Folder | null;
