.PHONY: default
default: lint

.PHONY: init
init: githooks

.PHONY: tools
tools: init
	pip3 install --upgrade pipenv build
	pipenv install --dev

.PHONY: githooks
githooks:
	@if command -v git > /dev/null; then \
		git config core.hooksPath .githooks; \
	fi

.PHONY: lint
lint: init
	pipenv run pylint3 src bin/pifan

.PHONY: mypy
mypy: init
	pipenv run mypy src bin/pifan

.PHONY: pycodestyle
pycodestyle: init
	pipenv run pycodestyle --config .pycodestyle src bin/pifan

.PHONY: build
build:
	python3 -m build

.PHONY: install
install:
	sudo -H pip3 install --upgrade .

.PHONY: uninstall
uninstall:
	sudo -H pip3 uninstall pifan
