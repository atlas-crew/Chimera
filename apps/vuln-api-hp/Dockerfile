# Development Dockerfile for chimera-api-hp
FROM rust:1.85-slim AS builder

WORKDIR /app

# Cache dependency build
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo 'fn main() {}' > src/main.rs && cargo build --release && rm -rf src

# Build real binary
COPY src/ src/
RUN touch src/main.rs && cargo build --release

# Runtime — minimal image
FROM debian:bookworm-slim

RUN groupadd -r -g 1000 chimera && \
    useradd -r -u 1000 -g chimera -m -s /sbin/nologin chimera

COPY --from=builder /app/target/release/chimera-api-hp /usr/local/bin/chimera-api-hp

ENV PORT=8890

USER chimera
EXPOSE 8890

HEALTHCHECK --interval=10s --timeout=2s --start-period=3s --retries=3 \
    CMD curl -sf http://localhost:8890/healthz || exit 1

CMD ["chimera-api-hp"]
