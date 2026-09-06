const fs = require('node:fs');

const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  throw new Error('Usage: node compact-captions.cjs INPUT.srt OUTPUT.srt');
}

const parseTime = (value) => {
  const [hours, minutes, rest] = value.split(':');
  const [seconds, millis] = rest.split(',');
  return ((Number(hours) * 60 + Number(minutes)) * 60 + Number(seconds)) * 1000 + Number(millis);
};

const formatTime = (millis) => {
  const safe = Math.max(0, Math.round(millis));
  const hours = Math.floor(safe / 3600000);
  const minutes = Math.floor((safe % 3600000) / 60000);
  const seconds = Math.floor((safe % 60000) / 1000);
  const ms = safe % 1000;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
};

const splitWords = (text, maximum = 7) => {
  const words = text.replace(/\s+/g, ' ').trim().split(' ');
  const parts = [];
  for (let index = 0; index < words.length; index += maximum) {
    parts.push(words.slice(index, index + maximum).join(' '));
  }
  return parts;
};

const blocks = fs.readFileSync(inputPath, 'utf8').trim().split(/\r?\n\r?\n/);
const output = [];
for (const block of blocks) {
  const lines = block.split(/\r?\n/);
  const match = lines[1]?.match(/^(.*?) --> (.*?)$/);
  if (!match) continue;
  const start = parseTime(match[1]);
  const end = parseTime(match[2]);
  // Keep the final brand card visually clean; platforms can still use the full SRT as soft CC.
  if (start >= 251000) continue;
  const text = lines.slice(2).join(' ');
  const parts = splitWords(text);
  const weights = parts.map((part) => part.split(' ').length);
  const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
  let cursor = start;
  parts.forEach((part, index) => {
    const next = index === parts.length - 1
      ? end
      : cursor + ((end - start) * weights[index]) / totalWeight;
    output.push({ start: cursor, end: next, text: part });
    cursor = next;
  });
}

fs.writeFileSync(outputPath, output.map((caption, index) => [
  index + 1,
  `${formatTime(caption.start)} --> ${formatTime(caption.end)}`,
  caption.text,
  '',
].join('\n')).join('\n'));
