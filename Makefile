.PHONY: help build build-js build-bundle build-shiny clean test lint format install docs docs-python docs-typescript docs-preview

# Default target
help:
	@echo "Shinymap Build Commands"
	@echo ""
	@echo "  make build        - Full build (TypeScript + bundles for Python)"
	@echo "  make build-js     - Build TypeScript only"
	@echo "  make build-bundle - Bundle React components for Python package"
	@echo "  make build-shiny  - Build Shiny bridge for Python package"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make install      - Install dependencies"
	@echo ""
	@echo "Documentation Commands"
	@echo ""
	@echo "  make docs         - Build full documentation site"
	@echo "  make docs-python  - Generate Python API docs (quartodoc)"
	@echo "  make docs-typescript - Generate TypeScript API docs (typedoc)"
	@echo "  make docs-preview - Preview documentation site locally"

# Full build: TypeScript compilation + bundling for Python
build: build-js build-bundle build-shiny
	@echo "✓ Full build complete"

# Build TypeScript
build-js:
	@echo "Building TypeScript..."
	cd packages/shinymap/js && npm run build
	@echo "✓ TypeScript compilation complete"

# Bundle React components for Python package
build-bundle:
	@echo "Bundling React components for Python package..."
	cd packages/shinymap/js && node build-global.js
	@echo "✓ Bundle created at packages/shinymap/python/src/shinymap/www/shinymap.global.js"

# Build and copy Shiny bridge for Python package
build-shiny:
	@echo "Building Shiny bridge..."
	cd packages/shinymap/js && npm run build:shiny
	cp packages/shinymap/js/dist/shinymap-shiny.js packages/shinymap/python/src/shinymap/www/shinymap-shiny.js
	@echo "✓ Shiny bridge copied to packages/shinymap/python/src/shinymap/www/shinymap-shiny.js"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf packages/shinymap/js/dist
	rm -f packages/shinymap/python/src/shinymap/www/shinymap.global.js
	rm -f packages/shinymap/python/src/shinymap/www/shinymap-shiny.js
	@echo "✓ Clean complete"

# Run tests
test:
	@echo "Running Python tests..."
	uv run pytest packages/shinymap/python/tests/ -v
	@echo "✓ Tests complete"

# Lint
lint:
	@echo "Linting TypeScript..."
	cd packages/shinymap/js && npm run lint
	@echo "✓ Linting complete"

# Format
format:
	@echo "Formatting TypeScript..."
	cd packages/shinymap/js && npm run format
	@echo "✓ Formatting complete"

# Install dependencies
install:
	@echo "Installing Node.js dependencies..."
	cd packages/shinymap/js && npm install
	@echo "Installing Python dependencies..."
	uv sync
	@echo "✓ Dependencies installed"

# Documentation targets

# Build full documentation site
docs: docs-python docs-typescript
	@echo "Building Quarto site..."
	cd docs && uv run quarto render
	@echo "✓ Documentation built at docs/_site/"

# Generate Python API docs
docs-python:
	@echo "Generating Python API documentation..."
	cd docs && uv run quartodoc build
	@echo "✓ Python API docs generated"

# Generate TypeScript API docs
docs-typescript:
	@echo "Generating TypeScript API documentation..."
	cd packages/shinymap/js && npm run docs
	@echo "✓ TypeScript API docs generated"

# Preview documentation site locally
docs-preview:
	@echo "Starting documentation preview server..."
	cd docs && uv run quarto preview
