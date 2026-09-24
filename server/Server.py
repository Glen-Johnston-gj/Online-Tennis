import socket
import _thread


class ClientConnection:
    def __init__(self, client : socket.socket, address = ("0.0.0.0", 0), message : bytes(255) = b'', client_active = False):
        self.client = client
        self.address = address
        self.message = message
        self.client_active = client_active

        self.response = b"200"
        self.error = b"404"

    def Make_connection(self, server : socket.socket, credentials = ""):
        server.listen()

        self.client, self.address = server.accept()
        self.client_active = True
        self.message = self.client.recv(1024).decode("ascii")

        if credentials == "":
            self.client.send(self.response)
            print(f"Accepted {self.address} without credentials")

        elif credentials == self.message[0:len(credentials)]:
            self.client.send(self.response)
            print(f"Accepted {self.address} with credentials")

        else:
            self.client_active = False
            
            self.client.send(self.error)
            self.client.close()
            
            self.address = None
            self.client = None

    def Get_message(self, target):
        self.message = self.client.recv(255)
        return

    def Send_message(self, Info : bytearray):
        self.client.send(Info)

    def Close_client(self):
        self.client.close()

class GameServer:
    
    def __init__(self, Server, Lobby_name: str = "", credentials : str = ""):


        self.__default_credentials = "NewLobbyPassword"
        self.__credentials = Lobby_name + credentials
        if Lobby_name == "" or credentials == "":
            self.__credentials = self.__default_credentials

        self.__Server = Server
        self.host : ClientConnection = ClientConnection(None)
        self.guest : ClientConnection = ClientConnection(None)

        self.host_POS : bytes = bytes([0,0,0])
        self.guest_POS: bytes = bytes([0,0,0])

        self.BALL_POSX : bytes = bytes([0,0,0])
        self.BALL_POSY : bytes = bytes([0,0,0])

        self.BALL_SPX : bytes = bytes([0,0])
        self.BALL_SPY : bytes = bytes([0,0])

        self.state : bytes = bytes([0])

        self.scoreH : bytes = bytes([0])
        self.scoreG : bytes = bytes([0])

        self.winner : bytes = bytes([255])

        self.game_in_play : bytes = bytes([0])
        self.host_ready = False
        self.guest_ready = False
        self.just_started_host = True
        self.just_started_guest = True

        self.HOST = b'700'
        self.GUEST = b'750'

        self.OKAY = b'200'
        self.READY_UP = b'210'
        self.GAME_PLAY = b'250'
        self.NEW_PACK = b'230'
        self.UPDATE_PACK = b'235'
        self.SPAWN = b'800'
        self.UPDATEBALL = b'850'
        
    def Make_host_package(self):
                
        package = bytearray(
        [
         0, 0, 0,               # Enemy Player Y
         0, 0, 0,               # Ball XY
         0, 0, 0,
         0, 0, 0,               # Ball SXY
         0, 0, 0,

         0,						# Score Host
         0, 					# Score Guest

         0,                     # Playing
         0,                     # Winner

         0,						# Ball State
         0
        ])


        package[0:3]   = self.guest_POS
        package[17:18] = int(self.host_ready and self.guest_ready).to_bytes(1)
        self.host.Send_message(package)
        return

    def Make_guest_package(self):               
        package = bytearray(
        [
         0, 0, 0,               # Enemy Player Y
         0, 0, 0,               # Ball XY
         0, 0, 0,
         0, 0, 0,               # Ball SXY
         0, 0, 0,

         0,						# Score Host
         0, 					# Score Guest

         0,                     # Playing
         0,                     # Winner

         0,						# Ball State
         0
        ])


        package[0:3]   = self.host_POS
        package[3:6]   = self.BALL_POSX
        package[6:9]   = self.BALL_POSY
        package[9:12]  = self.BALL_SPX
        package[12:15] = self.BALL_SPY
        package[15:16] = self.scoreH
        package[16:17] = self.scoreG
        package[17:18] = int(self.host_ready and self.guest_ready).to_bytes(1)
        package[18:19] = self.winner
        package[19:20] = self.state
        self.guest.Send_message(package)
        return

    
    def Wait_until_ready(self, what_client = "h") -> bool:
        if what_client == "h":
            self.host.Send_message(self.READY_UP)
            self.host.Get_message(19)

            if self.host.message[17:18] > bytes([0]):
                self.host_ready = True
 
        elif what_client == "g":
            self.guest.Send_message(self.READY_UP)
            self.guest.Get_message(19)

            if self.guest.message[17:18] > bytes([0]):
                self.guest_ready = True


    def Get_Update(self, what_client = "h"):
        if what_client == "h":
            self.host.Send_message(self.NEW_PACK)
            self.host.Get_message(19)

            self.host_POS = self.host.message[0:3]

            self.BALL_POSX = self.host.message[3:6] 
            self.BALL_POSY = self.host.message[6:9]
            self.BALL_SPX = self.host.message[9:12]
            self.BALL_SPY = self.host.message[12:15]

            self.scoreH = self.host.message[15:16]
            self.scoreG = self.host.message[16:17]
            self.winner = self.host.message[18:19]
            self.state = self.host.message[19:20]
        # If the ball expires
            if self.state == 0:
                self.game_in_play = 0
                self.host_ready = False
                self.guest_ready = False 

        elif what_client == "g":
            self.guest.Send_message(self.NEW_PACK)
            self.guest.Get_message(19)
            self.guest_POS = self.guest.message[0:3]


    def Update_clients(self, what_client = "h"):
        if what_client == "h":
            self.host.Send_message(self.UPDATE_PACK)
            status = self.host.client.recv(16)
            if status == b'200':
                self.Make_host_package()
            else: print("Updating client error in", what_client)

        elif what_client == "g":
            self.guest.Send_message(self.UPDATE_PACK)
            status = self.guest.client.recv(16)
            if status == b'200':
                self.Make_guest_package()
            else: print("Updating client error in", what_client)

    def guest_update_ball(self):
        self.guest.Send_message(self.UPDATEBALL)
        self.guest.Get_message(0)
        self.Make_guest_package()

    def Guest_thread(self):
        try:

            self.game_in_play = True
            while self.game_in_play:

                if self.host_ready and self.guest_ready:
                    if self.just_started_guest == True:
                        self.guest.Send_message(self.SPAWN)
                        self.guest.client.recv(16)
                    self.just_started_guest = False

                    self.Get_Update("g")
                    self.Update_clients("g")
                else:
                    self.guest_update_ball()
                    self.just_started_guest = True
                    self.Wait_until_ready("g")

            self.guest.Close_client()
        except Exception as e:
            print("ERROR in guest:", e)

    def Host_thread(self):
        try:

            self.game_in_play = True
            while self.game_in_play:
                if self.host_ready and self.guest_ready:
                    if self.just_started_host == True:
                        self.host.Send_message(self.SPAWN)
                        self.host.client.recv(16)    
                    self.just_started_host = False

                    self.Get_Update()
                    self.Update_clients()
                
                    if self.host.message[19:20] == bytes([0]):
                        print(list(self.host.message))
                        self.host_ready = False
                        self.guest_ready = False

                else:
                    self.just_started_host = True 
                    self.Wait_until_ready()

            self.host.Close_client()
        except Exception as e:
            print("ERROR: in host", e)

    def Idle_Server(self):

        # Server credentials check
        if self.__credentials == self.__default_credentials:
            print("This server is insecure, are you sure you want to continue?")
            continues = input("y/n >> ").lower()
            if continues == "n":
                return

        # Accept a connection with name and key as host
        print("Waiting for host...")
        self.host.response = self.HOST
        while self.host.client_active == False:
            self.host.Make_connection(self.__Server, self.__credentials)
        print("Host found at", self.host.address)
        self.host.response = self.OKAY

        # Accept second connection with name and key as guest
        print("Waiting for guest...")
        self.guest.response = self.GUEST
        while self.guest.client_active == False:
            self.guest.Make_connection(self.__Server, self.__credentials)
        print("Guest found at", self.guest.address)
        self.guest.response = self.OKAY

        # Lunch Server thread for guest
        _thread.start_new_thread(self.Guest_thread, ())
        self.Host_thread()
        return 
