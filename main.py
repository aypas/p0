# import blessed

# term = blessed.Terminal()

from sockets.server import run_server

run_server(("127.0.0.1", 8080), testing=False)