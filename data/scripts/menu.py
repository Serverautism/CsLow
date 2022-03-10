import pygame


class Button:
    def __init__(self, title, rect: pygame.Rect, image=None, color=None):
        self.title = title
        self.rect = rect
        self.image = image
        self.color = color

        self.colors = {
            'black': (0, 0, 0),
            'text': (223, 246, 245)
        }

        self.font = pygame.font.Font('data/font/font.ttf', 20)

        if not self.image:
            self.image = pygame.Surface((self.rect.width, self.rect.height))
            self.image.set_colorkey(self.colors['black'])

            self.image.fill(self.color)

            self.image.blit(self.font.render(self.title, True, self.colors['text']), (0, 0))

        self.pressed = False

    def update(self, mouse_press=None):
        if mouse_press:
            if self.rect.collidepoint(mouse_press):
                self.pressed = True
                return True

        self.pressed = False
        return False

    def render(self, surface):
        surface.blit(self.image, self.rect)

    def get_pressed(self):
        return self.pressed


class Input:
    def __init__(self, title, rect: pygame.Rect, image=None, color=None):
        self.title = title
        self.rect = rect
        self.image = image
        self.color = color

        self.active = False
        self.text = ''

        self.colors = {
            'black': (0, 0, 0),
            'text_preset': (223, 246, 245),
            'text': (48, 44, 46)
        }

        self.font = pygame.font.Font('data/font/font.ttf', 20)

        self.render_surface = pygame.Surface((self.rect.width, self.rect.height))
        self.render_surface.set_colorkey(self.colors['black'])

        self.pre_render()

    def update(self, mouse_press=None):
        if mouse_press:
            if self.rect.collidepoint(mouse_press):
                self.active = True
            else:
                self.active = False

    def handle_input(self, input):
        if self.active:
            got_input = False
            for event in input:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        if self.text != '':
                            self.text = self.text[:-1]
                            got_input = True
                    elif event.key == pygame.K_RETURN:
                        self.active = False
                    else:
                        self.text += event.unicode
                        got_input = True

            if got_input:
                self.pre_render()

    def render(self, surface):
        surface.blit(self.render_surface, self.rect)

    def pre_render(self):
        image_x = self.rect.width / 2 - self.image.get_width() / 2
        image_y = self.rect.height / 2 - self.image.get_height() / 2
        self.render_surface.blit(self.image, (image_x, image_y))

        if self.text != '':
            text_render = self.font.render(self.text, True, self.colors['text'])
            text_x = 10
            text_y = self.rect.height / 2 - text_render.get_height() / 2
        else:
            text_render = self.font.render(self.title, True, self.colors['text_preset'])
            text_x = 10
            text_y = self.rect.height / 2 - text_render.get_height() / 2

        self.render_surface.blit(text_render, (text_x, text_y))

    def get_text(self):
        return self.text


class Menu:
    def __init__(self, alignment=None, position=(0, 0), title='', content=None):
        self.title = title
        if content is None:
            content = []
        self.content = content[:]

        self.colors = {
            'black': (0, 0, 0),
            'text': (223, 246, 245)
        }

        self.content_space = 15
        self.font = pygame.font.Font('data/font/font.ttf', 20)
        self.title_font = pygame.font.Font('data/font/font.ttf', 30)
        self.title_render = self.title_font.render(self.title, True, self.colors['text'])

        self.width = self.title_render.get_width()
        self.height = self.title_render.get_height() + self.content_space

        self.position = position
        self.x, self.y = position

        self.alignment = alignment
        if self.alignment:
            self.render_width, self.render_height = 1024, 576
            self.render_dimensions = (self.render_width, self.render_height)

            if self.alignment == 'center':
                self.x = self.render_width / 2 - self.width / 2
                self.position = (self.x, self.y)

        self.render_surface = None
        self.rect = None
        self.pre_render()

    def update(self, input):
        mouse_pos = pygame.mouse.get_pos()
        pos_on_menu = (mouse_pos[0] - self.x, mouse_pos[1] - self.y)

        clicked = False
        for event in input:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True

        if clicked:
            for c in self.content:
                c.update(pos_on_menu)
                c.render(self.render_surface)
        else:
            for c in self.content:
                if isinstance(c, Button):
                    c.update()
                    c.render(self.render_surface)
                elif isinstance(c, Input):
                    c.handle_input(input)
                    c.render(self.render_surface)

    def render(self, surface):
        surface.blit(self.render_surface, self.position)

    def get_pressed(self, title):
        for c in self.content:
            if isinstance(c, Button):
                if c.title == title:
                    return c.get_pressed()
        return False

    def get_text(self, title):
        for c in self.content:
            if isinstance(c, Input):
                if c.title == title:
                    return c.get_text()
        return ''

    def pre_render(self):
        for c in self.content:
            c.rect.y = self.height

            self.height += c.rect.height
            self.height += self.content_space

            if c.rect.width > self.width:
                self.width = c.rect.width

        self.render_surface = pygame.Surface((self.width, self.height))
        self.render_surface.set_colorkey(self.colors['black'])

        self.rect = self.render_surface.get_rect()
        self.rect.topleft = self.position

        title_x = self.width / 2 - self.title_render.get_width() / 2
        title_y = 0
        self.render_surface.blit(self.title_render, (title_x, title_y))

        for c in self.content:
            c.rect.x = self.width / 2 - c.rect.width / 2

            c.render(self.render_surface)

        if self.alignment:
            if self.alignment == 'center':
                self.x = self.render_width / 2 - self.width / 2
                self.position = (self.x, self.y)

    def add_content(self, content, index=-1):
        if index == -1:
            self.content.append(content)
        else:
            self.content.insert(index, content)

        self.width = self.title_render.get_width()
        self.height = self.title_render.get_height() + self.content_space
        self.pre_render()
