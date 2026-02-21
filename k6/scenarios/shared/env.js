import exec from "k6/execution";

const DEFAULT_PROTOCOL = "http";
const DEFAULT_HOST = "localhost";
const DEFAULT_PORT = "8880";
const DEFAULT_HEADERS = ["X-Real-IP"];

const GLOBAL_SPOOF_CONFIG = buildSpoofConfig();
const STICKY_CACHE = new Map();

export function resolveBaseUrl() {
  if (__ENV.BASE) {
    return trimTrailingSlash(__ENV.BASE);
  }

  if (__ENV.TARGET_BASE_URL) {
    return trimTrailingSlash(__ENV.TARGET_BASE_URL);
  }

  const protocol = normaliseProtocol(__ENV.TARGET_PROTOCOL || DEFAULT_PROTOCOL);
  const host = __ENV.TARGET_HOST || DEFAULT_HOST;
  const port = __ENV.TARGET_PORT || DEFAULT_PORT;

  const portSegment = port ? `:${port}` : "";
  return `${protocol}://${host}${portSegment}`;
}

export function applySpoofHeaders(headers = {}) {
  if (!GLOBAL_SPOOF_CONFIG.enabled) {
    return headers;
  }

  const ip = GLOBAL_SPOOF_CONFIG.sticky ? getStickyIp() : generateIp();
  if (!ip) {
    return headers;
  }

  for (const headerName of GLOBAL_SPOOF_CONFIG.headers) {
    if (GLOBAL_SPOOF_CONFIG.overwrite || headers[headerName] === undefined) {
      headers[headerName] = ip;
    }
  }

  if (GLOBAL_SPOOF_CONFIG.setXff) {
    const existing = headers["X-Forwarded-For"];
    if (GLOBAL_SPOOF_CONFIG.overwrite || !existing) {
      headers["X-Forwarded-For"] = ip;
    } else {
      headers["X-Forwarded-For"] = `${ip}, ${existing}`;
    }
  }

  return headers;
}

function getStickyIp() {
  const vu = exec.vu;
  const key = vu ? vu.idInInstance : 0;
  if (!STICKY_CACHE.has(key)) {
    STICKY_CACHE.set(key, generateIp());
  }
  return STICKY_CACHE.get(key);
}

function generateIp() {
  if (GLOBAL_SPOOF_CONFIG.pool.length) {
    return randomChoice(GLOBAL_SPOOF_CONFIG.pool);
  }
  if (GLOBAL_SPOOF_CONFIG.ranges.length) {
    return intToIp(randomFromRanges(GLOBAL_SPOOF_CONFIG.ranges));
  }
  return GLOBAL_SPOOF_CONFIG.staticIp;
}

function buildSpoofConfig() {
  const pool = parseIpList(__ENV.SPOOF_IP_POOL);
  const staticIp = normaliseIp(__ENV.SPOOF_IP_STATIC);
  const ranges = parseRanges(__ENV.SPOOF_IP_RANGES || __ENV.SPOOF_IP_RANGE);
  const headers = parseHeaders();
  const setXff = parseBoolean(__ENV.SPOOF_IP_SET_XFF, true);
  const overwrite = parseBoolean(__ENV.SPOOF_IP_OVERWRITE, false);
  const sticky = parseBoolean(__ENV.SPOOF_IP_STICKY, true);

  const enabled = Boolean(
    (pool && pool.length) ||
      (ranges && ranges.length) ||
      staticIp
  );

  return {
    enabled,
    pool: pool || [],
    ranges: ranges || [],
    staticIp: staticIp || null,
    headers: (headers.length ? headers : DEFAULT_HEADERS).slice(),
    setXff,
    overwrite,
    sticky,
  };
}

function parseHeaders() {
  if (__ENV.SPOOF_IP_HEADERS) {
    return __ENV.SPOOF_IP_HEADERS
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
  }
  if (__ENV.SPOOF_IP_HEADER) {
    const trimmed = __ENV.SPOOF_IP_HEADER.trim();
    return trimmed ? [trimmed] : [];
  }
  return [];
}

