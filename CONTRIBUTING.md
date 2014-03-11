# How to Contribute

## Table of Contents

- [Overview](#overview)
- [Guidelines](#guidelines)
- [Continuous Integration](#continuous-integration)
- [Project CLI](#project-cli)
- [Areas of Needed Improvement](#areas-of-needed-improvement)

## Overview

1. Fork the repo.
2. Build development environment run tests to ensure a clean, working slate.
4. Improve/fix the code.
5. Add test cases if new functionality introduced or bug fixed (100% test coverage).
6. Ensure tests pass.
7. Add yourself to `CONTRIBUTORS.md`.
8. Push to your fork and submit a pull request.

## Guidelines

Some simple guidelines to follow when contributing code:

- Adhere to [PEP8][] except as specified in `setup.cfg`, section `pep8`.
- Clean, well documented code.
- All tests pass.
- 100% test coverage.

## Continuous Integration

Integration testing is provided by [Travis-CI][]: https://travis-ci.org/dgilland/alchy.

Test coverage reporting is provided by [Coveralls][]: https://coveralls.io/r/dgilland/alchy.

## Project CLI

Some useful CLI commands when working on the project are below. **NOTE:** All commands are run from the root of the project and require `make`.

### make build

Run the `clean` and `install` commands.

```
make build
```

### make install

Create virtualenv `env/` and installs Python dependencies.

```
make install
```

### make clean

Remove build/test related temporary files like `env/`, `.tox`, `.coverage`, and `__pycache__`.

```
make clean
```

### make test

Run unittests under the virtualenv's default Python version. Does not test all support Python versions. To test all supported versions, see `make test-full`.

```
make test
```

### make test-full

Run unittest and linting for all supported Python versions. **NOTE:** This will fail if you do not have all Python versions installed on your system. If you are on an Ubuntu based system, the [Dead Snakes PPA][] is a good resource for easily installing multiple Python versions. If for whatever reason you're unable to have all Python versions on your development machine, note that Travis-CI will run full integration tests on all pull requests (minus linting).

```
make test-full
```

### make pep8

Run [PEP8][] compliance check on code base.

```
make pep8
```

### make preview-docs

Preview docs using `mkdocs serve`. Docs will be accessible at http://localhost:8000 by default.

```
make preview-docs
```

## Areas of Needed Improvement

- Better documentation of functions/modules. Many are missing docstrings. Existing docstrings could be improved. Additional code comments may be needed as well.
- Improve code quality for readability (e.g. eliminate dense code statements like one-liners which do too much).
- Improve testing infrastructure. While not terrible, the organzation could be improved.
- More battle testing. Tests currently cover basic usage, but there may be more complex uses-cases that could draw out some edge-case bugs.
- Potentially improve `Query` loading methods. The current implementation doesn't handle nested loading options which differ than the base loading method used. For example, emulating this `query.options(joinedload(Foo).lazyload(Bar))` is not supported while this `query.options(joinedload(Foo).joinedload(Bar))` is via `query.joinedload(Foo, Bar)`. Would be nice to have a way to drill down into the nested loading strategies without having to use `query.options`. However, if the solution introduces too much complexity for a feature that isn't used/needed often, then it may be best to not attempt to support it.
- Improve `docs/` by providing more examples and better explanations.

[PEP8]: http://legacy.python.org/dev/peps/pep-0008/
[Travis-CI]: https://travis-ci.org/
[Coveralls]: https://coveralls.io/
[Dead Snakes PPA]: https://launchpad.net/~fkrull/+archive/deadsnakes
