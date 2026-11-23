# SkySynoptic — native macOS packaging project

**What this is:** The SkySynoptic NOAA GFS forecast map with a real macOS desktop entry point. When built on macOS, PyInstaller bundles the Python runtime, native GUI bridge, and scientific libraries into `SkySynoptic.app`; the app hosts its own local data server inside a native macOS window, using a random localhost port. The target end-user launch is double-clicking the app, **not** entering Terminal commands or keeping a Terminal window open.

**What this is not yet:** This ZIP is SOURCE CODE plus a prepared GitHub Actions Mac build workflow, **not a completed DMG**. The supplied environment runs Linux; no native macOS `.app`, actual `.dmg`, or Apple notarization has been built or verified. A signed/notarized release needs Apple Developer ID signing credentials and the Apple notarization service. An unsigned DMG is **not** exempt from Gatekeeper.

## Build without Terminal on your Mac (GitHub website)

1. Create a GitHub repository and upload the **contents** of this extracted folder, including the `.github/workflows/build-macos.yml` file. GitHub upload from the website is sufficient; no Mac Terminal setup is required.
2. Open **Actions → Build macOS app and DMG → Run workflow** in your repository. The workflow runs on macOS ARM64 and Intel machines. It builds the app, runs offline smoke checks, creates two DMGs, and uploads the resulting files in the workflow's **Artifacts** section.
3. **For normally trusted DMGs**, first set repository **Settings → Secrets and variables → Actions** with these secrets:

   | Secret | Purpose |
   |---|---|
   | `APPLE_DEVELOPER_CERTIFICATE_P12_BASE64` | Base64-encoded Developer ID Application `.p12` certificate and private key |
   | `APPLE_CERTIFICATE_PASSWORD` | Password for that `.p12` |
   | `APPLE_SIGNING_IDENTITY` | Exact Developer ID Application identity from Keychain |
   | `APPLE_ID` | Apple ID for notarization |
   | `APPLE_APP_SPECIFIC_PASSWORD` | App-specific password for Apple's notarytool |
   | `APPLE_TEAM_ID` | Developer Team ID |

   This requires an **Apple Developer Program membership** and a **Developer ID Application** certificate. Do not send any private key, Apple password, or signing secrets to ChatGPT or upload them inside the source ZIP. Configure them directly in GitHub Secrets.

4. Run the workflow again after adding secrets. It will sign, notarize, staple, and verify both the app and the DMG. Download the **signed** workflow artifacts. The DMG contains `SkySynoptic.app` and an Applications folder shortcut to drag it into Applications. Mac may still ask for **location permission** on demand; that is unrelated to Gatekeeper.

**Without Apple secrets:** the workflow intentionally marks its outputs `UNSIGNED-TEST-ONLY.dmg`. They cannot be represented as frictionless, Gatekeeper-trusted releases. If signing or notarization fails, the workflow fails rather than labeling its output signed.

## What changed since the previous version

- Fixed **0°/360° and ±180° longitude continuity**. The weather raster and contours stay aligned with the currently requested region instead of being stretched from the Indian Ocean across the world map.
- Added **Mercator-row resampling** for colour rasters. Data originally on regular geographic latitude rows should not be treated as equally spaced Mercator rows.
- The pressure contours use Gaussian smoothing (sigma 1.7 grid cells), retaining native 0.25° GFS model positions.
- NOAA pressure and cloud requests can execute concurrently, with a cap of three active downloads.
- The last manually selected/GPS-approved location is remembered locally.
- The native app chooses its own local port, so old test servers on `localhost:8000` do not prevent it launching.
- Cache files go to `~/Library/Caches/SkySynoptic` and remain outside the signed app bundle.

## Technical build chain (reproducible)

`requirements.txt` + `requirements-build.txt` → tests → PyInstaller on macOS with bundled assets, cfgrib, eccodes, eccodeslib, pywebview → add app privacy/localhost transport configuration → Developer ID **hardened-runtime code signing** → native app `--self-test` → notarize and staple the app → `hdiutil` DMG creation → sign, notarize and staple DMG → SHA-256 checksum → upload CI artifacts.

See `.github/workflows/build-macos.yml`, `scripts/build_macos.sh`, `scripts/patch_info_plist.py`, and `macos-entitlements.plist` for the exact build source of truth. Keep these checked into version control for all future versions. There is no need to manually execute these scripts if using the GitHub website workflow.

## Scope and known issues

The current frontend still fetches true NOAA GFS 0.25° data per forecast variable for a ~60° regional window. It includes sea-level pressure, forecast cloud cover, temperature, humidity, and precipitation, a timeline, layers, and automatic data load. It is **not** yet live satellite imagery, a wallpaper, or a worldwide tile server. Future model-hour playback depends on fetching forecast frames and is not guaranteed smooth at 10fps. The basemap and Leaflet JavaScript load from Internet hosts. NOAA availability and geolocation permissions still matter.

**Validation completed in this environment:** Python syntax, shell syntax and six offline regression tests. **Not validated:** actual macOS signing/notarization, compiled Cocoa window launch, live NOAA GRIB decode inside the frozen executable, or rendering in the user's browser. The CI job includes a compiled-app smoke check for key imports and the local frontend, but no automated live satellite/NOAA display test yet.

NOAA GFS: https://nomads.ncep.noaa.gov/ . Dependencies: Leaflet, pywebview, PyInstaller, xarray, cfgrib, ecCodes, NumPy, SciPy and Matplotlib. Check their respective licences and NOAA's access guidance before public redistribution.
