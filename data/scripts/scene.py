import pygame, threading, json, random, time
from . import player, map, shadow_caster, hud, menu
from socket import AF_INET, socket, SOCK_STREAM


class MainScene:
    def __init__(self, map_path):
        self.colors = {
            'background': (125, 112, 113),
            'text': (223, 246, 245),
            'shadows': (48, 44, 46)
        }

        self.next_scene = None

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
    def __init__(self, port: int, path):
        MainScene.__init__(self, path)

        self.map_path = path
        self.message_splitter = ''.join(chr(random.randint(33, 126)) for _ in range(10))

        self.clients = {}
        self.addresses = {}
        self.player_dictionary = {}
        self.player_list = []

        self.ip = ''
        self.port = port
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
        self.player.update(self.player_list)

        for p in self.player_list:
            p.update()

        if len(self.player.damage_taken) > 0:
            damage_taken = self.player.get_damage_taken(0)
            for one_damage in damage_taken:
                enemy, bullet, damage, victim = one_damage
                self.player.hearts -= damage
                self.player_list[enemy].bullets.pop(bullet)
                one_damage[0] += 1

            self.broadcast(self.build_message({'damage': damage_taken}))

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

        info = {
            'map': self.map_path,
            'message_splitter': self.message_splitter,
            'own_index': client_index_whole_list,
            'players': [[self.player.center, self.player.rotation, self.player.active_weapon, self.player.frame]] + [[p.center, p.rotation, p.active_weapon, p.frame] for p in self.player_list]
        }

        info = json.dumps(info)
        client.send(bytes(info, 'utf8'))

        client_session_info = client.recv(self.buffer_size).decode('utf8')
        if client_session_info == 'ping':
            print(f'got ping request from {self.addresses[client]}')
            del self.addresses[client]
            return

        new_player = player.RemotePlayer(self.map)
        self.player_list.append(new_player)
        self.player_dictionary[client] = new_player

        self.clients[client] = client

        while True:
            try:
                msg = client.recv(self.buffer_size)
                if msg != bytes("{quit}", "utf8"):
                    decoded_message = msg.decode('utf8')
                    dict = decoded_message.split(self.message_splitter)[0]
                    client_info = json.loads(dict)

                    if 'player' in client_info:
                        new_player.set_center(client_info['player']['center'])
                        new_player.set_rotation(client_info['player']['rotation'])
                        new_player.set_image(client_info['player']['weapon'], client_info['player']['frame'])
                        for bullet in client_info['player']['bullets']:
                            new_player.add_bullet(*bullet, True)

                    if 'index' in client_info:
                        client_index_whole_list = client_info['index']
                        client_index = client_index_whole_list - 1

                    if 'damage' in client_info:
                        self.broadcast(dict)

                        for one_damage in client_info['damage']:
                            enemy, bullet, damage, victim = one_damage
                            if enemy == 0:
                                self.player.bullets.pop(bullet)
                            else:
                                self.player_list[enemy - 1].bullets.pop(bullet)

                            new_player.hearts -= damage

                else:
                    self.player_list.pop(client_index)
                    client.close()
                    del self.clients[client]
                    disconnection_info = {'disconnect': client_index_whole_list}
                    self.broadcast(self.build_message(disconnection_info))
                    print(f'{self.addresses[client]} disconnected')
                    break

            except json.JSONDecodeError as e:
                print(f'Error receiving data from {self.addresses[client]}:')
                #print(e)
                pass

            except OSError as e:
                print('connection failed')
                #print(e)
                self.player_list.pop(client_index)
                client.close()
                del self.clients[client]
                disconnection_info = {'disconnect': client_index_whole_list}
                self.broadcast(self.build_message(disconnection_info))
                print(f'{self.addresses[client]} lost connection')
                break

    def build_message(self, message: dict):
        return json.dumps(message) + self.message_splitter

    def broadcast(self, message: str):  # prefix is for name identification.
        message_bytes = bytes(message, 'utf8')
        try:
            for sock in self.clients:
                sock.send(message_bytes)

        except OSError as e:
            print('error broadcasting to one client')
            print(e)

        except RuntimeError as e:
            print('deleted client while broadcasting')
            print(e)

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

        self.connected = True

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
        self.player.update(self.player_list)

        for i, p in enumerate(self.player_list):
            if i != self.own_index:
                p.update()

        if len(self.player.damage_taken) > 0:
            self.send(self.build_message({'damage': self.player.get_damage_taken(self.own_index)}))

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

        if self.player.hearts <= 0:
            self.stop()
            quit()

    def receive(self):
        while self.connected:
            try:
                msg = self.client_socket.recv(self.buffer_size)
                decoded_message = msg.decode('utf8')
                dict = decoded_message.split(self.message_splitter)[0]
                if msg != bytes("{quit}", "utf8"):
                    info_from_server = json.loads(dict)

                    # update players
                    if 'players' in info_from_server:
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

                    # remove a player
                    if 'disconnect' in info_from_server:
                        index = info_from_server['disconnect']
                        self.player_list.pop(index)
                        if index < self.own_index:
                            self.own_index -= 1
                            index_info = {'index': self.own_index}
                            self.send(self.build_message(index_info))

                    # handle hit
                    if 'damage' in info_from_server:
                        for one_damage in info_from_server['damage']:
                            enemy, bullet, damage, victim = one_damage
                            if enemy == self.own_index:
                                self.player.bullets.pop(bullet)
                            else:
                                self.player_list[enemy].bullets.pop(bullet)

                            if victim == self.own_index:
                                self.player.hearts -= damage
                            else:
                                self.player_list[victim].hearts -= damage

            except json.JSONDecodeError as e:
                print('Error receiving data from server:')
                #print(e)
                pass

            except OSError:
                print('connection failed')
                break

    def send(self, message):
        self.client_socket.send(bytes(message, "utf8"))

    def send_info(self):
        if self.connected:
            info = {
                'player': {
                    'center': self.player.center,
                    'rotation': self.player.rotation,
                    'weapon': self.player.active_weapon,
                    'frame': self.player.frame,
                    'bullets': self.player.get_new_bullets()
                }
            }
            self.send(self.build_message(info))

    def build_message(self, message: dict):
        msg = json.dumps(message) + self.message_splitter
        return msg

    def stop(self):
        self.send('{quit}')
        self.client_socket.close()
        self.connected = False