function parseBoolean(raw, fallback) {
  if (raw === undefined) {
    return fallback;
  }
  const value = String(raw).toLowerCase();
  if (value === "true" || value === "1") return true;
  if (value === "false" || value === "0") return false;
  return fallback;
}

function parseIpList(raw) {
  if (raw === undefined) {
    return null;
  }
  if (!raw) {
    return [];
  }
  return raw
    .split(",")
    .map((value) => normaliseIp(value))
    .filter(Boolean);
}

function parseRanges(raw) {
  if (raw === undefined) {
    return null;
  }
  if (!raw) {
    return [];
  }
  const entries = raw.split(",").map((value) => value.trim()).filter(Boolean);
  const result = [];
  for (const entry of entries) {
    const parsed = parseRange(entry);
    if (parsed) {
      result.push(parsed);
    }
  }
  return result;
}

function parseRange(entry) {
  if (entry.includes("/")) {
    return parseCidr(entry);
  }
  if (entry.includes("-")) {
    const [startRaw, endRaw] = entry.split("-");
    const start = normaliseIp(startRaw);
    const end = normaliseIp(endRaw);
    if (!start || !end) return null;
    const startInt = ipToInt(start);
    const endInt = ipToInt(end);
    if (startInt === null || endInt === null || endInt < startInt) return null;
    return [startInt, endInt];
  }
  const single = normaliseIp(entry);
  if (!single) return null;
  const value = ipToInt(single);
  return value !== null ? [value, value] : null;
}

function parseCidr(entry) {
  const [base, prefixRaw] = entry.split("/");
  const baseIp = normaliseIp(base);
  const prefix = Number(prefixRaw);
  if (!baseIp || !Number.isInteger(prefix) || prefix < 0 || prefix > 32) {
    return null;
  }
  const baseInt = ipToInt(baseIp);
  if (baseInt === null) {
    return null;
  }
  const mask = prefix === 0 ? 0 : (~0 << (32 - prefix)) >>> 0;
  const start = baseInt & mask;
  const span = prefix === 32 ? 1 : 1 << (32 - prefix);
  const end = (start + span - 1) >>> 0;
  return [start >>> 0, end];
}

function randomChoice(values) {
  const index = Math.floor(Math.random() * values.length);
  return values[index];
}

function randomFromRanges(ranges) {
  if (ranges.length === 1) {
    return randomIntBetween(ranges[0][0], ranges[0][1]);
  }
  const total = ranges.reduce((sum, [start, end]) => sum + (end - start + 1), 0);
  let roll = Math.floor(Math.random() * total);
  for (const [start, end] of ranges) {
    const span = end - start + 1;
    if (roll < span) {
      return start + roll;
    }
    roll -= span;
  }
  const [start, end] = ranges[ranges.length - 1];
  return randomIntBetween(start, end);
}

function randomIntBetween(min, max) {
  const floorMin = Math.ceil(min);
  const floorMax = Math.floor(max);
  return Math.floor(Math.random() * (floorMax - floorMin + 1)) + floorMin;
}

function normaliseIp(value) {
  if (!value) return null;
  const parts = value.trim().split(".");
  if (parts.length !== 4) return null;
  const normalised = [];
  for (const part of parts) {
    const num = Number(part);
    if (!Number.isInteger(num) || num < 0 || num > 255) {
      return null;
    }
    normalised.push(String(num));
  }
  return normalised.join(".");
}

function ipToInt(ip) {
  const parts = ip.split(".").map(Number);
  if (parts.length !== 4) return null;
  return ((parts[0] << 24) >>> 0) + (parts[1] << 16) + (parts[2] << 8) + parts[3];
}

function intToIp(value) {
  return [
    (value >>> 24) & 0xff,
    (value >>> 16) & 0xff,
    (value >>> 8) & 0xff,
    value & 0xff,
  ].join(".");
}

function normaliseProtocol(value) {
  const trimmed = value.trim();
  return trimmed.endsWith(":") ? trimmed.slice(0, -1) : trimmed;
}

function trimTrailingSlash(value) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}
