.PHONY: explain
explain:
	### Welcome
	#
	### Targets
	@cat Makefile* | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

##
# Installation
##

.PHONY: clean
clean: ## Clean the local folder
	rm -fr reports .coverage .pytest_cache .ruff_cache

.PHONY: clean-dependencies
clean-dependencies: ## Clean the dependencies
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .ruff_cache

.PHONY: install
install: ## Install and run the dependencies
	uv sync --locked


##
# Quality
##
.PHONY: lint
lint: ## Lint the code with Ruff
	uv run ruff check

.PHONY: lint-fix
lint-fix: ## Lint the code with Ruff and fix
	uv run ruff check --fix

.PHONY: test
test: ## Run the tests
	PYTHONPATH=$(PWD) uv run pytest

.PHONY: test-cov
test-cov: ## Run the tests with coverage report
	PYTHONPATH=$(PWD) uv run pytest --cov --cov-report=term --cov-report=html
