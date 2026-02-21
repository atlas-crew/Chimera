#!/usr/bin/env node

import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const USAGE = `Usage: node scripts/run-compose.mjs <up|down> <api-demo|apparatus>\n`;

const SERVICE_MAP = {
  'api-demo': ['chimera-waf', 'demo-site'],
  apparatus: ['chimera-waf', 'apparatus'],
};

function fail(message) {
  console.error(`\n[compose-runner] ${message}`);
  process.exit(1);
}

function detectRuntime() {
  const candidates = [
    {
      check: ['podman', '--version'],
      command: ['podman', 'compose'],
      name: 'podman',
    },
    {
      check: ['docker', '--version'],
      command: ['docker', 'compose'],
      name: 'docker',
    },
  ];

  for (const candidate of candidates) {
    const result = spawnSync(candidate.check[0], candidate.check.slice(1), {
      stdio: 'ignore',
    });
    if (result.status === 0) {
      return candidate;
    }
  }

  return null;
}

const [, , action, target] = process.argv;

if (!action || !target) {
  fail(USAGE.trim());
}

if (!['up', 'down'].includes(action)) {
  fail(`Unknown action "${action}". Supported: up, down.`);
}

if (!Object.hasOwn(SERVICE_MAP, target)) {
  fail(`Unknown target "${target}". Supported: ${Object.keys(SERVICE_MAP).join(', ')}.`);
}

const runtime = detectRuntime();
if (!runtime) {
  fail('Neither podman nor docker was found on PATH. Please install one of them.');
}

const composeFile = resolve(process.cwd(), 'compose.yml');
if (!existsSync(composeFile)) {
  fail(`compose.yml not found at ${composeFile}`);
}

const services = SERVICE_MAP[target];
const baseArgs = ['-f', composeFile];

let args;
if (action === 'up') {
  args = baseArgs.concat(['up', '--build', '-d', ...services]);
} else {
  args = baseArgs.concat(['rm', '-s', '-f', ...services]);
}

console.log(`[compose-runner] Using ${runtime.name} compose to ${action} ${services.join(', ')}`);

const result = spawnSync(runtime.command[0], runtime.command.slice(1).concat(args), {
  stdio: 'inherit',
});

if (result.status !== 0) {
  fail(`${runtime.name} compose ${action} exited with code ${result.status}`);
}
