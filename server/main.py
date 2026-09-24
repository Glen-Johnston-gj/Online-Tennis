import socket
import Server
import traceback
import json

with open("conf.json", "r") as f:
    file = json.load(f)

IP = file["IP"]
PORT = file["port"]
LOBBYNAME = file["lobby"]["name"]
LOBBYPW = file["lobby"]["password"]

binded_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
binded_socket.bind((IP, PORT))

server = Server.GameServer(binded_socket, LOBBYNAME, LOBBYPW)

try:
    server.Idle_Server()
except Exception as e:
    print("Exception triggered", e, "\n\n")
    traceback.print_exc()