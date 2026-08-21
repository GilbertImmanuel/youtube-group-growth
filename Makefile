# Override the interpreter with `make PY=path/to/python <target>`.
# Default assumes the intended environment is active on PATH.
PY ?= python

.PHONY: data clean features models report eval-collabs eval-matching test

data:
	$(PY) -m src.collect.youtube_api

clean:
	$(PY) -m src.clean.build

features:
	$(PY) -m src.features.panel

models:
	$(PY) -m src.models.did

report:
	$(PY) -m src.models.descriptive
	$(PY) -m src.viz.descriptive

eval-collabs:
	$(PY) -m src.features.collabs --eval

eval-matching:
	$(PY) -m src.features.panel --eval-matching

test:
	$(PY) -m pytest
