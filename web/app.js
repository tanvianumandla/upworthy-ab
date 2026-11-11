// app.js
// Compares two headlines using the effects measured in the Upworthy A/B tests.
import { detectFeatures } from "./features.js";

const inputA = document.getElementById("headline-a");
const inputB = document.getElementById("headline-b");
const results = document.getElementById("results");

const data = await (await fetch("effects.json")).json();
document.getElementById("n-comparisons").textContent = data.comparisons.toLocaleString();

function update() {
  const a = detectFeatures(inputA.value);
  const b = detectFeatures(inputB.value);
  results.innerHTML = renderResults(a, b, data);
}
inputA.addEventListener("input", update);
inputB.addEventListener("input", update);

// ---------- helpers ----------

const BAR_LIMIT = 0.15;        // the range bar covers -15% to +15%
const SMALL_DIFFERENCE = 0.03; // under 3% is called "small" even if it's real

function toBarPosition(change) {
  const clamped = Math.max(-BAR_LIMIT, Math.min(BAR_LIMIT, change));
  return ((clamped + BAR_LIMIT) / (2 * BAR_LIMIT)) * 100;
}

function formatPercent(change) {
  const sign = change > 0 ? "+" : "";
  return `${sign}${(change * 100).toFixed(1)}%`;
}

// The model's value for one feature: 1/0 for yes/no features,
// and word count / 5 for length (the effect is "per 5 words").
function featureValue(found, id) {
  if (id === "words_per_5") return found.word_count / 5;
  return found[id] ? 1 : 0;
}

// ---------- the verdict: B compared with A ----------
// The model works on a log scale, so effects add up there:
//   estimate = sum over features of (B's value - A's value) * coef
// Its uncertainty uses the model's covariance matrix (cov), which accounts
// for features being correlated with each other.
function compare(a, b, data) {
  const ids = data.features.map((f) => f.id);
  const diff = ids.map((id) => featureValue(b, id) - featureValue(a, id));
  if (diff.every((d) => Math.abs(d) < 1e-9)) return null; // same features

  let estimate = 0;
  data.features.forEach((f, i) => { estimate += diff[i] * f.coef; });

  let variance = 0;
  for (let i = 0; i < diff.length; i++) {
    for (let j = 0; j < diff.length; j++) {
      variance += diff[i] * data.cov[i][j] * diff[j];
    }
  }
  const se = Math.sqrt(variance);
  return {
    change: Math.exp(estimate) - 1,
    low: Math.exp(estimate - 1.96 * se) - 1,
    high: Math.exp(estimate + 1.96 * se) - 1,
  };
}

function renderVerdict(a, b, data) {
  const result = compare(a, b, data);
  if (!result) {
    return `<div class="verdict none">These two headlines have the same features, so the
      data can't tell them apart.</div>`;
  }

  // Always describe the one with the better pattern, so numbers read as "more clicks".
  let winner = "B", loser = "A", r = result;
  if (result.change < 0) {
    winner = "A"; loser = "B";
    r = { change: 1 / (1 + result.change) - 1,
          low: 1 / (1 + result.high) - 1,
          high: 1 / (1 + result.low) - 1 };
  }
  const range = `likely range ${formatPercent(r.low)} to ${formatPercent(r.high)}`;

  const amount = `${(r.change * 100).toFixed(1)}%`;

  if (r.low <= 0) {
    return `<div class="verdict none"><strong>No clear difference.</strong>
      Headline ${winner} leans ${formatPercent(r.change)}, but the ${range} includes 0.</div>`;
  }
  if (r.change < SMALL_DIFFERENCE) {
    return `<div class="verdict none"><strong>Only a small difference.</strong>
      Headline ${winner} has a slight edge: about ${amount} more clicks (${range}).</div>`;
  }
  return `<div class="verdict win-${winner.toLowerCase()}">
      <strong>Headline ${winner} fits the patterns better.</strong>
      Headlines with its features got about ${amount} more clicks
      than headlines like ${loser} (${range}).</div>`;
}

// ---------- the feature table ----------

function renderRow(effect, a, b, hasA, hasB) {
  const isLength = effect.id === "words_per_5";
  const mark = (found, has) => {
    if (!has) return "";
    if (isLength) return String(found.word_count);
    return found[effect.id] ? "✓" : "";
  };
  const differs = isLength
    ? hasA && hasB && a.word_count !== b.word_count
    : (hasA && a[effect.id]) !== (hasB && b[effect.id]);
  const label = isLength ? "Length (words)" : effect.label;

  let valueText = "no clear effect";
  let direction = "none";
  if (effect.significant) {
    valueText = formatPercent(effect.change) + (isLength ? " per 5" : "");
    direction = effect.change > 0 ? "up" : "down";
  }
  const left = toBarPosition(effect.low);
  const width = toBarPosition(effect.high) - left;
  const color = { up: "var(--up)", down: "var(--down)", none: "var(--neutral)" }[direction];

  return `
    <div class="row ${differs ? "differs" : "same"}">
      <span class="label">${label}</span>
      <span class="mark">${mark(a, hasA)}</span>
      <span class="mark">${mark(b, hasB)}</span>
      <span class="value ${direction}">${valueText}</span>
      <div class="range" title="95% range: ${formatPercent(effect.low)} to ${formatPercent(effect.high)}">
        <div class="zero"></div>
        <div class="ci" style="left:${left}%; width:${width}%; background:${color}"></div>
      </div>
    </div>`;
}

function renderResults(a, b, data) {
  const hasA = a.word_count > 0;
  const hasB = b.word_count > 0;
  if (!hasA && !hasB) return "";

  const verdict = hasA && hasB
    ? renderVerdict(a, b, data)
    : `<div class="verdict none">Add a second headline to compare.</div>`;

  const header = `
    <div class="row header">
      <span>Feature</span><span class="mark">A</span><span class="mark">B</span>
      <span class="value">Effect on clicks</span><span>95% range</span>
    </div>`;

  return verdict + header +
    data.features.map((f) => renderRow(f, a, b, hasA, hasB)).join("") +
    `<p class="legend">Bold rows are where the two headlines differ. Each effect compares
      headlines for the same story. The bar's center line is 0 (no effect).</p>`;
}