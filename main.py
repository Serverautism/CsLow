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

        self.screen_width, self.screen_height = 1024, 576
        self.screen_dimensions = (self.screen_width, self.screen_height)

        self.render_width, self.render_height = 1024, 576
        self.render_dimensions = (self.render_width, self.render_height)

        self.font = pygame.font.Font('data/font/font.ttf', 15)
        self.screen = pygame.display.set_mode(self.screen_dimensions)
        self.clock = pygame.time.Clock()
        self.render_surface = pygame.Surface(self.render_dimensions)

        self.input = []

        '''mode = input('Mode: ')
        if mode == '1':
            self.main_scene = scene.HostScene('data/maps/map_1.csv')
            self.active_scene = self.main_scene
        elif mode == '2':
            ip = input('IP: ')
            port = int(input('Port: '))
            self.main_scene = scene.ClientScene((ip, port))
            # self.main_scene = scene.ClientScene()
            self.active_scene = self.main_scene
        elif mode == '3':
            self.active_scene = scene.MainMenuScene()'''

        self.active_scene = scene.MainMenuScene()

    def run(self):
        while self.running:
            self.clock.tick(self.fps)

            self.handle_input()

            self.active_scene.update(self.render_surface, self.input)

            self.render_surface.blit(self.font.render('fps: ' + str(round(self.clock.get_fps(), 2)), True, self.colors['text']), (5, 5))
            self.screen.blit(pygame.transform.scale(self.render_surface, self.screen_dimensions), (0, 0))
            pygame.display.update()

            if self.active_scene.next_scene:
                self.active_scene = self.active_scene.next_scene
                if isinstance(self.active_scene, scene.MainMenuScene):
                    pygame.display.set_caption('CsLow: MainMenu')
                elif isinstance(self.active_scene, scene.ClientScene):
                    pygame.display.set_caption('CsLow: Client')
                elif isinstance(self.active_scene, scene.HostScene):
                    pygame.display.set_caption('CsLow: Host')

    def handle_input(self):
        self.input = pygame.event.get()
        for event in self.input:
            if event.type == pygame.QUIT:
                self.active_scene.stop()
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.active_scene.stop()
                    self.running = False


if __name__ == '__main__':
    app = Game()
    app.run()
