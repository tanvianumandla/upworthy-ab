// app.js
// Wires the page together: loads the effects, listens for typing, and shows results.
import { detectFeatures } from "./features.js";

const input = document.getElementById("headline");
const results = document.getElementById("results");

const data = await (await fetch("effects.json")).json();
document.getElementById("n-comparisons").textContent = data.comparisons.toLocaleString();

input.addEventListener("input", () => {
  const found = detectFeatures(input.value);
  results.innerHTML = renderResults(found, data.features);
});

// The range bar covers -15% to +15%. Convert a change (like -0.088) to a
// position from 0 to 100 (percent of the bar's width).
const BAR_LIMIT = 0.15;
function toBarPosition(change) {
  const clamped = Math.max(-BAR_LIMIT, Math.min(BAR_LIMIT, change));
  return ((clamped + BAR_LIMIT) / (2 * BAR_LIMIT)) * 100;
}

function formatPercent(change) {
  const sign = change > 0 ? "+" : "";
  return `${sign}${(change * 100).toFixed(1)}%`;
}

// Builds one row: label, effect, and range bar.
function renderRow(effect, isOn, label, suffix) {
  let valueText = "no clear effect";
  let direction = "none";
  if (effect.significant) {
    valueText = formatPercent(effect.change) + suffix;
    direction = effect.change > 0 ? "up" : "down";
  }

  const left = toBarPosition(effect.low);
  const width = toBarPosition(effect.high) - left;
  const color = { up: "var(--up)", down: "var(--down)", none: "var(--neutral)" }[direction];

  return `
    <div class="row ${isOn ? "" : "off"}">
      <span class="label">${isOn ? "✓ " : ""}${label}</span>
      <span class="value ${direction}">${valueText}</span>
      <div class="range" title="95% range: ${formatPercent(effect.low)} to ${formatPercent(effect.high)}">
        <div class="zero"></div>
        <div class="ci" style="left:${left}%; width:${width}%; background:${color}"></div>
      </div>
    </div>`;
}

function renderResults(found, effects) {
  if (found.word_count === 0) return "";

  const rows = effects.map((effect) => {
    // Length is always "on": every headline has some length.
    if (effect.id === "words_per_5") {
      const label = `Length: ${found.word_count} word${found.word_count === 1 ? "" : "s"}`;
      return { isOn: true, html: renderRow(effect, true, label, " per 5 words") };
    }
    const isOn = found[effect.id];
    return { isOn, html: renderRow(effect, isOn, effect.label, "") };
  });

  // Features in this headline first, then the rest (dimmed).
  rows.sort((a, b) => Number(b.isOn) - Number(a.isOn));
  const count = rows.filter((r) => r.isOn).length - 1; // not counting length

  return `
    <p class="summary">
      ${count === 0 ? "None of the tested features found." : `${count} feature${count === 1 ? "" : "s"} found.`}
      Change in clicks vs. other headlines for the same story:
    </p>
    ${rows.map((r) => r.html).join("")}`;
}