

install_prod:
	pip install .

install:
	pip install --editable .[dev]

typecheck:
	mypy -p cars

stylecheck:
	black --diff cars

style:
	black cars

check: typecheck stylecheck

test:
	python -m pytest -v cars