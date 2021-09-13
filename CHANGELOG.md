0.0.7 (September 13, 2021)
========================

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
========================

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
