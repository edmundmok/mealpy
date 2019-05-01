.DEFAULT_GOAL := test

.PHONY: venv
venv:
	bin/venv_update.py \
		venv= -p python3 venv \
		install= -r requirements-dev.txt -rrequirements.txt \
		bootstrap-deps= -r requirements-bootstrap.txt \
		>/dev/null
	venv/bin/pre-commit install --install-hooks

.PHONY: test
test: venv
	venv/bin/coverage run -m pytest --strict tests/
	venv/bin/coverage report --show-missing --skip-covered --fail-under 64 --omit 'tests/*'
	venv/bin/coverage report --show-missing --skip-covered --fail-under 100 --include 'tests/*'
	venv/bin/check-requirements

.PHONY: clean
clean: ## Clean working directory
	find . -iname '*.pyc' | xargs rm -f
	rm -rf ./venv
