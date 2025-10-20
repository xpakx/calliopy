.PHONY: run mypy test $(EXAMPLES) forwarder
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

forwarder: ./clibs/forward_trace.c
	gcc -fPIC -shared ./clibs/forward_trace.c -o ./clibs/forward_trace.so

