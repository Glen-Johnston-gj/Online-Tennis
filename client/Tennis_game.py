import pygame as pg
import client
import _thread
import json

# Changing this will do nothing other then make the game look very bad and not work properly
RES = 640, 480

try:
    with open("conf.json", "r") as f:
        file = json.load(f)
        f.close()

    PLAYER_SPEED = file["paddle speed"]
    BALL_SPEED = file["ball speed"]
    PASSKEY_NAME = file["lobby"]["passkey name"]
    PASSKEY_PSW = file["lobby"]["passkey psw"]
    IP = file["IP"]
    PORT = file["port"]
except:
    print("Config is currupted or not found")


class player:
    def __init__(self, game, colour = (255, 255, 255), posXY = (0,0)):

        self.game = game

        self.posx, self.posy = posXY
        self.width = 10
        self.height = 100

        self.speed = PLAYER_SPEED

        self.colour = colour

    # Signals
        self.up = False
        self.down = False
 
    def update(self):
        if self.up:
            self.posy -= self.speed / self.game.delta_time
            if self.posy < 0:
                self.posy = 0
        if self.down:
            self.posy += self.speed / self.game.delta_time
            if self.posy + self.height > self.game.height:
                self.posy = self.game.height - self.height

    def draw(self):
        pg.draw.rect(self.game.screen, self.colour, (self.posx, self.posy, self.width, self.height))

class bot(player):
    def __init__(self, game, colour=(255, 255, 255), posXY = (0,0)):
        super().__init__(game, colour, posXY)

class Ball:
    def __init__(self, game):
        self.game = game
        self.state = False
        self.posx, self.posy = [self.game.width / 2 - 5, self.game.width / 2 - 5]
        self.width, self.height = 10, 10

        self.movementX, self.movementY = [0,0]
        self.speedX = BALL_SPEED

        self.winner = -1

    def check_paddles(self, XY, WH):
        # If the left is less then or equal
        # and the right is more then or equal
        if (XY[0] <= self.posx or \
            XY[0] <= self.posx + self.width) \
        and XY[0] + WH[0] >= self.posx:

            # If the top is less then or equal
            # and the bottom is more then or equal
            if (XY[1] <= self.posy or XY[1] <= self.posy + self.height) and XY[1] + WH[1] >= self.posy:

                self.movementX *= -1
                self.movementY = (self.posy + self.height) - XY[1] - (XY[1] + WH[1] - self.posy)

    def update(self):
        if self.state:
            self.posx += self.movementX / self.game.delta_time
            self.posy += self.movementY / self.game.delta_time

            # The bot wins
            if self.posx - self.width < 0:
                self.winner = -1
                self.state = False

                if self.game.host:
                    self.game.ready_up = False

                if self.game.host:
                    self.game.score[1] += 1
                else:
                    self.game.score[0] += 1

            # Player wins
            elif self.posx + self.width > self.game.width:
                self.winner = 1
                self.state = False

                if self.game.host:
                    self.game.ready_up = False

                if self.game.host:
                    self.game.score[0] += 1
                else:
                    self.game.score[1] += 1

            # if it hits the top of the screen bounce down
            if self.posy < 0:
                self.posy = 0
                self.movementY *= -1
            # If it hits the bottom of the screen bounce up
            elif self.posy + self.height > self.game.height:
                self.posy = self.game.height - self.height
                self.movementY *= -1

    def draw(self):
        if self.state:
            pg.draw.rect(self.game.screen, (250, 250, 250), (self.posx, self.posy, self.width, self.height))

    def spawn(self):
        self.posx = self.game.width / 2 - 5
        self.posy = self.game.height / 2 - 5
        self.state = True
        self.movementX = self.speedX * self.winner
        self.movementY = 0

