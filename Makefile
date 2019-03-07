.PHONY: default
default: run

.PHONY: run
run:
	python githack http://127.0.0.1:8000

.PHONY: zipapprun
zipapprun:zipapp
	python githack.pyz http://127.0.0.1:8000

.PHONY: clean
clean:
	rm -r site

.PHONY: zipapp
zipapp:
	python -m zipapp githack
