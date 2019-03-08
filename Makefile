.PHONY: default
default: run

.PHONY: run
run:
	python githack http://127.0.0.1:8000

.PHONY: zipapprun
zipapprun:zipapp
	python githack.pyz http://127.0.0.1:8000

.PHONY: build
build:
	python setup.py bdist_wheel

.PHONY: clean
clean:
	rm -Ir site dist build githack.egg-info

.PHONY: zipapp
zipapp:
	python -m zipapp githack
