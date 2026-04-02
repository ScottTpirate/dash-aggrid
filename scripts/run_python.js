#!/usr/bin/env node

const { spawnSync } = require('child_process');

const args = process.argv.slice(2);
const candidates = [];

if (process.env.PYTHON_BIN) {
  candidates.push([process.env.PYTHON_BIN, ...args]);
}

candidates.push(['python3', ...args]);
candidates.push(['python', ...args]);
candidates.push(['py', '-3', ...args]);

for (const [command, ...commandArgs] of candidates) {
  const result = spawnSync(command, commandArgs, { stdio: 'inherit' });
  if (!result.error) {
    process.exit(result.status ?? 0);
  }
}

console.error(
  'Unable to locate a Python interpreter. Set PYTHON_BIN, or ensure python3/python is on PATH.'
);
process.exit(1);
