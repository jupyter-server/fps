# Changes in FPS {#changelog}

<!-- <START NEW CHANGELOG ENTRY> -->

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

<!-- <END NEW CHANGELOG ENTRY> -->

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
