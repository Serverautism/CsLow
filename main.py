import pygame
from data.scripts import scene


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

        self.font = pygame.font.Font('data/font/font.ttf', 15)
        self.screen = pygame.display.set_mode(self.screen_dimensions)
        self.clock = pygame.time.Clock()
        self.render_surface = pygame.Surface(self.render_dimensions)

        self.input = []

        self.main_scene = scene.MainScene('data/maps/map_1.csv')

    def run(self):
        while self.running:
            self.clock.tick(self.fps)

            self.handle_input()

            self.main_scene.update(self.render_surface, self.input)

            self.render_surface.blit(self.font.render('fps: ' + str(round(self.clock.get_fps(), 2)), True, self.colors['text']), (5, 5))
            self.screen.blit(pygame.transform.scale(self.render_surface, self.screen_dimensions), (0, 0))
            pygame.display.update()

    def handle_input(self):
        self.input = pygame.event.get()
        for event in self.input:
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False


if __name__ == '__main__':
    app = Game()
    app.run()
