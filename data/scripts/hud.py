import pygame
import time
from . import player


class Hud:
    def __init__(self, p: player.Player):
        self.player = p

        self.last_weapon = self.player.active_weapon
        self.last_ammo = self.player.ammo.copy()
        self.last_hearts = self.player.hearts
        self.last_reload = 0

        self.full_reload_duration = 60
        self.full_reload_count = 0

        self.last_time = time.time()
        self.dt = 1

        self.font = pygame.font.Font('data/font/font.ttf', 10)

        self.colors = {
            'black': (0, 0, 0),
            'text': (223, 246, 245),
            'selected_weapon': (223, 246, 245)
        }

        self.heart_images = [
            pygame.image.load('data/sprites/icons/heart.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/heart_half.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/heart_empty.png').convert_alpha()
        ]

        self.bullet_images = [
            pygame.image.load('data/sprites/icons/bullet.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/bullet_empty.png').convert_alpha()
        ]

        self.weapon_images = [
            pygame.image.load('data/sprites/icons/knife.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/pistol.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/rifle.png').convert_alpha()
        ]

        self.reload_images = [
            pygame.image.load('data/sprites/icons/reload_1.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/reload_2.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/reload_3.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/reload_4.png').convert_alpha(),
            pygame.image.load('data/sprites/icons/reload_5.png').convert_alpha()
        ]

        self.border_20x20 = pygame.image.load('data/sprites/icons/border_20x20.png').convert_alpha()
        self.border_36x20 = pygame.image.load('data/sprites/icons/border_36x20.png').convert_alpha()

        self.heart_render = pygame.Surface((self.heart_images[0].get_width() * self.player.max_hearts, self.heart_images[0].get_height()))
        self.heart_render.set_colorkey(self.colors['black'])

        self.bullets_render = pygame.Surface((self.bullet_images[0].get_width() * 10, (self.bullet_images[0].get_height() + 5) * int((self.player.rifle_max_ammo / 10))))
        self.bullets_render.set_colorkey(self.colors['black'])

        self.weapons_render = pygame.Surface((self.border_36x20.get_width(), (self.border_36x20.get_height() + 5) * len(self.weapon_images)))
        self.weapons_render.set_colorkey(self.colors['black'])

        self.reload_render = pygame.Surface((self.reload_images[0].get_width(), self.reload_images[0].get_height()))
        self.reload_render.set_colorkey(self.colors['black'])

        self.render_hearts()
        self.render_bullets()
        self.render_weapons()
        self.render_reload(self.last_reload)

    def update(self):
        self.dt = time.time() - self.last_time
        self.dt *= 120
        self.last_time = time.time()

        if self.player.active_weapon != self.last_weapon:
            self.last_weapon = self.player.active_weapon
            self.render_weapons()

        if self.player.ammo != self.last_ammo:
            self.last_ammo = self.player.ammo.copy()
            self.render_bullets()

        if self.player.hearts != self.last_hearts:
            self.last_hearts = self.player.hearts
            self.render_hearts()

        if self.player.reloading:
            progress = self.player.reloading_counter / self.player.reloading_duration
            if progress > self.last_reload:
                self.render_reload(progress)
                self.last_reload = progress
        elif self.last_reload != 0:
            self.last_reload = 0
            self.render_reload(1)
            self.full_reload_count = self.full_reload_duration
        elif self.full_reload_count > 0:
            self.full_reload_count -= self.dt
        else:
            self.render_reload(self.last_reload)

    def render(self, surface: pygame.Surface):
        surface.blit(self.heart_render, (36, 36))

        surface.blit(self.bullets_render, (1024 - self.bullets_render.get_width() - 36, 576 - self.bullets_render.get_height() - 36))

        surface.blit(self.weapons_render, (1024 - self.weapons_render.get_width() - 36, 36))

        if self.player.reloading or self.full_reload_count > 0:
            surface.blit(self.reload_render, (1024 - self.reload_render.get_width() - 36, 576 - self.bullets_render.get_height() - 36 - 10 - self.reload_render.get_height()))

    def render_hearts(self):
        self.heart_render.fill(self.colors['black'])

        x = 0
        for i in range(int(self.player.hearts)):
            self.heart_render.blit(self.heart_images[0], (i * self.heart_images[0].get_width(), 0))
            x += 1

        next_x = x
        if self.player.hearts % 1 == .5:
            self.heart_render.blit(self.heart_images[1], (next_x * self.heart_images[1].get_width(), 0))
            x += 1

        for i in range(self.player.max_hearts - x):
            self.heart_render.blit(self.heart_images[2], ((i + x) * self.heart_images[2].get_width(), 0))

    def render_bullets(self):
        self.bullets_render = pygame.Surface((self.bullet_images[0].get_width() * 10, (self.bullet_images[0].get_height() + 5) * int((self.player.ammo[0] / 10))))
        self.bullets_render.set_colorkey(self.colors['black'])

        self.bullets_render.fill(self.colors['black'])

        full = self.player.ammo[1]
        empty = self.player.ammo[0] - full

        x = 0
        y = 0
        for i in range(full):
            self.bullets_render.blit(self.bullet_images[0], (x * self.bullet_images[0].get_width(), y * (self.bullet_images[0].get_height() + 5)))
            x += 1
            if x == 10:
                x = 0
                y += 1

        for i in range(empty):
            self.bullets_render.blit(self.bullet_images[1], (x * self.bullet_images[0].get_width(), y * (self.bullet_images[0].get_height() + 5)))
            x += 1
            if x == 10:
                x = 0
                y += 1

    def render_weapons(self):
        self.weapons_render.fill(self.colors['black'])

        if self.player.active_weapon == 'rifle':
            pygame.draw.rect(self.weapons_render, self.colors['selected_weapon'], (4, 4, 64, 32))
        self.weapons_render.blit(self.border_36x20, (0, 0))
        self.weapons_render.blit(self.weapon_images[2], (4, 4))

        if self.player.active_weapon == 'pistol':
            pygame.draw.rect(self.weapons_render, self.colors['selected_weapon'], (4 + 32, self.border_36x20.get_height() + 5 + 4, 32, 32))
        self.weapons_render.blit(self.border_20x20, (32, self.border_36x20.get_height() + 5))
        self.weapons_render.blit(self.weapon_images[1], (4 + 32, self.border_36x20.get_height() + 5 + 4))

        if self.player.active_weapon == 'knife':
            pygame.draw.rect(self.weapons_render, self.colors['selected_weapon'], (4 + 32, self.border_36x20.get_height() * 2 + 5 * 2 + 4, 32, 32))
        self.weapons_render.blit(self.border_20x20, (32, self.border_36x20.get_height() * 2 + 5 * 2))
        self.weapons_render.blit(self.weapon_images[0], (4 + 32, self.border_36x20.get_height() * 2 + 5 * 2 + 4))

    def render_reload(self, progress):
        self.reload_render.fill(self.colors['black'])

        if progress < .25:
            self.reload_render.blit(self.reload_images[0], (0, 0))
        elif progress < .5:
            self.reload_render.blit(self.reload_images[1], (0, 0))
        elif progress < .75:
            self.reload_render.blit(self.reload_images[2], (0, 0))
        elif progress < 1:
            self.reload_render.blit(self.reload_images[3], (0, 0))
        else:
            self.reload_render.blit(self.reload_images[4], (0, 0))
