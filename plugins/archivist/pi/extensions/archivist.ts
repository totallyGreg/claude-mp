// Pi entry for the archivist (curator) role. Tools it adds: vault_stat, vault_write
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { archivistGuard } from "./guard.ts";

export default (pi: ExtensionAPI) => archivistGuard(pi, "archivist:archivist");
