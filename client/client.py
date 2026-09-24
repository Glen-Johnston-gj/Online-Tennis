# pc_client.py
import socket

class Client:

    def __init__(self, Address : tuple[str, int] = ('127.0.0.0', 4000)):
        self.GameServerAddress = Address
        self.Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.OKAY = b'200'
        self.READY_UP = b'210'
        self.GAME_PLAY = b'250'
        self.NEW_PACK = b'230'
        self.UPDATE_PACK = b'235'
        self.SPAWN = b'800'

        self.HOST = b'700'
        self.GUEST = b'750'


        self.package = bytearray([
                0, 0, 0,                # Player Y
                0, 0, 0,                # Ball XY
                0, 0, 0,
                0, 0,                   # Ball SXY
                0, 0,
                0, 0,                   # Score
                0,                      # Ready
                0,                      # Winner
                0,                      # State
                0
            ])

    def Connect_To_Server(self, creds : str):
        self.Server.connect(self.GameServerAddress)
        self.Server.send(creds.encode("ascii"))
        status = self.Server.recv(16)
        print("Connecting to the server status:", status)
        return status

    def Ready_up(self, ready : bool):
        self.package = bytearray([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
        self.package[17:18] = (int(ready)).to_bytes(1)
        self.Server.send(self.package)

    def Recv_data(self):
        data = self.Server.recv(255)
        return data

    def send_data(self):
        self.Server.send(self.package)

    def make_package(self, playeY : int, ballpos : list[int, int], ballspeed : list[int, int], score : list[int, int], ready : bool, winner : int, state : bool):
        self.package = bytearray([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0])
        self.package[0:3] = playeY.to_bytes(3)
        self.package[3:6] = ballpos[0].to_bytes(3)
        self.package[6:9] = ballpos[1].to_bytes(3)
        self.package[9:12] = ballspeed[0].to_bytes(3, signed=True)
        self.package[12:15] = ballspeed[1].to_bytes(3, signed=True)
        self.package[15:16] = score[0].to_bytes(1)
        self.package[16:17] = score[1].to_bytes(1)
        self.package[17:18] = int(ready).to_bytes(1)
        self.package[18:19] = winner.to_bytes(1, signed=True)
        self.package[19:20] = int(state).to_bytes(1)

    def close(self):
        self.Server.close()
