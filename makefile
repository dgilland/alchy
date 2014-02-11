.PHONY: env test release

##
# Variables
##

ENV = . env/bin/activate;
PYTEST_ARGS = --doctest-modules -v -s
COVERAGE_ARGS = --cov-config setup.cfg --cov-report term-missing --cov

##
# Targets
##

build:
	rm -rf env
	virtualenv env --python=python2.7
	env/bin/pip install -r requirements.txt

test:
	$(ENV) py.test $(PYTEST_ARGS) $(COVERAGE_ARGS) alchy alchy tests

testall:
	$(ENV) tox

clean:
	rm -rf env
	find . -name \*.pyc -type f -delete
	find . -name __pycache__ -exec rm -rf {} \;
	rm -rf dist *.egg*

release:
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -rf dist *.egg*