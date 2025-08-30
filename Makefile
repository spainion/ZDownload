.PHONY: init lint test context suggest models check

init:
	./init.sh

lint:
	pre-commit run --all-files

context:
        python scripts/context_snapshot.py
        python scripts/code_scan.py

suggest:
	python scripts/llm_suggest.py "$(PROMPT)"

models:
	python scripts/openrouter_models.py

test:
	ruff check ZDownloadManager
	python -m py_compile $(shell find ZDownloadManager -name '*.py')
	(cd ZDownloadManager && python -m unittest discover tests -v)

check:
	python scripts/context_snapshot.py --check
	pre-commit run --all-files
	ruff check ZDownloadManager
	python -m py_compile $(shell find ZDownloadManager -name '*.py')
	(cd ZDownloadManager && python -m zdownloadmanager.cli --help)
	(cd ZDownloadManager && python -m unittest discover tests -v)
