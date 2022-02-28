import pygame
import time


def load_animation(path, length):
    animation = []
    for i in range(length):
        image = pygame.image.load(f'{path}{i+1}.png').convert_alpha()
        animation.append(image)
    return animation


def to_renderer_position(pos):
    new_x = (1024 * pos[0]) / 1920
    new_y = (576 * pos[1]) / 1080
    return new_x, new_y


class Bullet:
    def __init__(self, direction, center, speed, damage, map):
        self.one_direction = direction
        self.direction = (direction[0] * speed, direction[1] * speed)
        self.center = center
        self.map = map
        self.damage = damage

        self.dead = False
        self.collided = False

        self.last_time = time.time()
        self.dt = 1

        self.frames = load_animation('data/sprites/animations/bullet_', 3)

        self.frame = 0
        self.animation_change = 10
        self.animation_count = 0
        self.image = self.frames[self.frame]
        self.rect = self.image.get_rect(center=self.center)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.dt = time.time() - self.last_time
        self.dt *= 120
        self.last_time = time.time()

        if not self.collided:
            self.center = (self.center[0] + min(self.direction[0] * self.dt, 33), self.center[1] + min(self.direction[1] * self.dt, 33))
            self.rect.center = self.center

            for wall in self.map.walls:
                if self.rect.colliderect(wall.rect):
                    while wall.rect.collidepoint(self.center):
                        self.center = (self.center[0] - self.one_direction[0] * self.dt, self.center[1] - self.one_direction[1] * self.dt)
                    self.rect.center = self.center
                    self.collided = True
                    break
        else:
            if self.animation_count >= self.animation_change:
                self.frame += 1
                self.animation_count = 0
                if self.frame == len(self.frames):
                    self.dead = True
                else:
                    self.image = self.frames[self.frame]
            self.animation_count += self.dt

    def render(self, surface: pygame.Surface):
        surface.blit(self.image, self.rect)
