"""SkySynoptic native desktop entry point.

Packaged as SkySynoptic.app. Runs its bundled forecast server on an ephemeral
loopback port, displays a native WKWebView via pywebview, and exits cleanly.
No Terminal, global Python install, or fixed port 8000 is necessary.
"""
import sys
from threading import Thread
from urllib.request import urlopen


def self_test(check_backend=True):
    """Offline packaging smoke test; no NOAA requests or GUI required."""
    from server import make_server
    if check_backend:
        import eccodes
        import xarray as xr
        assert eccodes.codes_get_api_version(), 'ecCodes library did not initialise'
        assert 'cfgrib' in xr.backends.list_engines(), 'cfgrib xarray backend was not bundled'
    server = make_server(port=0)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        port=server.server_address[1]
        with urlopen(f'http://127.0.0.1:{port}/', timeout=10) as response:
            content=response.read()
            assert response.status == 200 and b'SkySynoptic' in content
        print(f'SELF-TEST PASS: local frontend on port {port}',flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main():
    if '--self-test' in sys.argv:
        self_test()
        return
    from server import make_server
    import webview
    server=make_server(port=0)
    worker=Thread(target=server.serve_forever,name='SkySynoptic forecast server',daemon=True)
    worker.start()
    url=f'http://127.0.0.1:{server.server_address[1]}/'
    try:
        webview.create_window('SkySynoptic',url,width=1440,height=900,min_size=(900,600),background_color='#202020')
        webview.start()
    finally:
        server.shutdown()
        server.server_close()


if __name__=='__main__':
    main()