class MenuScene:
    def __init__(self, menu):
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

        self.menu = menu

        self.next_scene = None


class MainMenuScene(MenuScene):
    def __init__(self):
        self.input_image = pygame.image.load('data/sprites/icons/menu_input.png')
        self.host_image = pygame.image.load('data/sprites/icons/menu_button_host.png')
        self.join_image = pygame.image.load('data/sprites/icons/menu_button_join.png')
        self.settings_image = pygame.image.load('data/sprites/icons/menu_button_settings.png')

        self.menu_content = [
            menu.Button('host', self.host_image.get_rect(), image=self.host_image),
            menu.Button('join', self.join_image.get_rect(), image=self.join_image),
            menu.Button('settings', self.settings_image.get_rect(), image=self.settings_image)
        ]

        self.host_clicked = 0
        self.join_clicked = 0

        self.menu = menu.Menu('center', (100, 50), 'MAIN MENU', self.menu_content)

        MenuScene.__init__(self, self.menu)

    def update(self, surface, input):
        self.render_surface.fill(self.colors['background'])

        self.handle_input(input)

        # update
        self.menu.update(input)

        self.handle_menu_actions()

        # render stuff
        self.menu.render(self.render_surface)

        surface.blit(self.render_surface, (0, 0))

    def handle_menu_actions(self):
        if self.menu.get_pressed('join'):
            if self.join_clicked == 1:
                threading.Thread(target=self.test_join).start()
            else:
                if self.host_clicked == 0:
                    self.menu.add_content(menu.Input('ip', self.input_image.get_rect(), image=self.input_image), 1)
                    self.menu.add_content(menu.Input('port', self.input_image.get_rect(), image=self.input_image), 2)
                else:
                    self.menu.add_content(menu.Input('ip', self.input_image.get_rect(), image=self.input_image), 2)
                    self.menu.add_content(menu.Input('port', self.input_image.get_rect(), image=self.input_image), 3)

            self.join_clicked += 1

        elif self.menu.get_pressed('host'):
            print(self.host_clicked)
            if self.host_clicked == 1:
                self.host_clicked += 1
                threading.Thread(target=self.test_host).start()
            else:
                self.host_clicked += 1
                self.menu.add_content(menu.Input('host port', self.input_image.get_rect(), image=self.input_image), 0)

    def test_host(self):
        try:
            test_address = ('', int(self.menu.get_text('host port')))
            test_server = socket(AF_INET, SOCK_STREAM)
            test_server.bind(test_address)
            test_server.listen()
            test_server.close()

        except ValueError as e:
            print('host port not an int')
            # print(e)
            self.host_clicked = 1

        except OSError as e:
            print('port not valid')
            # print(e)
            self.host_clicked = 1

        else:
            print('creating new session')
            self.next_scene = HostScene(int(self.menu.get_text('host port')), 'data/maps/map_1.csv')

    def test_join(self):
        try:
            test_address = (self.menu.get_text('ip'), int(self.menu.get_text('port')))
            test_socket = socket(AF_INET, SOCK_STREAM)
            test_socket.connect(test_address)
            session_info = test_socket.recv(1024)
            test_socket.send(bytes('ping', "utf8"))
            test_socket.close()

        except ValueError as e:
            print('port not an int')
            # print(e)
            self.join_clicked = 1

        except OSError as e:
            print('not a valid game session?')
            # print(e)
            self.join_clicked = 1

        else:
            print('found game session')
            self.next_scene = ClientScene(test_address)

    def handle_input(self, input):
        for event in input:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pass

    def stop(self):
        pass
