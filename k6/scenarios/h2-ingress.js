import http from "k6/http";
import { check } from "k6";

import { resolveBaseUrl, applySpoofHeaders } from "./shared/env.js";

export const options = {
  vus: Number(__ENV.VUS || 20),
  duration: __ENV.DURATION || "2m",
  insecureSkipTLSVerify: true
};

export default function () {
  const base = normaliseBase(__ENV.BASE_HTTPS || resolveBaseUrl());
  const res = http.get(`${base}/api/system/version`, {
    headers: applySpoofHeaders(),
    tags: { proto: "h2" }
  });
  check(res, { "200": (r) => r.status === 200 });
}

function normaliseBase(value) {
  if (!value) {
    return "https://echo.localtest.me";
  }
  return value.endsWith("/") ? value.slice(0, -1) : value;
}
