.PHONY: install run test smoke migrate ekadasi clean

install:
	pip install -e ".[dev]"

run:
	streamlit run sadhana_setu/ui/app.py

test:
	pytest -v

smoke:
	python -m sadhana_setu smoke

migrate:
	python -m sadhana_setu migrate

ekadasi:
	python -m sadhana_setu ekadasi

clean:
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__ *.egg-info build dist
	find . -name '*.pyc' -delete
