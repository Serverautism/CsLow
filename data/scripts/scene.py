import pygame, threading, json, random, time
from . import player, map, shadow_caster, hud
from socket import AF_INET, socket, SOCK_STREAM


class MainScene:
    def __init__(self, map_path):
        self.colors = {
            'background': (125, 112, 113),
            'text': (223, 246, 245),
            'shadows': (48, 44, 46)
        }

        self.screen_width, self.screen_height = 1024, 576
        self.screen_dimensions = (self.screen_width, self.screen_height)

        self.render_width, self.render_height = 1024, 576
        self.render_dimensions = (self.render_width, self.render_height)

        self.font = pygame.font.Font('data/font/font.ttf', 15)
        self.render_surface = pygame.Surface(self.render_dimensions)

        self.map = map.Map(map_path)

        self.player = player.Player((4 * 32, 3 * 32), self.map)

        self.shadow_caster = shadow_caster.ShadowCaster(self.player, self.map, self.colors['shadows'])

        self.hud = hud.Hud(self.player)

    def update(self, surface, input):
        self.render_surface.fill(self.colors['background'])

        self.handle_input(input)

        # update
        self.player.update()
        self.shadow_caster.update()
        self.hud.update()

        # render
        self.shadow_caster.render(self.render_surface)
        self.map.draw(self.render_surface)
        self.player.render(self.render_surface)
        self.hud.render(self.render_surface)

        self.render_surface.blit(self.font.render('rotation: ' + str(round(self.player.rotation, 2)), True, self.colors['text']), (85, 5))

        surface.blit(self.render_surface, (0, 0))

    def handle_input(self, input):
        for event in input:
            if event.type == pygame.QUIT:
                pass

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pass
                elif event.key == pygame.K_1:
                    self.player.switch_weapon(1)
                elif event.key == pygame.K_2:
                    self.player.switch_weapon(2)
                elif event.key == pygame.K_3:
                    self.player.switch_weapon(3)
                elif event.key == pygame.K_r:
                    self.player.reload()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.player.attack(True)
                elif event.button == 4:
                    self.player.switch_weapon(-1)
                elif event.button == 5:
                    self.player.switch_weapon(-2)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.player.go_left()
        if keys[pygame.K_d]:
            self.player.go_right()
        if keys[pygame.K_s]:
            self.player.go_down()
        if keys[pygame.K_w]:
            self.player.go_up()
        if (keys[pygame.K_a] and keys[pygame.K_d]) or (not keys[pygame.K_a] and not keys[pygame.K_d]):
            self.player.stop_x()
        if (keys[pygame.K_w] and keys[pygame.K_s]) or (not keys[pygame.K_w] and not keys[pygame.K_s]):
            self.player.stop_y()

        mouse_keys = pygame.mouse.get_pressed()
        if mouse_keys[0]:
            self.player.attack()


class HostScene(MainScene):
    def __init__(self, path):
        MainScene.__init__(self, path)

        self.map_path = path
        self.message_splitter = ''.join(chr(random.randint(33, 126)) for _ in range(10))

        self.clients = {}
        self.addresses = {}
        self.player_dictionary = {}
        self.player_list = []

        self.ip = ''
        self.port = 33000
        self.buffer_size = 1024
        self.address = (self.ip, self.port)

        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind(self.address)

        self.server.listen()

        self.accept_thread = threading.Thread(target=self.accept_new_connections)
        self.accept_thread.start()

    def update(self, surface, input):
        self.render_surface.fill(self.colors['background'])

        self.handle_input(input)

        # update
        self.player.update()

        for p in self.player_list:
            p.update()

        self.shadow_caster.update()
        self.hud.update()

        info = {
            'players': [[self.player.center, self.player.rotation, self.player.active_weapon, self.player.frame, self.player.get_new_bullets()]] + [[p.center, p.rotation, p.active_weapon, p.frame, p.get_new_bullets()] for p in self.player_list]
        }
        self.broadcast(self.build_message(info))

        # render
        for p in self.player_list:
            p.render(self.render_surface)

        self.shadow_caster.render(self.render_surface)
        self.map.draw(self.render_surface)
        self.player.render(self.render_surface)
        self.hud.render(self.render_surface)

        self.render_surface.blit(self.font.render('rotation: ' + str(round(self.player.rotation, 2)), True, self.colors['text']), (85, 5))

        surface.blit(self.render_surface, (0, 0))

    def accept_new_connections(self):
        while True:
            try:
                client, client_address = self.server.accept()
                print(f'{client_address[0]}:{client_address[1]} has connected')
                self.addresses[client] = client_address
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except OSError:
                break

    def handle_client(self, client):
        client_index = len(self.player_list)
        client_index_whole_list = client_index + 1
        new_player = player.RemotePlayer(self.map)
        self.player_list.append(new_player)
        self.player_dictionary[client] = new_player

        info = {
            'map': self.map_path,
            'message_splitter': self.message_splitter,
            'own_index': client_index_whole_list,
            'players': [[self.player.center, self.player.rotation, self.player.active_weapon, self.player.frame]] + [[p.center, p.rotation, p.active_weapon, p.frame] for p in self.player_list]
        }

        info = json.dumps(info)
        client.send(bytes(info, 'utf8'))

        name = client.recv(self.buffer_size).decode("utf8")
        self.clients[client] = name

        while True:
            try:
                msg = client.recv(self.buffer_size)
                decoded_message = msg.decode('utf8')
                dict = decoded_message.split(self.message_splitter)[0]
                if msg != bytes("{quit}", "utf8"):
                    client_info = json.loads(dict)
                    new_player.set_center(client_info['center'])
                    new_player.set_rotation(client_info['rotation'])
                    new_player.set_image(client_info['weapon'], client_info['frame'])
                    for bullet in client_info['bullets']:
                        new_player.add_bullet(*bullet, True)
                else:
                    client.send(bytes("{quit}", "utf8"))
                    client.close()
                    del self.clients[client]
                    break
            except json.JSONDecodeError as e:
                print(f'Error receiving data from {self.addresses[client]}:')
                print(e)

    def build_message(self, message: dict):
        return json.dumps(message) + self.message_splitter

    def broadcast(self, message: str):  # prefix is for name identification.
        message_bytes = bytes(message, 'utf8')
        for sock in self.clients:
            sock.send(message_bytes)

    def stop(self):
        for sock in self.clients:
            sock.close()
        self.server.close()


