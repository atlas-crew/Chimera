import http from "k6/http";
import { check } from "k6";

import { resolveBaseUrl, applySpoofHeaders } from "./shared/env.js";

export const options = {
  vus: Number(__ENV.VUS || 40),
  duration: __ENV.DURATION || "3m"
};

const paths = [
  "/api/products/search?q=%27%20OR%20%271%27=%271",
  "/api/medical/phi/endpoints",
  "/api/payments/bin-ranges?bin=../../../etc/passwd",
  "/api/oauth/token",
  "/api/webhooks/callback",
  "/api/vendors/documents/upload",
  "/api/loyalty/customers/export?include_pii=true",
  "/api/integrations/discovery",
  "/api/transactions/export?format=json"
];

export default function () {
  const base = resolveBaseUrl();
  const i = Math.floor(Math.random() * paths.length);
  const headers = applySpoofHeaders({
    "X-Long-Header": "x".repeat(4096),
    "X-Proto": "test"
  });
  const res = http.get(`${base}${paths[i]}`, { headers });
  check(res, { "recv": (r) => r.status > 0 });
}
