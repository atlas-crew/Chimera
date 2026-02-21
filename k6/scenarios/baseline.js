import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

import { resolveBaseUrl, applySpoofHeaders } from "./shared/env.js";

export const options = {
  vus: __ENV.VUS ? Number(__ENV.VUS) : 10,
  duration: __ENV.DURATION || "1m"
};

const t = new Trend("latency_ms");

export default function () {
  const base = resolveBaseUrl();
  const res = http.get(`${base}/healthz`, { headers: applySpoofHeaders() });
  t.add(res.timings.duration);
  check(res, { "200": (r) => r.status === 200 });
  sleep(0.2);
}
