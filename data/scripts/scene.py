import pygame
from . import player, map, shadow_caster, hud


class Scene:
    def update(self, surface, input):
        print('there was no overwrite for update')

    def handle_input(self, input):
        print('there was no overwrite for input')


class MainMenuScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.colors = {
            'background': (125, 112, 113),
            'text': (223, 246, 245),
            'shadows': (48, 44, 46)
        }

        self.screen_width, self.screen_height = 1920, 1080
        self.screen_dimensions = (self.screen_width, self.screen_height)

        self.render_width, self.render_height = 1024, 576
        self.render_dimensions = (self.render_width, self.render_height)

        self.font = pygame.font.Font('data/font/font.ttf', 15)
        self.render_surface = pygame.Surface(self.render_dimensions)


class MainScene(Scene):
    def __init__(self, map_path):
        Scene.__init__(self)

        self.colors = {
            'background': (125, 112, 113),
            'text': (223, 246, 245),
            'shadows': (48, 44, 46)
        }

        self.screen_width, self.screen_height = 1920, 1080
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
