import pygame, threading, json, random, logging
from . import player, map, shadow_caster, hud, menu
from socket import AF_INET, socket, SOCK_STREAM


logging.basicConfig(
    filename='data/logs/session.log',
    filemode='w',
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%d.%m.%y %H:%M:%S',
    level=logging.DEBUG
)


def log(message):
    logging.debug(f'{message}')


class MainScene:
    def __init__(self, map_path, team):
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

        self.player = player.Player((4 * 32, 3 * 32), self.map, team)

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
    def __init__(self, port: int, path, name, teams, own_team):
        MainScene.__init__(self, path, own_team)

        self.name = name
        self.teams = teams
        self.own_team = own_team

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
            'players': [[self.player.center, self.player.rotation, self.player.active_weapon, self.player.frame, self.player.get_new_bullets(), self.player.team, self.player.hearts]] + [[p.center, p.rotation, p.active_weapon, p.frame, p.get_new_bullets(), p.team, p.hearts] for p in self.player_list]
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
                log(f'{client_address[0]}:{client_address[1]} has connected')
                self.addresses[client] = client_address

                threading.Thread(target=self.handle_client, args=(client,)).start()
            except OSError:
                break

    def handle_client(self, client):
        client_index = len(self.player_list)
        client_index_whole_list = client_index + 1

        info = {
            'name': self.name,
            'teams': self.teams,
            'names': [n for n in self.clients.values()],
            'map': self.map_path,
            'message_splitter': self.message_splitter,
            'own_index': client_index_whole_list,
            'players': [[self.player.center, self.player.rotation, self.player.active_weapon, self.player.frame, self.player.team, self.player.hearts]] + [[p.center, p.rotation, p.active_weapon, p.frame, p.team, p.hearts] for p in self.player_list]
        }

        info = json.dumps(info)
        client.send(bytes(info, 'utf8'))

        client_session_info = client.recv(self.buffer_size).decode('utf8')

        if client_session_info == 'ping' or client_session_info == '':
            log(f'got ping request from {self.addresses[client]}')
            del self.addresses[client]
            client.close()
            return

        client_session_info = json.loads(client_session_info.split(self.message_splitter)[0])

        new_player = player.RemotePlayer(self.map, client_session_info['team'])
        self.player_list.append(new_player)
        self.player_dictionary[client] = new_player

        self.clients[client] = client_session_info['name']

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
                        log('got damage message fom player')
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
                    log(f'{self.addresses[client]} disconnected')
                    break

            except json.JSONDecodeError as e:
                log(f'Error receiving data from {self.addresses[client]}')
                log(dict)
                log(e)
                pass

            except OSError as e:
                log('connection failed')
                #log(e)
                self.player_list.pop(client_index)
                client.close()
                del self.clients[client]
                disconnection_info = {'disconnect': client_index_whole_list}
                self.broadcast(self.build_message(disconnection_info))
                log(f'{self.addresses[client]} lost connection')
                break

    def build_message(self, message: dict):
        return json.dumps(message) + self.message_splitter

    def broadcast(self, message: str):  # prefix is for name identification.
        message_bytes = bytes(message, 'utf8')
        try:
            for sock in self.clients:
                sock.send(message_bytes)

        except OSError as e:
            log('error broadcasting to one client')
            log(e)

        except RuntimeError as e:
            log('deleted client while broadcasting')
            log(e)

    def stop(self):
        for sock in self.clients:
            sock.close()
        self.server.close()


