// Checks detectFeatures() against the Python feature values on 239 real headlines.
// Run from the web/ folder:  node test_features.mjs
import { readFileSync } from "node:fs";
import { detectFeatures } from "./features.js";

const cases = JSON.parse(readFileSync(new URL("./test_headlines.json", import.meta.url)));
let failures = 0;

for (const { headline, expected } of cases) {
  const got = detectFeatures(headline);
  for (const [key, want] of Object.entries(expected)) {
    if (got[key] !== want) {
      failures++;
      if (failures <= 10) {
        console.log(`FAIL ${key}: expected ${want}, got ${got[key]}\n     "${headline}"`);
      }
    }
  }
}

const total = cases.length * Object.keys(cases[0].expected).length;
console.log(`\n${total - failures}/${total} checks passed`);
process.exit(failures ? 1 : 0);
