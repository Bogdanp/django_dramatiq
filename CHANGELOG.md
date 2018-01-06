# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2017-01-06
### Fixed

- `--path` is now the first to be passed to `dramatiq`.  This fixes an
  issue where the workers wouldn't boot when the `-no-reload` flag was
  set.

## [0.2.0] - 2017-01-06
### Added

- `--path` command line argument.

### Changed

- The broker is now set up by `DjangoDramatiqConfig.ready`.
- The minimum dramatiq version is now 0.18.
- `BASE_DIR` is no longer a required setting.

### Fixed

- `Task.message` no handles `memoryview`s properly.

## [0.1.5] - 2017-12-22
### Fixed

- Python 3.5 is now supported.

## [0.1.4] - 2017-12-08
### Fixed

- Fixed use of `tobytes()` in `Task.message` for Django 2.0.

## [0.1.3] - 2017-11-20
### Added

- `--reload-use-polling` flag to force a poll-based file watcher
  instead of a OS-native one.  This is useful inside of Vagrant and
  Docker. ([Dramatiq #18])

[Dramatiq #18]: https://github.com/Bogdanp/dramatiq/issues/18

## [0.1.2] - 2017-11-20
### Fixed

- Tasks modules and packages are now detected using Django's built-in
  ``module_has_submodule`` helper. ([@rakanalh])

[@rakanalh]: https://github.com/rakanalh

## [0.1.1] - 2017-11-15
### Fixed

- `dramatiq` and `dramatiq-gevent` are now resolved according to
  `sys.executable` ([@rakanalh]).

[@rakanalh]: https://github.com/rakanalh


[Unreleased]: https://github.com/Bogdanp/django_dramatiq/compare/v0.2.0...HEAD
[0.2.2]: https://github.com/Bogdanp/django_dramatiq/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/Bogdanp/django_dramatiq/compare/v0.2.0...v0.2.1
[0.1.5]: https://github.com/Bogdanp/django_dramatiq/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/Bogdanp/django_dramatiq/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/Bogdanp/django_dramatiq/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/Bogdanp/django_dramatiq/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Bogdanp/django_dramatiq/compare/v0.1.0...v0.1.1
