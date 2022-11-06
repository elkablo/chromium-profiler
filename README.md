# chromium-profiler

Chromium-profiler is a utility to test some web page cases in Chromium, meant to
profile Chromium for PGO.

## Why?

* Current versions of Google Chrome are compiled with PGO (Profile Guided
Optimizations). We also want this for Chromium.
* Chromium source code contains [documentation](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/pgo.md)
  for how to compile with PGO, but
  1. The `tools/perf/run_benchmark` utility used for profiling depends on
     `vpython` and various other stuff (most of that is bundled in Chromium
     sources, but not all).
  2. The profiling cases for the `tools/perf/run_benchmark` need
     [Web Page Replay](https://chromium.googlesource.com/catapult/+/HEAD/web_page_replay_go)
     archives, which [Google does not share publicly](https://www.chromium.org/developers/telemetry/upload_to_cloud_storage).

  For automatized profiling the community therefore needs to create it's own Web
  Page Replay archives.

## Dependencies

* [Web Page Replay](https://chromium.googlesource.com/catapult/+/HEAD/web_page_replay_go)
  compiled as a binary with name `wpr` (Gentoo package
  `dev-util/web_page_replay_go` from [this repository](https://github.com/elkablo/wpr-gentoo))
* [Selenium WebDriver](https://www.selenium.dev/) (Gentoo package
  `dev-python/selenium`)

## How to use

To run all test cases, run
```shell
./chromium_profiler.py --chrome-executable PATH_TO_CHROME --chromedriver-executable PATH_TO_CHROMEDRIVER
```
replacing `PATH_TO_CHROME` and `PATH_TO_CHROMEDRIVER` as needed. On amd64
Gentoo, for example, these are `/usr/lib64/chromium-browser/chrome` and
`/usr/lib64/chromium-browser/chromedriver`.

If Chromium is compiled to generate LLVM profiling data, the results will be
stored in various files in a temporary directory and removed after the run.
If the `--profile-output` option is specified, the profiling results of all
the runs will be incrementally merged with the `llvm-profdata` utility into
the file specified by that option. Thus the `llvm-profdata` utility must be
in the `PATH` environment variable if `--profile-output` option is specified.

To list available cases, use the `--list-cases` option.

To test specific cases, use the `--case` option, which accepts glob-style
patterns and can be used multiple times.

To use additional arguments for starting the browser, use the `--add-arg`
option.