class Game:
    def __init__(self):
        pg.init()
        self.key = PASSKEY_NAME + PASSKEY_PSW
        self.IP = IP
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.width = RES[0]
        self.height = RES[1]

        self.delta_time = 0.1
        self.running = False

        self.colour = (255, 255, 255)

        self.player = player(self, self.colour, (20, 200))
        self.bot_player = bot(self, self.colour, (610, 100))
        self.ball = Ball(self)
        self.client = client.Client((IP, PORT))

        self.font = pg.font.SysFont("Arial", 32, True, False)

        self.score = [0,0]

        self.in_game = False
        self.host = False
        self.ready_up = False

        self.just_in_game = False
        self.game_in_play = False

        self.mouseXY = 0,0
        self.clicked = False
        self.justclicked = False

        self.join_surface = self.font.render("Join", True, (255, 255, 255))
        self.ready_surface = self.font.render("Space to ready up", True, (255, 255, 255))

    def join_game(self):
        self.client.GameServerAddress = (self.IP, self.client.GameServerAddress[1])
        host = self.client.Connect_To_Server(self.key)
        self.in_game = True

        if host != self.client.HOST:
            self.host = False
            self.player.posx = 610
            self.bot_player.posx = 20

        else: self.host = True

        _thread.start_new_thread(self.server_loop, ())

    def disconnect(self):
        self.client.OKAY = b'600'
        self.client.Server.recv(6)

    def handle_data(self, data : bytearray):
        if self.host:
            self.bot_player.posy = int(self.bot_player.posy).from_bytes(data[0:3])
        else:
            self.bot_player.posy = int(self.bot_player.posy).from_bytes(data[0:3])
            self.ball.posx = int(self.ball.posx).from_bytes(data[3:6])
            self.ball.posy = int(self.ball.posy).from_bytes(data[6:9])
            self.ball.movementX = int(self.ball.movementX).from_bytes(data[9:12], signed=True)
            self.ball.movementY = int(self.ball.movementY).from_bytes(data[12:15], signed=True)
            self.ball.winner = int(self.ball.winner).from_bytes(data[18:19], signed=True)

    def server_loop(self):
        while self.in_game:
            server_need = self.client.Server.recv(255)

            if server_need == self.client.READY_UP:
                self.client.Ready_up(self.ready_up)

            elif server_need == b'850':
                self.client.Server.send(b'200')
                data = self.client.Server.recv(32)
                self.ball.state = False
                if self.ready_up == True:
                    self.ready_up = False
                self.score[0] = self.score[0].from_bytes(data[15:16])
                self.score[1] = self.score[1].from_bytes(data[16:17])

            elif server_need == self.client.SPAWN:
                self.game_in_play = True
                self.in_game = True
                self.player.posy = self.height / 2 - (self.player.height / 2)
                self.bot_player.posy = self.height / 2 - (self.bot_player.height / 2)
                self.ball.spawn()
                self.client.Server.send(b'200')

            elif server_need == self.client.NEW_PACK:
                if not self.host: self.ball.state = True
                self.client.make_package(int(round(self.player.posy, 0)), (int(round(self.ball.posx, 0)), int(round(self.ball.posy, 2))), (int(round(self.ball.movementX, 0)), int(round(self.ball.movementY, 0))), self.score, self.ready_up, self.ball.winner, self.ball.state)
                self.client.send_data()

            elif server_need == self.client.UPDATE_PACK:
                if not self.host: self.ball.state = True
                self.client.Server.send(b'200')
                data = self.client.Recv_data()
                self.handle_data(data)

            else:
                print("fail", server_need)

    def lobby_UI(self):
        POSX = self.width / 2 - 75
        POSY = self.height / 2 - 25
        pg.draw.rect(self.screen, (100, 200, 100), (POSX, POSY, 150, 50))
        self.screen.blit(self.join_surface, (self.width / 2 - (self.join_surface.get_width() / 2), self.height / 2 - (self.join_surface.get_height() / 2)))
        if self.mouseXY[0] >= POSX and self.mouseXY[0] <= POSX + 150:
            if self.mouseXY[1] >= POSY and self.mouseXY[1] <= POSY + 50:
                if self.justclicked:
                    pg.draw.rect(self.screen, (200, 200, 200), (POSX, POSY, 150, 50))
                    self.screen.blit(self.join_surface, (self.width / 2 - (self.join_surface.get_width() / 2), self.height / 2 - (self.join_surface.get_height() / 2)))
                    self.join_game()

    def events(self):
        self.justclicked = False
        self.mouseXY = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                # self.disconnect()

            if event.type == pg.MOUSEBUTTONDOWN:
                self.justclicked = True
                self.clicked = True
            if event.type == pg.MOUSEBUTTONUP:
                self.clicked = True

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_w:
                    self.player.up = True
                elif event.key == pg.K_s:
                    self.player.down = True
                elif event.key == pg.K_SPACE:
                    # ready up
                    self.ready_up = True

            elif event.type == pg.KEYUP:
                if event.key == pg.K_w:
                    self.player.up = False
                elif event.key == pg.K_s:
                    self.player.down = False

    def update(self):
        self.clock.tick(60)
        self.delta_time = self.clock.get_fps()

        self.events()

        if not self.in_game:
            self.lobby_UI()

        elif not self.ready_up:
            self.screen.blit(self.ready_surface, (self.width / 2 - (self.ready_surface.get_width() / 2), self.height / 2 - (self.ready_surface.get_height() / 2)))

        self.player.update()
        self.bot_player.update()

        self.ball.check_paddles((self.player.posx, self.player.posy), (self.player.width, self.player.height))
        self.ball.check_paddles((self.bot_player.posx, self.bot_player.posy), (self.bot_player.width, self.bot_player.height))
        self.ball.update()

    def render_UI(self):
        # Render the Score text
        self.screen.blit(self.font.render(str(self.score[0]), True, (180, 180, 180)), (200, 60))
        self.screen.blit(self.font.render(str(self.score[1]), True, (180, 180, 180)), (400, 60))

        # Render the gray score lines and middle line
        pg.draw.rect(self.screen, (180, 180, 180), \
        (self.width / 2 - 5, 0, 10, 480))
        pg.draw.rect(self.screen, (180, 180, 180), \
        (5, 0, 10, 480))
        pg.draw.rect(self.screen, (180, 180, 180), \
        (625, 0, 10, 480))

    def draw(self):
        pg.display.flip()
        self.screen.fill((20, 20, 20))
        self.render_UI()

        self.player.draw()
        self.bot_player.draw()
        self.ball.draw()

    def run(self):
        self.running = True
        while self.running:
            self.update()
            self.draw()
        pg.quit()


game = Game()
game.run()
input("end >>")
