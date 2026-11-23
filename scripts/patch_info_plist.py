"""Applied after PyInstaller and before final code signing."""
import plistlib,sys
from pathlib import Path
app=Path(sys.argv[1]); p=app/'Contents'/'Info.plist'
with p.open('rb') as f: info=plistlib.load(f)
info['CFBundleIdentifier']='org.skysynoptic.desktop'
info['NSLocationWhenInUseUsageDescription']='SkySynoptic uses your location only to centre the weather map when you request it.'
info['NSAppTransportSecurity']={**info.get('NSAppTransportSecurity',{}),'NSAllowsLocalNetworking':True}
info['LSMinimumSystemVersion']='13.0'
with p.open('wb') as f: plistlib.dump(info,f)
