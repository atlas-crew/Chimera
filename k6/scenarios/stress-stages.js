import http from "k6/http";
import { check } from "k6";

import { resolveBaseUrl, applySpoofHeaders } from "./shared/env.js";

export const options = {
  stages: [
    { duration: "1m", target: 25 },
    { duration: "2m", target: 150 },
    { duration: "2m", target: 300 },
    { duration: "1m", target: 0 }
  ],
  thresholds: {
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<750"]
  }
};

export default function () {
  const base = resolveBaseUrl();
  const res = http.get(`${base}/api/products/search?q=security`, {
    headers: applySpoofHeaders()
  });
  check(res, { "200": (r) => r.status === 200 });
}
