.PHONY: build clean install test docs preview-docs test-release release travisci-install travisci-test

##
# Variables
##

ENV_NAME = env
ENV_ACT = . env/bin/activate;
PIP = $(ENV_NAME)/bin/pip
PYTEST_ARGS = --doctest-modules -v -s
PYTEST_TARGET = alchy tests
COVERAGE_ARGS = --cov-config setup.cfg --cov-report term-missing --cov
COVERAGE_TARGET = alchy

##
# Targets
##

build: clean install

clean:
	rm -rf $(ENV_NAME)
	rm -rf .tox
	find . -name \*.pyc -type f -delete
	find . -depth -name __pycache__ -type d -exec rm -rf {} \;
	rm -rf dist *.egg* build

install:
	rm -rf $(ENV_NAME)
	virtualenv $(ENV_NAME) --python=python2.7
	$(PIP) install -r requirements.txt

test:
	$(ENV_ACT) py.test $(PYTEST_ARGS) $(COVERAGE_ARGS) $(COVERAGE_TARGET) $(PYTEST_TARGET)

docs:
	$(ENV_ACT) mkdocs build

preview-docs:
	$(ENV_ACT) mkdocs serve

test-release:
	rm -rf .tox
	$(ENV_ACT) tox

release:
	$(ENV_ACT) python setup.py sdist bdist_wheel
	$(ENV_ACT) twine upload dist/*
	rm -rf dist *.egg* build

##
# TravisCI
##

travisci-install:
	pip install -r requirements.txt

travisci-test:
	py.test $(PYTEST_ARGS) $(COVERAGE_ARGS) $(COVERAGE_TARGET) $(PYTEST_TARGET)
