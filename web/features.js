// features.js
// Detects headline features. Must match src/features.py exactly.
// Run `node test_features.mjs` to check your version against the Python results.

export function detectFeatures(headline) {
  const trimmed = headline.trim();
  return {
    question: headline.includes("?"),
    number: /\d/.test(headline),
    you: /\byou(r|'re|rself|'ll)?\b/i.test(headline),
    this_these: /\b(this|these)\b/i.test(headline),
    exclamation: headline.includes("!"),
    quote: /["\u201c\u201d]/.test(headline),
    word_count: trimmed ? trimmed.split(/\s+/).length : 0,
  };
}
