"""Launch the complete dashboard without installing any packages."""
import argparse, functools, http.server, webbrowser
from pathlib import Path
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);p.add_argument('--no-browser',action='store_true');a=p.parse_args()
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(Path(__file__).parent/'dist'))
    with http.server.ThreadingHTTPServer(('127.0.0.1',a.port),handler) as server:
        url=f'http://localhost:{a.port}';print(f'FloodLens: {url}\nPress Ctrl+C to stop.')
        if not a.no_browser:webbrowser.open(url)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
