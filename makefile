.PHONY: env test release

##
# Variables
##

ENV_NAME = env
ENV_ACT = . env/bin/activate;
PIP = $(ENV_NAME)/bin/pip
PYTEST_ARGS = --doctest-modules -v -s
COVERAGE_ARGS = --cov-config setup.cfg --cov-report term-missing --cov

##
# Targets
##

build:
	rm -rf $(ENV_NAME)
	virtualenv $(ENV_NAME) --python=python2.7
	$(PIP) install -r requirements.txt

test:
	$(ENV_ACT) py.test $(PYTEST_ARGS) $(COVERAGE_ARGS) alchy alchy tests

testall:
	$(ENV_ACT) tox

clean:
	rm -rf $(ENV_NAME)
	find . -name \*.pyc -type f -delete
	find . -name __pycache__ -exec rm -rf {} \;
	rm -rf dist *.egg*

release:
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -rf dist *.egg*