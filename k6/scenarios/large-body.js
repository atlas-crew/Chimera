import http from "k6/http";
import { check } from "k6";

import { resolveBaseUrl, applySpoofHeaders } from "./shared/env.js";

export const options = {
  vus: Number(__ENV.VUS || 10),
  iterations: Number(__ENV.ITERS || 200)
};

function payloadKB(kb) {
  const s = "A".repeat(1024);
  const a = [];
  for (let i = 0; i < kb; i++) a.push(s);
  return a.join("");
}

export default function () {
  const base = resolveBaseUrl();
  const kb = Number(__ENV.KB || 1024); // 1 MB
  const body = payloadKB(kb);
  const res = http.post(`${base}/api/payments/process`, body, {
    headers: applySpoofHeaders({ "Content-Type": "text/plain" })
  });
  check(res, { "recv": (r) => r.status > 0 });
}
