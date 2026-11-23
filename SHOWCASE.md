# SkySynoptic — project showcase

> **Status:** Scientific software prototype / source-defined macOS packaging workflow. **Not a verified signed or notarised Mac app release.**

**Source:** https://github.com/arielkapur/skynapse  
**Portfolio:** https://arielkapur.github.io/#work (after approval)

## The idea

A visual atmospheric instrument: explore the weather as spatial, time-dependent physical data instead of reading a flat numerical forecast.

SkySynoptic is a forecast-map viewer using real NOAA GFS model data. The project explores pressure contours, cloud cover, and forecast variables on a map, with a packaging workflow being prepared to turn the locally served interface into a native-window macOS application.

## What the source currently covers

- NOAA GFS model data requested for a regional forecast window.
- Pressure contours, cloud cover, temperature, humidity and precipitation layers.
- A timeline / forecast-frame interface.
- Mercator-row resampling and longitude wraparound handling for geographic displays.
- A Python backend with scientific data libraries and a Leaflet frontend.
- A macOS build pipeline targeting Intel and Apple Silicon, using PyInstaller and pywebview, with signing/notarisation steps when properly configured.

## Important distinction: source versus release

The repository documents source code and a prepared GitHub Actions workflow. This does **not** itself demonstrate that a working desktop app or notarised DMG has been built or tested on a Mac. The README identifies the verified and unverified parts of the build process, required Apple Developer credentials, and limitations.

Avoid presenting the workflow as a finished consumer release until actual CI artifacts and a macOS runtime test are available.

## For portfolio readers

**Category:** Scientific software / meteorological visualization  
**Stack:** Python, NOAA GFS, xarray/cfgrib, ecCodes, Leaflet, PyInstaller/pywebview  
**Current public action:** Browse source and build documentation; not a one-click download of a verified app.

## Media to capture later

- A real screenshot of pressure contours over a selected geographic region.
- A short weather-layer / forecast timeline screen recording from a running build.
- An architecture diagram: NOAA data → decoder/resampler → local server → map frontend → optional Cocoa window.
- A tested macOS build and screenshot only after successful workflow and runtime verification.

The current portfolio uses an original abstract illustration rather than claiming an unverified app screenshot.

## References

Read [README.md](README.md), [the GitHub Actions macOS workflow](.github/workflows/build-macos.yml), and the [source code](server.py) for setup details, limitations and implementation.
