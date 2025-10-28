import http.server
import ssl
import os
import socketserver
import mimetypes

PORT = 8008 # 使用一个新端口以确保没有冲突
CERT_FILE = 'server.pem'
KEY_FILE = 'server.key'

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.translate_path(self.path)
        
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                self.send_response(301)
                self.send_header('Location', self.path + '/')
                self.end_headers()
                return
            
            for index in "index.html", "index.htm":
                index_path = os.path.join(path, index)
                if os.path.exists(index_path):
                    path = index_path
                    break
            else:
                return self.list_directory(path)

        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None:
            ctype = 'application/octet-stream'

        try:
            with open(path, 'rb') as f:
                self.send_response(200)
                if ctype.startswith('text/'):
                    self.send_header("Content-type", ctype + '; charset=utf-8')
                else:
                    self.send_header("Content-type", ctype)
                
                fs = os.fstat(f.fileno())
                self.send_header("Content-Length", str(fs[6]))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(404, "File not found")
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()

if __name__ == "__main__":
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print("证书或私钥文件不存在。请先生成它们。")
        print(f"可以使用以下命令生成自签名证书和私钥：")
        print(f"openssl req -new -x509 -keyout {KEY_FILE} -out {CERT_FILE} -days 365 -nodes")
        exit(1)

    Handler = SimpleHTTPRequestHandler
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        print(f"在端口 {PORT} 上启动 HTTPS 服务器...")
        print(f"请访问 https://localhost:{PORT} 或 https://您的IP地址:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止。")
            httpd.server_close()
