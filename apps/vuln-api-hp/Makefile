# Makefile for chimera-api-hp — high-performance echo server

.PHONY: help build build-release run test clean docker docker-prod

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

PORT ?= 8890

help:
	@echo "$(BLUE)Chimera API HP — High-Performance Echo Server$(NC)"
	@echo ""
	@echo "Available targets:"
	@echo "  $(GREEN)build$(NC)          - Build debug binary"
	@echo "  $(GREEN)build-release$(NC)  - Build optimized release binary"
	@echo "  $(GREEN)run$(NC)            - Build and run (debug)"
	@echo "  $(GREEN)run-release$(NC)    - Build and run (release)"
	@echo "  $(GREEN)test$(NC)           - Run tests"
	@echo "  $(GREEN)bench$(NC)          - Quick throughput benchmark with wrk"
	@echo "  $(GREEN)clean$(NC)          - Remove build artifacts"
	@echo "  $(GREEN)docker$(NC)         - Build dev Docker image"
	@echo "  $(GREEN)docker-prod$(NC)    - Build production Docker image"

build:
	@echo "$(BLUE)Building debug binary...$(NC)"
	cargo build
	@echo "$(GREEN)✓ Build complete$(NC)"

build-release:
	@echo "$(BLUE)Building release binary...$(NC)"
	cargo build --release
	@echo "$(GREEN)✓ Release build complete$(NC)"
	@ls -lh target/release/chimera-api-hp | awk '{print "  Binary size: " $$5}'

run:
	@echo "$(BLUE)Starting chimera-api-hp on port $(PORT)...$(NC)"
	PORT=$(PORT) cargo run

run-release:
	@echo "$(BLUE)Starting chimera-api-hp (release) on port $(PORT)...$(NC)"
	PORT=$(PORT) cargo run --release

test:
	@echo "$(BLUE)Running tests...$(NC)"
	cargo test
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-ci:
	@echo "$(BLUE)Running CI tests...$(NC)"
	cargo test -- --nocapture
	@echo "$(GREEN)✓ CI tests passed$(NC)"

bench:
	@echo "$(BLUE)Benchmarking /echo (10s, 8 threads, 256 connections)...$(NC)"
	@echo "$(YELLOW)Make sure the server is running: make run-release$(NC)"
	@wrk -t8 -c256 -d10s http://localhost:$(PORT)/echo || echo "$(RED)Install wrk: brew install wrk$(NC)"

clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	cargo clean
	@echo "$(GREEN)✓ Clean complete$(NC)"

docker:
	@echo "$(BLUE)Building dev Docker image...$(NC)"
	docker build -t chimera-api-hp:dev .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-prod:
	@echo "$(BLUE)Building production Docker image...$(NC)"
	docker build -f Dockerfile.prod -t chimera-api-hp:latest .
	@docker images chimera-api-hp:latest --format "  Image size: {{.Size}}"
	@echo "$(GREEN)✓ Production image built$(NC)"
