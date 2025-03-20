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
            self.socket.bind(('0.0.0.0', port))  # Explicit binding
            self.socket.listen(5)
            self.socket.settimeout(0.1)
            print(f"Web server started successfully on port {port}")
        except OSError as e:
            print(f"Failed to start web server: {e}")
            if port == 80:
                print("Trying alternative port 8080...")
                self.socket.close()
                self.__init__(8080)
            else:
                self.socket.close()
                raise
    
    def handle_requests(self, papers):
        """Handle incoming web requests"""
        try:
            # Check for new client connections
            try:
                conn, addr = self.socket.accept()
                print(f"Client connected from {addr[0]}")
                conn.settimeout(3.0)
                self._process_request(conn, papers)
                conn.close()
            except OSError:
                # Socket timeout, which is expected
                pass
                
        except Exception as e:
            raise
            print(f"Error handling request: {e}")
    
    def _process_request(self, conn, papers):
        """Process HTTP request"""
        try:
            # Receive request
            request = conn.recv(1024).decode()
            print(f"Received request: {request.split('\\r\\n')[0]}")
            print(f"Request: {request}")
            
            # Parse request to get path
            request_line = request.split('\r\n')[0]
            method, path, version = request_line.split(' ')
            print(f"Processing {method} request for {path}")
            
            # Serve requested content
            if path == '/':
                self._serve_index(conn, papers)
            elif path == '/papers':
                self._serve_papers(conn, papers)
            elif path == '/style.css':
                self._serve_css(conn)
            else:
                self._serve_404(conn)
                
        except Exception as e:
            raise
            print(f"Error processing request: {e}")
            self._serve_error(conn)
    
    def _serve_index(self, conn, papers):
        """Serve index page using template file"""
        try:
            # Read the index template
            with open('templates/index.html', 'r') as f:
                template = f.read()
            
            # Generate papers content
            if papers:
                papers_content = ""
                # Read the paper template
                with open('templates/paper_template.html', 'r') as f:
                    paper_template = f.read()
                    
                
                for paper in papers:
                    print(f"Paper: {paper}")
                    # Replace placeholders in the paper template
                    paper_html = paper_template
                    paper_html = paper_html.replace('{{title}}', paper['title'])
                    paper_html = paper_html.replace('{{summary}}', "AI summary: " + paper['summary'])
                    paper_html = paper_html.replace('{{published}}', paper['published'][:10])
                    paper_html = paper_html.replace('{{keyword}}', paper['keyword'])
                    paper_html = paper_html.replace('{{url}}', paper['url'])
                    papers_content += paper_html
            else:
                # Read the no papers template
                papers_content = "<p>No papers found.</p>"
            
            # Replace placeholders in the index template
            html = template
            html = html.replace('{{datetime}}', self._format_datetime())
            html = html.replace('{{papers_content}}', papers_content)
            
            self._send_response(conn, html)
            print("Served index page")
        except OSError as e:
            raise
            print(f"Error reading template files: {e}")
            self._serve_error(conn)
    
    def _serve_papers(self, conn, papers):
        """Serve papers as JSON"""
        import ujson
        content = ujson.dumps(papers)
        self._send_response(conn, content, content_type="application/json")
        print("Served papers as JSON")
    
    def _serve_css(self, conn):
        """Serve CSS file"""
        try:
            # Read the CSS file
            with open('templates/style.css', 'r') as f:
                css = f.read()
            self._send_response(conn, css, content_type="text/css")
            print("Served CSS")
        except OSError as e:
            print(f"Error reading CSS file: {e}")
            self._serve_error(conn)
    
    def _serve_404(self, conn):
        """Serve 404 page"""
        content = "<html><body><h1>404 Not Found</h1><p>The requested resource was not found.</p></body></html>"
        self._send_response(conn, content, status="404 Not Found")
        print("Served 404 page")
    
    def _serve_error(self, conn):
        """Serve error page"""
        content = "<html><body><h1>500 Internal Server Error</h1><p>An error occurred while processing your request.</p></body></html>"
        self._send_response(conn, content, status="500 Internal Server Error")
        print("Served error page")
    
    def _send_response(self, conn, content, status="200 OK", content_type="text/html"):
        """Send HTTP response"""
        response = f"HTTP/1.1 {status}\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += "Connection: close\r\n"
        response += f"Content-Length: {len(content)}\r\n"
        response += "\r\n"
        
        conn.send(response.encode())
        conn.send(content.encode() if isinstance(content, str) else content)
    
    def _format_datetime(self):
        """Create a simple datetime string for MicroPython"""
        year, month, day, hour, minute, second, _, _ = time.localtime()
        return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"