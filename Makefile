# Default dir locations
PYTHON ?= /usr/bin/python

# Methods
.PHONY: all
all:
	$(PYTHON) -m pytest -vv

.PHONY: install
install:
	$(PYTHON) setup.py install

.PHONY: test
test:
	pip install -qr requirements.txt
	pip install -qr test-requirements.txt
	$(PYTHON) -m pytest -vv

.PHONY: image
image:
	docker build -t $(tag) .

.PHONY: syntax-check
syntax-check:
	flake8 atomicapp

.PHONY: clean
clean:
	$(PYTHON) setup.py clean --all
