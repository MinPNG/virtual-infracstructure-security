#!/usr/bin/env python3

import os
from http.server import SimpleHTTPRequestHandler, HTTPServer, HTTPStatus

PORT = 3690

class SimpleServer(SimpleHTTPRequestHandler):
    def do_POST(self):
        path = self.translate_path(self.path)
        if os.path.exists(path) and os.path.isfile(path):
            try:
                f = open(path, 'wb')
            except OSError:
                self.send_error(HTTPStatus.NOT_FOUND, "Could not open file")
                return None
        else:
            if not os.path.exists(os.path.dirname(path)):
                try:
                    os.makedirs(os.path.dirname(path))
                except OSError:
                    self.send_error(HTTPStatus.NOT_FOUND, "Could not create dir")
                    return None
            try:
                f = open(path, 'wb')
            except OSError:
                self.send_error(HTTPStatus.NOT_FOUND, "Could not open file")
                return None
        try:
            content_length = int(self.headers['Content-Length'])
            f.write(self.rfile.read(content_length))
            self.send_response(HTTPStatus.OK)
            self.end_headers()
        finally:
            f.close()

server_address = ('', PORT)
httpd = HTTPServer(server_address, SimpleServer)

try:
    print("serving at port", PORT)
    httpd.serve_forever()

except KeyboardInterrupt:
    pass

print("stopping server")
httpd.server_close()