class ClientScene(MainScene):
    def __init__(self, server_info=('127.0.0.1', 33000)):
        self.ip = server_info[0]
        self.port = server_info[1]

        self.buffer_size = 1024
        self.address = (self.ip, self.port)

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(self.address)

        info = self.client_socket.recv(self.buffer_size).decode("utf8")
        info = json.loads(info)

        path = info['map']
        self.message_splitter = info['message_splitter']
        self.own_index = info['own_index']

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

        MainScene.__init__(self, path)

        self.player_list = []
        for i, p in enumerate(info['players']):
            if i != self.own_index:
                new_player = player.RemotePlayer(self.map)
                new_player.set_center(p[0])
                new_player.set_rotation(p[1])
                new_player.set_image(p[2], p[3])
                self.player_list.append(new_player)
            else:
                self.player_list.append(None)

    def update(self, surface, input):
        self.render_surface.fill(self.colors['background'])

        self.handle_input(input)

        # update
        self.player.update()

        for i, p in enumerate(self.player_list):
            if i != self.own_index:
                p.update()

        self.shadow_caster.update()
        self.hud.update()

        self.send_info()

        # render
        for i, p in enumerate(self.player_list):
            if i != self.own_index:
                p.render(self.render_surface)

        self.shadow_caster.render(self.render_surface)
        self.map.draw(self.render_surface)
        self.player.render(self.render_surface)
        self.hud.render(self.render_surface)

        self.render_surface.blit(self.font.render('rotation: ' + str(round(self.player.rotation, 2)), True, self.colors['text']), (85, 5))

        surface.blit(self.render_surface, (0, 0))

    def receive(self):
        while True:
            try:
                msg = self.client_socket.recv(self.buffer_size)
                decoded_message = msg.decode('utf8')
                dict = decoded_message.split(self.message_splitter)[0]
                if msg != bytes("{quit}", "utf8"):
                    info_from_server = json.loads(dict)

                    # update players
                    players = info_from_server['players']
                    for i, p in enumerate(players):
                        if i >= len(self.player_list):
                            new_player = player.RemotePlayer(self.map)
                            new_player.set_center(p[0])
                            new_player.set_rotation(p[1])
                            new_player.set_image(p[2], p[3])
                            for b in p[4]:
                                new_player.add_bullet(*b)
                            self.player_list.append(new_player)
                        elif i != self.own_index:
                            self.player_list[i].set_center(p[0])
                            self.player_list[i].set_rotation(p[1])
                            self.player_list[i].set_image(p[2], p[3])
                            for b in p[4]:
                                self.player_list[i].add_bullet(*b)
            except json.JSONDecodeError as e:
                print('Error receiving data from server:')
                print(e)

            except OSError:
                break

    def send(self, message):
        self.client_socket.send(bytes(message, "utf8"))

    def send_info(self):
        info = {
            'center': self.player.center,
            'rotation': self.player.rotation,
            'weapon': self.player.active_weapon,
            'frame': self.player.frame,
            'bullets': self.player.get_new_bullets()
        }
        self.send(self.build_message(info))

    def build_message(self, message: dict):
        msg = json.dumps(message) + self.message_splitter
        return msg

    def stop(self):
        self.send('{quit}')
        self.client_socket.close()
