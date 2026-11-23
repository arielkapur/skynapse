#!/bin/bash
# Native macOS runner only. Called by GitHub Actions; emits a .app and .dmg.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m pytest -q tests
"$PYTHON" scripts/make_icon.py
mkdir -p icon.iconset
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" scripts/SkySynoptic-icon.png --out "icon.iconset/icon_${size}x${size}.png" >/dev/null
  if [ "$size" -le 512 ]; then
    double=$((size*2))
    sips -z "$double" "$double" scripts/SkySynoptic-icon.png --out "icon.iconset/icon_${size}x${size}@2x.png" >/dev/null
  fi
done
iconutil -c icns icon.iconset -o SkySynoptic.icns
args=(--noconfirm --clean --onedir --windowed --name SkySynoptic --osx-bundle-identifier org.skysynoptic.desktop
  --icon SkySynoptic.icns --add-data 'index.html:.' --add-data 'grid_geo.py:.'
  --hidden-import cfgrib.xarray_plugin --hidden-import webview.platforms.cocoa
  --collect-all cfgrib --copy-metadata cfgrib --collect-all eccodes --collect-all eccodeslib --collect-all webview)
if [ -n "${APPLE_SIGNING_IDENTITY:-}" ]; then
  args+=(--codesign-identity "$APPLE_SIGNING_IDENTITY" --osx-entitlements-file macos-entitlements.plist)
fi
"$PYTHON" -m PyInstaller "${args[@]}" desktop.py
app="dist/SkySynoptic.app"
test -d "$app"
"$PYTHON" scripts/patch_info_plist.py "$app"
if [ -n "${APPLE_SIGNING_IDENTITY:-}" ]; then
  codesign --force --deep --options runtime --timestamp --entitlements macos-entitlements.plist --sign "$APPLE_SIGNING_IDENTITY" "$app"
  codesign --verify --deep --strict --verbose=2 "$app"
else
  # Ad-hoc is for CI/debug only. It is NOT trusted by Gatekeeper.
  codesign --force --deep --sign - "$app"
  codesign --verify --deep --verbose=2 "$app"
fi
"$app/Contents/MacOS/SkySynoptic" --self-test
if [ -n "${APPLE_SIGNING_IDENTITY:-}" ]; then
  test -n "${APPLE_ID:-}" && test -n "${APPLE_APP_PASSWORD:-}" && test -n "${APPLE_TEAM_ID:-}" || {
    echo 'Signing credentials provided but notarization credentials missing.' >&2; exit 1;
  }
  ditto -c -k --keepParent "$app" dist/SkySynoptic-app-notary.zip
  xcrun notarytool submit dist/SkySynoptic-app-notary.zip --apple-id "$APPLE_ID" --password "$APPLE_APP_PASSWORD" --team-id "$APPLE_TEAM_ID" --wait
  xcrun stapler staple "$app"
  xcrun stapler validate "$app"
fi
mkdir -p dist/dmg-stage
# Ditto preserves macOS bundle attributes and resource forks.
ditto "$app" dist/dmg-stage/SkySynoptic.app
ln -s /Applications dist/dmg-stage/Applications
arch="$(uname -m)"
if [ -n "${APPLE_SIGNING_IDENTITY:-}" ]; then
  image="dist/SkySynoptic-macOS-${arch}-signed.dmg"
else
  image="dist/SkySynoptic-macOS-${arch}-UNSIGNED-TEST-ONLY.dmg"
fi
hdiutil create -quiet -ov -fs HFS+ -format UDZO -volname SkySynoptic -srcfolder dist/dmg-stage "$image"
if [ -n "${APPLE_SIGNING_IDENTITY:-}" ]; then
  codesign --force --sign "$APPLE_SIGNING_IDENTITY" --timestamp "$image"
  xcrun notarytool submit "$image" --apple-id "$APPLE_ID" --password "$APPLE_APP_PASSWORD" --team-id "$APPLE_TEAM_ID" --wait
  xcrun stapler staple "$image"
  xcrun stapler validate "$image"
  spctl --assess --type execute -vv "$app"
fi
shasum -a 256 "$image" | tee "${image}.sha256"
echo "Built: $image"
