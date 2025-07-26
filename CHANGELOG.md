# Version history

<!-- <START NEW CHANGELOG ENTRY> -->

## 0.5.1

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.5.0...5fa147d95d96bbaa0393723c454b4eb32d0d590f))

### Merged PRs

- Don't nest contexts in modules [#137](https://github.com/jupyter-server/fps/pull/137) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-07-26&to=2025-07-26&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-07-26..2025-07-26&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 0.5.0

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.4.2...63d7ad9b68d36a822ae3d066d0650c22d0dd44e5))

### Merged PRs

- Support nested contexts [#136](https://github.com/jupyter-server/fps/pull/136) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-06-13&to=2025-07-26&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-06-13..2025-07-26&type=Issues)

## 0.4.2

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.4.1...1154d342b0543d82e104899d406246e5d09c8a34))

### Merged PRs

- Improve server start/stop [#135](https://github.com/jupyter-server/fps/pull/135) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-06-10&to=2025-06-13&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-06-10..2025-06-13&type=Issues)

## 0.4.1

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.4.0...3bdd5263c63848638112570c115e13948873f370))

### Merged PRs

- Log failure to acquire value [#134](https://github.com/jupyter-server/fps/pull/134) ([@davidbrochart](https://github.com/davidbrochart))
- Fix `SharedValue.get()` [#133](https://github.com/jupyter-server/fps/pull/133) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-05-22&to=2025-06-10&type=c))

[@adriendelsalle](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Aadriendelsalle+updated%3A2025-05-22..2025-06-10&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-05-22..2025-06-10&type=Issues) | [@fcollonval](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Afcollonval+updated%3A2025-05-22..2025-06-10&type=Issues)

## 0.4.0

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.3.0...8d8b4c7d9c189bd0f60c7094323369bd478f58e1))

### Merged PRs

