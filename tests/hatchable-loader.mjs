// Test-only module resolution; Hatchable provides these imports in production.
import { registerHooks } from "node:module";

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === "hatchable") {
      return { url: new URL("./helpers/hatchable-sdk.mjs", import.meta.url).href, shortCircuit: true };
    }
    if (specifier.startsWith("lib/")) {
      return { url: new URL(`../${specifier}`, import.meta.url).href, shortCircuit: true };
    }
    return nextResolve(specifier, context);
  },
});
