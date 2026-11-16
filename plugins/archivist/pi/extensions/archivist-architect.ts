// Pi entry for the archivist-architect role. Tools it adds: bash
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { archivistGuard } from "./guard.ts";

export default (pi: ExtensionAPI) => archivistGuard(pi, "archivist:archivist-architect");