class ClientScene(MainScene):
    def __init__(self, server_info=('127.0.0.1', 33000), client_info=None):
        self.ip = server_info[0]
        self.port = server_info[1]

        if client_info is None:
            self.client_info = {
                'name': 'name',
                'team': 'team'
            }
        else:
            self.client_info = client_info

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

        MainScene.__init__(self, path, client_info['team'])

        self.player_list = []
        for i, p in enumerate(info['players']):
            if i != self.own_index:
                new_player = player.RemotePlayer(self.map, p[4])
                new_player.set_center(p[0])
                new_player.set_rotation(p[1])
                new_player.set_image(p[2], p[3])
                self.player_list.append(new_player)
            else:
                self.player_list.append(None)

        self.send(self.build_message(self.client_info))

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
                                new_player = player.RemotePlayer(self.map, p[5])
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
                        log('got damage message from server')
                        for one_damage in info_from_server['damage']:
                            log('containing damage')
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
                log('Error receiving data from server:')
                log(dict)
                log(e)
                pass

            except OSError:
                log('connection failed')
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

        self.host_port_error = False
        self.host_connect_error = False
        self.join_port_error = False
        self.join_connect_error = False

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
                self.join_clicked += 1
                threading.Thread(target=self.test_join).start()
            else:
                self.join_clicked += 1
                if self.host_clicked == 0:
                    self.menu.add_content(menu.Input('ip', self.input_image.get_rect(), image=self.input_image), 1)
                    self.menu.add_content(menu.Input('port', self.input_image.get_rect(), image=self.input_image), 2)
                else:
                    self.menu.add_content(menu.Input('ip', self.input_image.get_rect(), image=self.input_image), 2)
                    self.menu.add_content(menu.Input('port', self.input_image.get_rect(), image=self.input_image), 3)

        elif self.menu.get_pressed('host'):
            if self.host_clicked == 1:
                self.host_clicked += 1
                threading.Thread(target=self.test_host).start()
            else:
                self.host_clicked += 1
                self.menu.add_content(menu.Input('host port', self.input_image.get_rect(), image=self.input_image), 0)

    def test_host(self):
        try:
            test_address = ('', int(self.menu.get_text('host port').strip()))
            test_server = socket(AF_INET, SOCK_STREAM)
            test_server.bind(test_address)
            test_server.listen()
            test_server.close()

        except ValueError as e:
            log('host port not an int')
            # log(e)
            self.host_clicked = 1

            if self.host_connect_error:
                self.menu.remove_content('host connect warning')
                self.host_connect_error = False

            if not self.host_port_error:
                self.menu.add_content(menu.Text('host port warning', 'seems like the port is not a number', (169, 59, 59)))
                self.host_port_error = True

        except OSError as e:
            log('port not valid')
            # log(e)
            self.host_clicked = 1

            if self.host_port_error:
                self.menu.remove_content('host port warning')
                self.host_port_error = False

            if not self.host_connect_error:
                self.menu.add_content(menu.Text('host connect warning', 'seems like the port is already taken', (169, 59, 59)))
                self.host_connect_error = True

        else:
            log('creating new session')
            self.next_scene = CreateHostScene(int(self.menu.get_text('host port')))

    def test_join(self):
        try:
            test_address = (self.menu.get_text('ip').strip(), int(self.menu.get_text('port').strip()))
            test_socket = socket(AF_INET, SOCK_STREAM)
            test_socket.connect(test_address)
            session_info = json.loads(test_socket.recv(1024).decode('utf8'))
            test_socket.send(bytes('ping', "utf8"))
            test_socket.close()

        except ValueError as e:
            log('port not an int')
            # log(e)
            self.join_clicked = 1

            if self.join_connect_error:
                self.menu.remove_content('join connect warning')
                self.join_connect_error = False

            if not self.join_port_error:
                self.menu.add_content(menu.Text('join port warning', 'seems like the port is not a number', (169, 59, 59)))
                self.join_port_error = True

        except OSError as e:
            log('not a valid game session?')
            # log(e)
            self.join_clicked = 1

            if self.join_port_error:
                self.menu.remove_content('join port warning')
                self.join_port_error = False

            if not self.join_connect_error:
                self.menu.add_content(menu.Text('join connect warning', 'no such game session found', (169, 59, 59)))
                self.join_connect_error = True

        else:
            log('found game session')
            self.next_scene = CreateJoinScene(test_address, session_info)

    def handle_input(self, input):
        for event in input:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pass

    def stop(self):
        pass


