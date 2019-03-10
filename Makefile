.PHONY: default
default: run

.PHONY: run
run:
	python githack http://127.0.0.1:8000

.PHONY: runzipapp
runzipapp: buildzipapp
	python githack.pyz http://127.0.0.1:8000

.PHONY: build
build:
	python setup.py bdist_wheel

.PHONY: buildzipapp
buildzipapp:
	# remove --compress cause python 3.6 not support compress
	# python -m zipapp --compress githack
	python -m zipapp githack

.PHONY: clean
clean:
	rm -Ir site dist build githack.egg-info
