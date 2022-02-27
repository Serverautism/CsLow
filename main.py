import pygame
from data.scripts import player, map, shadow_caster


class Game:
    def __init__(self):
        pygame.init()

        self.fps = 120
        self.running = True

        self.colors = {
            'background': (125, 112, 113),
            'text': (223, 246, 245),
            'shadows': (48, 44, 46)
        }

        self.screen_width, self.screen_height = 1920, 1080
        self.screen_dimensions = (self.screen_width, self.screen_height)

        self.render_width, self.render_height = 1024, 576
        self.render_dimensions = (self.render_width, self.render_height)

        self.font = pygame.font.SysFont("Arial", 15)
        self.screen = pygame.display.set_mode(self.screen_dimensions)
        self.clock = pygame.time.Clock()
        self.render_surface = pygame.Surface(self.render_dimensions)

        self.map = map.Map('data/maps/map_1.csv')

        self.player = player.Player((512, 288), self.map)

        self.shadow_caster = shadow_caster.ShadowCaster(self.player, self.map, self.colors['shadows'])

    def run(self):
        while self.running:
            self.render_surface.fill(self.colors['background'])
            self.clock.tick(self.fps)

            self.handle_input()

            # update
            self.player.update()
            self.shadow_caster.update()

            # render
            self.shadow_caster.render(self.render_surface)
            self.map.draw(self.render_surface)
            self.player.render(self.render_surface)

            self.render_surface.blit(self.font.render('fps: ' + str(round(self.clock.get_fps(), 2)), True, self.colors['text']), (5, 5))
            self.render_surface.blit(self.font.render('rotation: ' + str(round(self.player.rotation, 2)), True, self.colors['text']), (80, 5))
            self.screen.blit(pygame.transform.scale(self.render_surface, self.screen_dimensions), (0, 0))
            pygame.display.update()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_1:
                    self.player.switch_weapon(1)
                elif event.key == pygame.K_2:
                    self.player.switch_weapon(2)
                elif event.key == pygame.K_3:
                    self.player.switch_weapon(3)

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


if __name__ == '__main__':
    app = Game()
    app.run()