class CreateHostScene(MenuScene):
    def __init__(self, port):
        self.port = port

        self.input_image = pygame.image.load('data/sprites/icons/menu_input.png')
        self.host_image = pygame.image.load('data/sprites/icons/menu_button_host.png')

        self.menu_content = [
            menu.Input('your player name', self.input_image.get_rect(), image=self.input_image),
            menu.Input('team name 1, team name 2', self.input_image.get_rect(), image=self.input_image),
            menu.Input('team you want to join', self.input_image.get_rect(), image=self.input_image),
            menu.Button('host', self.host_image.get_rect(), image=self.host_image)
        ]

        self.name_empty = False
        self.name_long = False
        self.teams_less = False
        self.teams_many = False
        self.team_not_in_teams = False
        self.team_same = False
        self.team_empty = False

        self.menu = menu.Menu('center', (100, 50), 'host new game ', self.menu_content)

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
        if self.menu.get_pressed('host'):
            name = self.menu.get_text('your player name').strip()
            teams = [t.strip() for t in self.menu.get_text('team name 1, team name 2').split(',')]
            own_team = self.menu.get_text('team you want to join').strip()

            log(teams)

            # name is empty or to long
            if name == '':
                if not self.name_empty:
                    self.menu.add_content(menu.Text('name empty', 'please enter you player name', (169, 59, 59)))
                    self.name_empty = True
            elif self.name_empty:
                self.menu.remove_content('name empty')
                self.name_empty = False

            if len(name) > 15:
                if not self.name_long:
                    self.menu.add_content(menu.Text('name long', 'your player name is to long (max: 15)', (169, 59, 59)))
                    self.name_long = True
            elif self.name_long:
                self.menu.remove_content('name long')
                self.name_long = False

            # not enough or to many teams etc.
            if len(teams) < 2:
                if not self.teams_less:
                    self.menu.add_content(menu.Text('teams less', 'please enter a least 2 teams', (169, 59, 59)))
                    self.teams_less = True
            elif self.teams_less:
                self.menu.remove_content('teams less')
                self.teams_less = False

            if len(teams) > 4:
                if not self.teams_many:
                    self.menu.add_content(menu.Text('teams many', 'please don´t enter more than 4 teams', (169, 59, 59)))
                    self.teams_many = True
            elif self.teams_many:
                self.menu.remove_content('teams many')
                self.teams_many = False

            if len(teams) != len(set(teams)):
                if not self.team_same:
                    self.menu.add_content(menu.Text('teams same', 'the teams should not have same names', (169, 59, 59)))
                    self.team_same = True
            elif self.team_same:
                self.menu.remove_content('teams same')
                self.team_same = False

            if '' in teams:
                if not self.team_empty:
                    self.menu.add_content(menu.Text('team empty', 'empty team names are not allowed', (169, 59, 59)))
                    self.team_empty = True
            elif self.team_empty:
                self.menu.remove_content('team empty')
                self.team_empty = False

            # own team not in list
            if own_team not in teams:
                if not self.team_not_in_teams:
                    self.menu.add_content(menu.Text('team not in teams', 'the team you try to join does not exist', (169, 59, 59)))
                    self.team_not_in_teams = True
            elif self.team_not_in_teams:
                self.menu.remove_content('team not in teams')
                self.team_not_in_teams = False

            # if everything is fine
            if not any([self.name_empty, self.name_long, self.teams_less, self.teams_many, self.team_not_in_teams, self.team_same]):
                self.next_scene = HostScene(self.port, 'data/maps/map_1.csv', name, teams, own_team)

    def handle_input(self, input):
        for event in input:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pass

    def stop(self):
        pass


class CreateJoinScene(MenuScene):
    def __init__(self, address, session_info):
        self.address = address
        self.session_info = session_info

        host_name = session_info['name']
        teams_string = 'teams: ' + ''.join([t + ', ' for t in session_info['teams']])[:-2]

        self.input_image = pygame.image.load('data/sprites/icons/menu_input.png')
        self.join_image = pygame.image.load('data/sprites/icons/menu_button_join.png')

        self.menu_content = [
            menu.Input('your player name', self.input_image.get_rect(), image=self.input_image),
            menu.Text('teams', teams_string, (223, 246, 245)),
            menu.Input('team you want to join', self.input_image.get_rect(), image=self.input_image),
            menu.Button('join', self.join_image.get_rect(), image=self.join_image)
        ]

        self.menu = menu.Menu('center', (100, 50), f'join {host_name}´s game', self.menu_content)

        self.name_empty = False
        self.name_long = False
        self.name_taken = False
        self.team_empty = False
        self.team_not_in_teams = False

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
            name = self.menu.get_text('your player name').strip()
            team = self.menu.get_text('team you want to join').strip()

            # error with the chosen name
            if name in self.session_info['names']:
                if not self.name_taken:
                    self.menu.add_content(menu.Text('name taken', 'the player name is already taken', (169, 59, 59)))
                    self.name_taken = True
            elif self.name_taken:
                self.menu.remove_content('name taken')
                self.name_taken = False

            if name == '':
                if not self.name_empty:
                    self.menu.add_content(menu.Text('name empty', 'please enter you player name', (169, 59, 59)))
                    self.name_empty = True
            elif self.name_empty:
                self.menu.remove_content('name empty')
                self.name_empty = False

            if len(name) > 15:
                if not self.name_long:
                    self.menu.add_content(menu.Text('name long', 'your player name is to long (max: 15)', (169, 59, 59)))
                    self.name_long = True
            elif self.name_long:
                self.menu.remove_content('name long')
                self.name_long = False

            # error with the chosen team
            if team == '':
                if not self.team_empty:
                    self.menu.add_content(menu.Text('team empty', 'please enter you player team', (169, 59, 59)))
                    self.team_empty = True
            elif self.team_empty:
                self.menu.remove_content('team empty')
                self.team_empty = False

            if team not in self.session_info['teams']:
                if not self.team_not_in_teams:
                    self.menu.add_content(menu.Text('team not in teams', 'the team you try to join does not exist', (169, 59, 59)))
                    self.team_not_in_teams = True
            elif self.team_not_in_teams:
                self.menu.remove_content('team not in teams')
                self.team_not_in_teams = False

            if not any([self.name_empty, self.name_long, self.name_taken, self.team_empty, self.team_not_in_teams]):
                client_info = {
                    'name': name,
                    'team': team
                }
                self.next_scene = ClientScene(self.address, client_info)

    def handle_input(self, input):
        for event in input:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pass

    def stop(self):
        pass
