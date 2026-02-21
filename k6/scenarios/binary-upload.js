import http from "k6/http";
import { check } from "k6";

import { resolveBaseUrl, applySpoofHeaders } from "./shared/env.js";

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || "1m"
};

function randomBytes(n) {
  const arr = new Uint8Array(n);
  for (let i = 0; i < n; i++) arr[i] = Math.floor(Math.random() * 256);
  return arr.buffer;
}

export default function () {
  const base = resolveBaseUrl();
  const bytes = Number(__ENV.BYTES || 256 * 1024);
  const buf = randomBytes(bytes);
  const res = http.post(`${base}/api/vendors/documents/upload`, buf, {
    headers: applySpoofHeaders({ "Content-Type": "application/octet-stream" })
  });
  check(res, { "recv": (r) => r.status > 0 });
}
