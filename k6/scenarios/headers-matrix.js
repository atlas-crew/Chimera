import http from "k6/http";
import { check } from "k6";

import { resolveBaseUrl, applySpoofHeaders } from "./shared/env.js";

export const options = {
  vus: Number(__ENV.VUS || 20),
  duration: __ENV.DURATION || "1m"
};

function headers(n) {
  const h = {};
  for (let i = 0; i < n; i++) h[`X-Custom-${i}`] = `v-${i}`;
  return h;
}

export default function () {
  const base = resolveBaseUrl();
  const count = Number(__ENV.HCOUNT || 100);
  const res = http.get(`${base}/api/gateway/routes`, {
    headers: applySpoofHeaders(headers(count))
  });
  check(res, { "ok": (r) => r.status === 200 });
}
