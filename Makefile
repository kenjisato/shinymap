.PHONY: help build build-js build-bundle clean test lint format install

# Default target
help:
	@echo "Shinymap Build Commands"
	@echo ""
	@echo "  make build        - Full build (TypeScript + bundle for Python)"
	@echo "  make build-js     - Build TypeScript only"
	@echo "  make build-bundle - Bundle JS for Python package only"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make install      - Install dependencies"

# Full build: TypeScript compilation + bundling for Python
build: build-js build-bundle
	@echo "✓ Full build complete"

# Build TypeScript
build-js:
	@echo "Building TypeScript..."
	cd packages/shinymap/js && npm run build
	@echo "✓ TypeScript compilation complete"

# Bundle for Python package
build-bundle:
	@echo "Bundling for Python package..."
	cd packages/shinymap/js && node build-global.js
	@echo "✓ Bundle created at packages/shinymap/python/src/shinymap/www/shinymap.global.js"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf packages/shinymap/js/dist
	rm -f packages/shinymap/python/src/shinymap/www/shinymap.global.js
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
