from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class SudokuHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.p2p_server = kwargs.pop('p2p_server', None)
        super().__init__(*args, **kwargs)

    @staticmethod
    def validate_sudoku_grid(sudoku_grid):
        if len(sudoku_grid) != 9:
            raise ValueError("Invalid grid size")
        for row in sudoku_grid:
            if len(row) != 9:
                raise ValueError("Invalid grid size")
            for cell in row:
                if cell not in range(10):
                    raise ValueError("Invalid cell value")

    def do_POST(self):
        if self.path == "/solve":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            try:
                sudoku_grid = data["sudoku"]
                self.validate_sudoku_grid(sudoku_grid)
            except (ValueError, KeyError) as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode())
                return

            print("Received Sudoku grid for solving")
            response = self.p2p_server.distribute_sudoku_task(sudoku_grid)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

    def get_stats(self):
        stats = {
            "all": {
                "solved": self.p2p_server.solved_puzzles,
                "validations": self.p2p_server.total_validations
            },
            "nodes": [
                {"address": address, "validations": validations}
                for address, validations in self.p2p_server.node_validations.items()
            ]
        }
        return stats

    def get_network(self):
        network = {self.p2p_server.node_id: [f"{host}:{port}" for host, port in self.p2p_server.known_nodes]}
        return network

    def do_GET(self):
        if self.path == '/stats':
            stats = self.get_stats()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode('utf-8'))

        elif self.path == '/network':
            network = self.get_network()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(network).encode('utf-8'))

        elif self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Hello, world!")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Resource not found")


def run_http_server(port, p2p_server):
    handler = lambda *args, **kwargs: SudokuHTTPRequestHandler(*args, p2p_server=p2p_server, **kwargs)
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    httpd.serve_forever()
