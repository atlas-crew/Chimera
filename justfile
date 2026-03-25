set dotenv-load := false

# List available recipes
default:
    @just --list

# ── Setup ──────────────────────────────────────────────

# Install all workspace dependencies
install:
    pnpm install

# ── Workspace (all projects) ──────────────────────────

# Build all projects
build:
    pnpm nx run-many -t build

# Test all projects
test:
    pnpm nx run-many -t test

# Lint all projects
lint:
    pnpm nx run-many -t lint

# Run affected targets (build, test, lint) against base branch
affected target="test" base="main":
    pnpm nx affected -t {{ target }} --base={{ base }}

# Show the Nx project graph
graph:
    pnpm nx graph

# List all projects
projects:
    pnpm nx show projects

# Reset Nx cache
reset:
    pnpm nx reset

# ── chimera-api ───────────────────────────────────────

# Start the API (vulnerable mode)
api-start:
    pnpm nx run chimera-api:start

# Show how to stop the API process
api-stop:
    pnpm nx run chimera-api:stop

# Run API tests
api-test:
    pnpm nx run chimera-api:test

# Start the API demo via docker-compose
api-demo-up:
    pnpm nx run chimera-api:serve-api-demo

# Stop the API demo
api-demo-down:
    pnpm nx run chimera-api:stop-api-demo

# Run API unit tests directly (bypasses Nx)
api-test-unit:
    make -C apps/vuln-api test-unit

# ── vuln-web ──────────────────────────────────────────

# Start the web dev server
web-dev:
    pnpm nx run vuln-web:start

# Build the web app
web-build:
    pnpm nx run vuln-web:build

# Lint the web app
web-lint:
    pnpm nx run vuln-web:lint

# Preview the production build
web-preview:
    pnpm nx run vuln-web:preview

# Run web tests
web-test:
    pnpm nx run vuln-web:test

# ── Bundle / Packaging ─────────────────────────────────

# Build the web frontend into the Flask package (app/web_dist/)
bundle-web:
    pnpm nx run vuln-web:build:bundle

# Build the Python wheel (bundles web first via Nx dependsOn)
build-api:
    pnpm nx run chimera-api:build

# Publish the chimera-api package to PyPI
publish-api:
    pnpm nx run chimera-api:publish

# Alias: full bundle + wheel build
bundle: build-api

# ── Dev ───────────────────────────────────────────────

# Start both API and web dev server
dev:
    pnpm nx run-many -t start --parallel=2

# Run a specific Nx target for a project (e.g. just run chimera-api test)
run project target:
    pnpm nx run {{ project }}:{{ target }}

# ── Docs ───────────────────────────────────────

# Ruby path (Homebrew); override with RUBY_DIR= if needed
ruby_bin := env("RUBY_DIR", "/opt/homebrew/opt/ruby/bin")

# Serve the documentation site locally (Jekyll, default port 4000)
docs-serve port="4000":
    cd docs && PATH="{{ruby_bin}}:$PATH" bundle install --quiet && PATH="{{ruby_bin}}:$PATH" bundle exec jekyll serve --port {{port}} --livereload --livereload-port 35731

# Build the documentation site without serving
docs-build:
    cd docs && PATH="{{ruby_bin}}:$PATH" bundle install --quiet && PATH="{{ruby_bin}}:$PATH" bundle exec jekyll build
