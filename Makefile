.PHONY: default
default: lint

.PHONY: init
init: githooks

# Install build dependencies.
.PHONY: tools
tools: init
	pip3 install --upgrade build pylint3

.PHONY: githooks
githooks:
	@if command -v git > /dev/null; then \
		git config core.hooksPath .githooks; \
	fi

.PHONY: lint
lint: init
	pylint3 . bin/pifan

# Build distribution package in dist directory.
.PHONY: build
build:
	python3 -m build

.PHONY: install
install:
	sudo -H pip3 install --upgrade .

.PHONY: uninstall
uninstall:
	sudo -H pip3 uninstall pifan