- Split optional dependencies [#132](https://github.com/jupyter-server/fps/pull/132) ([@davidbrochart](https://github.com/davidbrochart))
- Make CLI optional [#131](https://github.com/jupyter-server/fps/pull/131) ([@davidbrochart](https://github.com/davidbrochart))
- Extract out server from `FastAPIModule` to `ServerModule` [#130](https://github.com/jupyter-server/fps/pull/130) ([@davidbrochart](https://github.com/davidbrochart))
- Add `Module` API documentation [#129](https://github.com/jupyter-server/fps/pull/129) ([@davidbrochart](https://github.com/davidbrochart))
- Use dependency groups for `test` and `docs` [#128](https://github.com/jupyter-server/fps/pull/128) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-04-21&to=2025-05-22&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-04-21..2025-05-22&type=Issues)

## 0.3.0

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.2.2...b587c686df102b7e85a4eedaefe6e5b467cbe5f0))

### Merged PRs

- [#126](https://github.com/jupyter-server/fps/pull/126) ([@davidbrochart](https://github.com/davidbrochart)), [#127](https://github.com/jupyter-server/fps/pull/127) ([@davidbrochart](https://github.com/davidbrochart)).
- Add API documentation.
- Change `exclusive` argument of `SharedValue()`, `Context.put()` and `Module.put()` to `max_boworrers`.
- Add `manage` argument of `SharedValue()` and `Context.put()` to use its context manager for setup/teardown.
- Add `add_teardown_callback()` method to `Context` and `Module` to register a teardown callback.
- Add `shared_value` argument of `Context.put()` to share a value in multiple contexts.
- Add `timeout` argument of `SharedValue.get()` and `Context.get()`.
- Add `teardown_callback` argument of `SharedValue()` and `Module.put()`.
- Remove `SharedValue.set_teardown_callback()`.

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-04-01&to=2025-04-21&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-04-01..2025-04-21&type=Issues)

## 0.2.2

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.2.1...78d1d789a9330a75eadb5a75d9e059d2d01a4538))

### Merged PRs

- Add Signal documentation [#125](https://github.com/jupyter-server/fps/pull/125) ([@davidbrochart](https://github.com/davidbrochart))
- Add Signal iterator [#124](https://github.com/jupyter-server/fps/pull/124) ([@davidbrochart](https://github.com/davidbrochart))
- Add Signal [#123](https://github.com/jupyter-server/fps/pull/123) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-03-31&to=2025-04-01&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-03-31..2025-04-01&type=Issues)

## 0.2.1

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.2.0...77c09d4d8248dba75841a2d5317bb69f3872d31b))

### Merged PRs

- Export SharedValue [#122](https://github.com/jupyter-server/fps/pull/122) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-03-26&to=2025-03-31&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-03-26..2025-03-31&type=Issues)

## 0.2.0

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.1.6...f16bd46ed2815b4d618c10b76908581d073ab2b4))

### Merged PRs

- Revert "Update to latest Jupyter Release Actions" [#121](https://github.com/jupyter-server/fps/pull/121) ([@Zsailer](https://github.com/Zsailer))
- Update to latest Jupyter Release Actions [#120](https://github.com/jupyter-server/fps/pull/120) ([@Zsailer](https://github.com/Zsailer))
- Add context documentation [#119](https://github.com/jupyter-server/fps/pull/119) ([@davidbrochart](https://github.com/davidbrochart))
- Convert repo to use releaser from repo [#118](https://github.com/jupyter-server/fps/pull/118) ([@davidbrochart](https://github.com/davidbrochart))
- Add optional `teardown_callback` parameter to `Context.put()` [#117](https://github.com/jupyter-server/fps/pull/117) ([@davidbrochart](https://github.com/davidbrochart))
- Add Context [#116](https://github.com/jupyter-server/fps/pull/116) ([@davidbrochart](https://github.com/davidbrochart))
- Add concurrency test for tasks [#115](https://github.com/jupyter-server/fps/pull/115) ([@davidbrochart](https://github.com/davidbrochart))
- Add .gitignore [#114](https://github.com/jupyter-server/fps/pull/114) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-03-19&to=2025-03-26&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-03-19..2025-03-26&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Apre-commit-ci+updated%3A2025-03-19..2025-03-26&type=Issues) | [@Zsailer](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3AZsailer+updated%3A2025-03-19..2025-03-26&type=Issues)

## 0.1.6

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.1.5...1fa4f5bef6cd23682e882f0bf3c2d5654be12108))

### Merged PRs

- missing default values in cli.main [#113](https://github.com/jupyter-server/fps/pull/113) ([@minrk](https://github.com/minrk))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-03-06&to=2025-03-19&type=c))

[@minrk](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Aminrk+updated%3A2025-03-06..2025-03-19&type=Issues)

## 0.1.5

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.1.4...7d84a4fbd7495676227d2e97e7418c348bec4662))

### Merged PRs

- Require anycorn >=0.18.1 [#111](https://github.com/jupyter-server/fps/pull/111) ([@davidbrochart](https://github.com/davidbrochart))
- Fix KeyboardInterrupt handling on Trio [#110](https://github.com/jupyter-server/fps/pull/110) ([@davidbrochart](https://github.com/davidbrochart))
- Support running on Trio [#109](https://github.com/jupyter-server/fps/pull/109) ([@davidbrochart](https://github.com/davidbrochart))
- Add --help-all CLI option [#108](https://github.com/jupyter-server/fps/pull/108) ([@davidbrochart](https://github.com/davidbrochart))
- Add --show-config CLI option [#107](https://github.com/jupyter-server/fps/pull/107) ([@davidbrochart](https://github.com/davidbrochart))
- Bump anyioutils v0.7.0 [#106](https://github.com/jupyter-server/fps/pull/106) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-02-26&to=2025-03-06&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-02-26..2025-03-06&type=Issues)

## 0.1.4

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.1.3...68a4b47acb16fd8570d8c086a84c737399cef086))

### Merged PRs

- Stop application when background tasks fail [#105](https://github.com/jupyter-server/fps/pull/105) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-02-26&to=2025-02-26&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-02-26..2025-02-26&type=Issues)

## 0.1.3

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.1.2...f86c6487fd3512cc6fb8883f3a7049aed857157e))

### Merged PRs

- Wait for server to be started [#104](https://github.com/jupyter-server/fps/pull/104) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-02-16&to=2025-02-26&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-02-16..2025-02-26&type=Issues)

## 0.1.2

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.1.1...0823e706665a44475a6d1065a7f7ff24d216204f))

### Merged PRs

- Fix CLI [#102](https://github.com/jupyter-server/fps/pull/102) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-02-07&to=2025-02-16&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-02-07..2025-02-16&type=Issues)

## 0.1.1

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.1.0...31fcee05d8ac894e971aa1b083c0831eb6679b97))

### Merged PRs

- Add documentation [#100](https://github.com/jupyter-server/fps/pull/100) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2025-02-05&to=2025-02-07&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2025-02-05..2025-02-07&type=Issues)

## 0.1.0

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.21...14bb99d3c8129cc9adc32ee8ff9b1c6e4fb0d512))

### Merged PRs

- Remove "value" from API [#99](https://github.com/jupyter-server/fps/pull/99) ([@davidbrochart](https://github.com/davidbrochart))
- Merge FastAIO [#98](https://github.com/jupyter-server/fps/pull/98) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-11-23&to=2025-02-05&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-11-23..2025-02-05&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Apre-commit-ci+updated%3A2022-11-23..2025-02-05&type=Issues)

## 0.0.21

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.20...c7e394d1ee94837c4118d24a0c86f9499ae90e3d))

### Merged PRs

- Allow setting log level [#86](https://github.com/jupyter-server/fps/pull/86) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-09-19&to=2022-11-23&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-09-19..2022-11-23&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Apre-commit-ci+updated%3A2022-09-19..2022-11-23&type=Issues)

## 0.0.20

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.19...503fbae2b5d54306c27b8fc9a195e4af1ec96c4e))

### Merged PRs

- Wait for server started before opening browser [#83](https://github.com/jupyter-server/fps/pull/83) ([@davidbrochart](https://github.com/davidbrochart))
- Switch to hatch [#82](https://github.com/jupyter-server/fps/pull/82) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-08-31&to=2022-09-19&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-08-31..2022-09-19&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Apre-commit-ci+updated%3A2022-08-31..2022-09-19&type=Issues)

## 0.0.19

No merged PRs

## 0.0.18

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.17...e1f6ea6f9a2f02e0e00bbea1dfbd0c6f52e4c23a))

### Merged PRs

- Use Rich in typer [#78](https://github.com/jupyter-server/fps/pull/78) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-08-30&to=2022-08-31&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-08-30..2022-08-31&type=Issues)

## 0.0.17

No merged PRs

## 0.0.16

No merged PRs

## 0.0.15

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.14...a5caf65d3a8c88c3be11b509812fae58bad3414a))

### Merged PRs

- Fix releasing of fps-uvicorn [#74](https://github.com/jupyter-server/fps/pull/74) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-08-29&to=2022-08-29&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-08-29..2022-08-29&type=Issues)

## 0.0.14

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.13...1d48dbfa3838e1f5635edcc7f3ced17714901518))

### Merged PRs

- Store Uvicorn CLI options, add possibility to pass query parameters [#72](https://github.com/jupyter-server/fps/pull/72) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-08-29&to=2022-08-29&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-08-29..2022-08-29&type=Issues)

## 0.0.13

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.12...166041e3346e3fa6773f8d6f48b08dacee785cb5))

### Merged PRs

- Fix exit [#70](https://github.com/jupyter-server/fps/pull/70) ([@davidbrochart](https://github.com/davidbrochart))
- [pre-commit.ci] pre-commit autoupdate [#69](https://github.com/jupyter-server/fps/pull/69) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- [pre-commit.ci] pre-commit autoupdate [#68](https://github.com/jupyter-server/fps/pull/68) ([@pre-commit-ci](https://github.com/pre-commit-ci))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-07-14&to=2022-08-29&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-07-14..2022-08-29&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Apre-commit-ci+updated%3A2022-07-14..2022-08-29&type=Issues)

## 0.0.12

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.11...724caf852e8952a5e7eb89c604d3d5d6179e4040))

### Merged PRs

- Rework application plugin [#66](https://github.com/jupyter-server/fps/pull/66) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-07-14&to=2022-07-14&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-07-14..2022-07-14&type=Issues)

## 0.0.11

([Full Changelog](https://github.com/jupyter-server/fps/compare/v0.0.10...1474ca165a9e6aa8434ed630382fb111d065715b))

### Merged PRs

- Add application pluggin [#64](https://github.com/jupyter-server/fps/pull/64) ([@davidbrochart](https://github.com/davidbrochart))
- [pre-commit.ci] pre-commit autoupdate [#63](https://github.com/jupyter-server/fps/pull/63) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- FPS is not experimental anymore [#62](https://github.com/jupyter-server/fps/pull/62) ([@davidbrochart](https://github.com/davidbrochart))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2022-05-17&to=2022-07-14&type=c))

[@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2022-05-17..2022-07-14&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Apre-commit-ci+updated%3A2022-05-17..2022-07-14&type=Issues)

## 0.0.10

([Full Changelog](https://github.com/jupyter-server/fps/compare/fps-0.0.9...189716c887dcd008561292f4d33d6a5f252a920f))

### Merged PRs

- Prepare for use with Jupyter Releaser [#60](https://github.com/jupyter-server/fps/pull/60) ([@davidbrochart](https://github.com/davidbrochart))
- Allow startup/shutdown to run in tests [#59](https://github.com/jupyter-server/fps/pull/59) ([@davidbrochart](https://github.com/davidbrochart))
- [pre-commit.ci] pre-commit autoupdate [#57](https://github.com/jupyter-server/fps/pull/57) ([@pre-commit-ci](https://github.com/pre-commit-ci))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/fps/graphs/contributors?from=2021-10-29&to=2022-05-17&type=c))

[@adriendelsalle](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Aadriendelsalle+updated%3A2021-10-29..2022-05-17&type=Issues) | [@davidbrochart](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Adavidbrochart+updated%3A2021-10-29..2022-05-17&type=Issues) | [@fcollonval](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Afcollonval+updated%3A2021-10-29..2022-05-17&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Ffps+involves%3Apre-commit-ci+updated%3A2021-10-29..2022-05-17&type=Issues)

0.0.9 (October 29, 2021)
========================

New features:
- Add root_path to uvicorn plugin (#38 @davidborchart)
- Add enabled_plugins config (#42 @adriendelsalle)

Improvements:
- Handle list delimiters for disabled_plugins (#41 #52 @adriendelsalle)
- Improve log messages for conflicting routes (#43 @adriendelsalle)
- Catch mounts masking routes (#45 @adriendelsalle)
- Add tests on configuration (#46 @adriendelsalle)
- housekeeping (#47 #51 @adriendelsalle #48 @davidborchart)

0.0.8 (September 22, 2021)
==========================

New features:
- Add capability to disable plugins (#30 @adriendelsalle)
- Add a new hook to register exception handlers (#31 @adriendelsalle)
- Add a builtin RedirectException (#33 @adriendelsalle)

Improvements:
- Group router logs (#28 @adriendelsalle)
- Minor improvements on pip recipes (#34 @adriendelsalle)

Bug fixes:
- Fix interactive API docs (#28 @davidborchart)

Breaking change:
- Make uvicorn server a plugin (#32 #35 @adriendelsalle)

0.0.7 (September 13, 2021)
==========================

New features:
- Add testing module and `pytest` generic fixtures (#19 @adriendelsalle)

Improvements:
- Support `pluggy 1.0.0` and future releases (#15 @adriendelsalle)
- Improve CLI parsing of plugins options (#17 @adriendelsalle)

Bug fixes:
- Fix `python 3.7` compatibility (#18 @adriendelsalle)

Documentation:
- Document testing module (#20 #21 @adriendelsalle)

0.0.6 (September 8, 2021)
=========================

New features:
- Add capability to pass router kwargs when registering it (#10 @davidbrochart)

Documentation:
- Remove note about CLI limited to FPS config, since plugins ones are now supported (#13 @davidbrochart)

0.0.5 (August 6, 2021)
======================

New features:
- Add capability to pass any plugin configuration as a CLI extra argument (#5)

Bug fixes:
- Allow to pass a negative CLI flag `--no-<flag>` for boolean `open-browser` option
- Fix colors based on status code for `uvicorn` logs (#7)
