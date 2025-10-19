.PHONY: run mypy test $(EXAMPLES)
EXAMPLES := $(notdir $(wildcard calliopy/examples/*.py))
EXAMPLES := $(EXAMPLES:.py=) 

all: run

run:
	uv run -m calliopy.main

$(EXAMPLES):
	uv run -m calliopy.examples.$@

mypy:
	uvx mypy calliopy/

test:
	PYTHONPATH=../calliopy uvx pytest
