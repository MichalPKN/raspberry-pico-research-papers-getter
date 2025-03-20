import socket
import time
import os

class WebServer:
    def __init__(self, port=80):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            print(f"Starting server...")
            self.socket.bind(('0.0.0.0', port)) 
            self.socket.listen(5)
            self.socket.settimeout(0.1)
            print(f"Web server started successfully on port {port}")
        except OSError as e:
            print(f"Failed to start web server: {e}")
            print("Trying alternative port 8080...")
            self.socket.close()
            self.__init__(8080)
    
    def handle_requests(self, papers):
        try:
            conn, addr = self.socket.accept()
            print(f"Client connected from {addr[0]}")
            conn.settimeout(3.0)
            self._process_request(conn, papers)
            conn.close()
        except OSError:
            # Socket timeout, expected
            pass
    
    def _process_request(self, conn, papers):
        try:
            request = conn.recv(1024).decode()
            print(f"Received request: {request.split('\\r\\n')[0]}")
            print(f"Request: {request}")
            
            request_line = request.split('\r\n')[0]
            method, path, version = request_line.split(' ')
            print(f"Processing {method} request for {path}")
            
            if path == '/':
                self._serve_index(conn, papers)
            elif path == '/papers':
                self._serve_papers(conn, papers)
            elif path == '/style.css':
                self._serve_css(conn)
            else:
                self._serve_404(conn)
                
        except Exception as e:
            print(f"Error processing request: {e}")
            self._serve_error(conn)
    
    def _serve_index(self, conn, papers):
        try:
            with open('templates/index.html', 'r') as f:
                template = f.read()
            if papers:
                papers_content = ""
                with open('templates/paper_template.html', 'r') as f:
                    paper_template = f.read()
                
                for paper in papers:
                    print(f"Paper: {paper}")
                    paper_html = paper_template
                    paper_html = paper_html.replace('{{title}}', paper['title'])
                    paper_html = paper_html.replace('{{summary}}', "AI summary: " + paper['summary'])
                    paper_html = paper_html.replace('{{published}}', paper['published'][:10])
                    paper_html = paper_html.replace('{{keyword}}', paper['keyword'])
                    paper_html = paper_html.replace('{{url}}', paper['url'])
                    papers_content += paper_html
            else:
                papers_content = "<p>No papers found.</p>"
            
            html = template
            html = html.replace('{{papers_content}}', papers_content)
            
            self._send_response(conn, html)
            print("Served index page")
        except OSError as e:
            print(f"Error reading template files: {e}")
            self._serve_error(conn)
    
    def _serve_papers(self, conn, papers):
        import ujson
        content = ujson.dumps(papers)
        self._send_response(conn, content, content_type="application/json")
        print("Served papers as JSON")
    
    def _serve_css(self, conn):
        try:
            with open('templates/style.css', 'r') as f:
                css = f.read()
            self._send_response(conn, css, content_type="text/css")
            print("Served CSS")
        except OSError as e:
            print(f"Error reading CSS file: {e}")
            self._serve_error(conn)
    
    def _serve_404(self, conn):
        content = "<html><body><h1>404 Not Found</h1><p>The requested resource was not found.</p></body></html>"
        self._send_response(conn, content, status="404 Not Found")
        print("Served 404 page")
    
    def _serve_error(self, conn):
        content = "<html><body><h1>500 Internal Server Error</h1><p>An error occurred while processing your request.</p></body></html>"
        self._send_response(conn, content, status="500 Internal Server Error")
        print("Served error page")
    
    def _send_response(self, conn, content, status="200 OK", content_type="text/html"):
        response = f"HTTP/1.1 {status}\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += "Connection: close\r\n"
        response += f"Content-Length: {len(content)}\r\n"
        response += "\r\n"
        
        conn.send(response.encode())
        conn.send(content.encode() if isinstance(content, str) else content)