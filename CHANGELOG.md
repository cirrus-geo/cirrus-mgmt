# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Support for `cirrus-geo>=0.15.0` with WorkflowEventManager changes around
  ProcessPayloads. ([#12])
- Added support for Python 3.12

### Changed

- Given the heavy changes initiated with
  [cirrus-geo#268](https://github.com/cirrus-geo/cirrus-geo/pull/268),
  `cirrus-mgmt` is now pinned to use the stable releases of cirrus-geo
  (`<1.0`). As described, in that PR, the management commands for releases
  `>=1.0` will not use this separate package.
- Updated Github Actions per nodejs16 deprecation notice in workflows.

### Removed

- Python support for python 3.8.

## [v0.1.1] - 2024-02-16

### Fixed

- CLI `run-workflow` dropped an `s` from `json.loads`, and the help text on the
  timout argument was
  incorrect. ([#5](https://github.com/cirrus-geo/cirrus-mgmt/pull/5))
- Return correct execution(`[-1]`), as new Step Function executions are
  appended to the `executions` list, from the StateDB
  Item. ([#6](https://github.com/cirrus-geo/cirrus-mgmt/pull/6))
- Enable both `call` CLI to set exit status code based of `Deployment.call`,
  and exception raised from `subprocess.check_call` if used as a
  library. ([#7](https://github.com/cirrus-geo/cirrus-mgmt/pull/7)

## [v0.1.0] - 2023-08-01

### Added

- CLI and library functions to run a cirrus workflow, and collect its output.
  Also adds a `call` command which is similar to `exec` but uses a
  subprocess. And adds `invoke_lambda` which invokes lambdas that are part of
  the cirrus deployment. ([#4](https://github.com/cirrus-geo/cirrus-mgmt/pull/4)

## [v0.1.0a] - 2022-11-09

Initial release

[unreleased]: https://github.com/cirrus-geo/cirrus-mgmt/compare/v0.1.1...main
[v0.1.1]: https://github.com/cirrus-geo/cirrus-mgmt/compare/v0.1.0...v0.1.1
[v0.1.0]: https://github.com/cirrus-geo/cirrus-mgmt/compare/v0.1.0a...v0.1.0
[v0.1.0a]: https://github.com/cirrus-geo/cirrus-mgmt/releases/tag/v0.1.0a
[#12]: https://github.com/cirrus-geo/cirrus-mgmt/pull/12
