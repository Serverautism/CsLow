import pygame
import time
import math
from . import bullet
import threading


def load_animation(path, length):
    animation = []
    for i in range(length):
        image = pygame.image.load(f'{path}{i+1}.png').convert_alpha()
        animation.append(image)
    return animation


def to_renderer_position(pos):
    new_x = (1024 * pos[0]) / 1024
    new_y = (576 * pos[1]) / 576
    return new_x, new_y


class RemotePlayer:
    def __init__(self, map):
        self.map = map
        self.center = (4 * 32, 3 * 32)
        self.rotation = 0
        self.active_weapon = 'pistol'
        self.hearts = 3

        self.knife_frames = load_animation('data/sprites/animations/knife_', 2)
        self.pistol_frames = load_animation('data/sprites/animations2/pistol_', 2)
        self.rifle_frames = load_animation('data/sprites/animations2/rifle_', 2)

        self.image = self.pistol_frames[0]
        self.rect = self.image.get_rect(center=self.center)
        self.rotated_image = self.image
        self.mask = pygame.mask.from_surface(self.image)

        self.frame = 0

        self.bullets = []
        self.new_bullets = []

    def update(self):
        self.rotated_image = pygame.transform.rotate(self.image, self.rotation)
        self.rect = self.rotated_image.get_rect(center=self.center)
        self.mask = pygame.mask.from_surface(self.rotated_image)

        self.update_bullets()

    def render(self, surface: pygame.Surface):
        surface.blit(self.rotated_image, self.rect)

        for b in self.bullets:
            b.render(surface)

    def set_rotation(self, angle):
        self.rotation = angle

    def set_center(self, center):
        self.center = center
        self.rect.center = center

    def set_image(self, weapon=None, frame=None):
        if weapon is not None:
            self.active_weapon = weapon

        if frame is not None:
            self.frame = frame

        if self.active_weapon == 'knife':
            self.image = self.knife_frames[self.frame]
        elif self.active_weapon == 'pistol':
            self.image = self.pistol_frames[self.frame]
        elif self.active_weapon == 'rifle':
            self.image = self.rifle_frames[self.frame]

    def update_bullets(self):
        to_remove = []
        for b in self.bullets:
            b.update()
            if b.dead:
                to_remove.append(b)

        for b in to_remove:
            self.bullets.remove(b)

    def add_bullet(self, direction, center, speed, damage, new=False):
        b = bullet.Bullet(direction, center, speed, damage, self.map)
        self.bullets.append(b)

        if new:
            self.new_bullets.append([direction, center, speed, damage])

    def get_new_bullets(self):
        if len(self.new_bullets) > 0:
            copy = self.new_bullets[:]
            self.new_bullets.clear()
            return copy
        else:
            return []


class Player:
    def __init__(self, center, map):
        self.center = center
        self.map = map
        self.spawn = center

        self.last_time = time.time()
        self.dt = 1

        self.speed = 1
        self.dx = 0
        self.dy = 0

        self.knife_frames = load_animation('data/sprites/animations/knife_', 2)
        self.pistol_frames = load_animation('data/sprites/animations2/pistol_', 2)
        self.rifle_frames = load_animation('data/sprites/animations2/rifle_', 2)

        self.frame = 0

        self.image = self.pistol_frames[self.frame]
        self.rect = self.image.get_rect(center=self.center)
        self.mask = pygame.mask.from_surface(self.image)

        self.rotation = 0
        self.rotated_image = self.image

        self.bullets = []
        self.new_bullets = []
        self.bullets_speed = 30

        self.active_weapon = 'pistol'

        self.knife_delay = 30
        self.knife_attack_duration = 10
        self.knife_max_ammo = 0
        self.knife_ammo = [self.knife_max_ammo, self.knife_max_ammo]
        self.knife_damage = 3

        self.pistol_delay = 10
        self.pistol_attack_duration = 5
        self.pistol_recoil = .5
        self.pistol_max_ammo = 10
        self.pistol_ammo = [self.pistol_max_ammo, self.pistol_max_ammo]
        self.pistol_damage = 1

        self.rifle_delay = 20
        self.rifle_attack_duration = 5
        self.rifle_recoil = 1
        self.rifle_max_ammo = 30
        self.rifle_ammo = [self.rifle_max_ammo, self.rifle_max_ammo]
        self.rifle_damage = .5

        self.delay_count = 0
        self.attack_count = 0
        self.can_attack = True
        self.reloading = False
        self.reloading_duration = 100
        self.reloading_counter = 0

        self.ammo = self.pistol_ammo

        self.max_hearts = 3
        self.hearts = self.max_hearts

        self.damage_taken = []

    def update(self, enemies=None):
        self.dt = time.time() - self.last_time
        self.dt *= 120
        self.last_time = time.time()

        if self.reloading:
            self.reloading_counter += 1
            if self.reloading_counter == self.reloading_duration:
                if self.active_weapon == 'pistol':
                    self.pistol_ammo = [self.pistol_max_ammo, self.pistol_max_ammo]
                    self.ammo = self.pistol_ammo
                elif self.active_weapon == 'rifle':
                    self.rifle_ammo = [self.rifle_max_ammo, self.rifle_max_ammo]
                    self.ammo = self.rifle_ammo

                self.reloading_counter = 0
                self.reloading = False

        if not self.can_attack:
            self.delay_count += self.dt
            if self.active_weapon == 'knife':
                if self.delay_count >= self.knife_delay:
                    self.can_attack = True
                    self.delay_count = 0
            elif self.active_weapon == 'pistol':
                if self.delay_count >= self.pistol_delay:
                    self.can_attack = True
                    self.delay_count = 0
            elif self.active_weapon == 'rifle':
                if self.delay_count >= self.rifle_delay:
                    self.can_attack = True
                    self.delay_count = 0

        if self.frame == 1:
            self.attack_count += self.dt
            if self.active_weapon == 'knife':
                if self.attack_count >= self.knife_attack_duration:
                    self.attack_count = 0
                    self.frame = 0
            elif self.active_weapon == 'pistol':
                if self.attack_count >= self.pistol_attack_duration:
                    self.attack_count = 0
                    self.frame = 0
            elif self.active_weapon == 'rifle':
                if self.attack_count >= self.rifle_attack_duration:
                    self.attack_count = 0
                    self.frame = 0

        old_rect = self.rect

        self.center = (self.center[0] + self.dx * self.dt, self.center[1] + self.dy * self.dt)

        self.rotate()

        self.update_image()

        self.rotated_image = pygame.transform.rotate(self.image, self.rotation)
        self.rect = self.rotated_image.get_rect(center=self.center)
        self.mask = pygame.mask.from_surface(self.rotated_image)

        self.check_collision_x((self.center[0], old_rect.center[1]), pygame.Rect(self.rect.x, old_rect.y, self.rect.width, old_rect.height))
        self.check_collision_y(self.center, self.rect)

        if enemies:
            self.check_enemy_bullets(enemies)

        self.update_bullets()

    def render(self, surface: pygame.Surface):
        surface.blit(self.rotated_image, self.rect)

        for b in self.bullets:
            b.render(surface)

    def check_enemy_bullets(self, enemies):
        for i, enemy in enumerate(enemies):
            if enemy:
                for j, bullet in enumerate(enemy.bullets):
                    if bullet.damage != 0:
                        if pygame.sprite.collide_mask(self, bullet):
                            self.damage_taken.append([i, j, bullet.damage])
                            # self.hearts -= bullet.damage
                            bullet.damage = 0

    def attack(self, clicked=False):
        if self.can_attack and (self.ammo[1] != 0 or self.active_weapon == 'knife') and not self.reloading:
            if self.active_weapon != 'rifle':
                if not clicked:
                    return

            if self.active_weapon == 'rifle' or self.active_weapon == 'pistol':
                mouse_pos = to_renderer_position(pygame.mouse.get_pos())

                direction = (mouse_pos[0] - self.center[0], mouse_pos[1] - self.center[1])
                direction_speed = (direction[0] ** 2 + direction[1] ** 2) ** .5
                direction = ((direction[0] / direction_speed), (direction[1] / direction_speed))

                center = (self.center[0] + direction[0] * 30, self.center[1] + direction[1] * 30)

                if self.active_weapon == 'pistol':
                    self.bullets.append(bullet.Bullet(direction, center, self.bullets_speed, self.pistol_damage, self.map))
                    self.new_bullets.append([direction, center, self.bullets_speed, self.pistol_damage])
                else:
                    self.bullets.append(bullet.Bullet(direction, center, self.bullets_speed/2, self.rifle_damage, self.map))
                    self.new_bullets.append([direction, center, self.bullets_speed/2, self.rifle_damage])

                self.frame = 1
                self.ammo[1] -= 1

            elif self.active_weapon == 'knife':
                self.frame = 1

            self.can_attack = False

    def get_new_bullets(self):
        if len(self.new_bullets) > 0:
            copy = self.new_bullets[:]
            self.new_bullets.clear()
            return copy
        else:
            return []

    def reload(self):
        if self.active_weapon != 'knife':
            self.reloading = True

    def update_bullets(self):
        to_remove = []
        for b in self.bullets:
            threading.Thread(target=b.update).start()
            if b.dead:
                to_remove.append(b)

        for b in to_remove:
            self.bullets.remove(b)

    def switch_weapon(self, ind: int):
        if not self.reloading and self.can_attack:
            index = ind
            if index == -1:
                if self.active_weapon == 'pistol':
                    index = 1
                elif self.active_weapon == 'knife':
                    index = 2
            elif index == -2:
                if self.active_weapon == 'rifle':
                    index = 2
                elif self.active_weapon == 'pistol':
                    index = 3

            if index == 1:
                self.active_weapon = 'rifle'
                self.image = self.rifle_frames[self.frame]
                self.ammo = self.rifle_ammo
            elif index == 2:
                self.active_weapon = 'pistol'
                self.image = self.pistol_frames[self.frame]
                self.ammo = self.pistol_ammo
            elif index == 3:
                self.active_weapon = 'knife'
                self.image = self.knife_frames[self.frame]
                self.ammo = self.knife_ammo

            self.delay_count = 0
            self.attack_count = 0
            self.frame = 0
            self.can_attack = True

    def update_image(self):
        if self.active_weapon == 'knife':
            self.image = self.knife_frames[self.frame]
        elif self.active_weapon == 'pistol':
            self.image = self.pistol_frames[self.frame]
        elif self.active_weapon == 'rifle':
            self.image = self.rifle_frames[self.frame]

    def rotate(self):
        mouse_pos = to_renderer_position(pygame.mouse.get_pos())
        radians = math.atan2(mouse_pos[1] - self.center[1], mouse_pos[0] - self.center[0])
        angle = math.degrees(radians)
        self.rotation = -angle

    def check_collision_x(self, center, rect):
        rect.center = center
        for t in self.map.walls:
            if rect.colliderect(t.rect):
                if rect.x > t.rect.x:
                    self.rect.left = t.rect.right
                else:
                    self.rect.right = t.rect.left
                self.center = self.rect.center

    def check_collision_y(self, center, rect):
        rect.center = center
        for t in self.map.walls:
            if self.rect.colliderect(t.rect):
                if rect.y > t.rect.y:
                    self.rect.top = t.rect.bottom
                else:
                    self.rect.bottom = t.rect.top
                self.center = self.rect.center

    def get_damage_taken(self, index: int):
        for damage in self.damage_taken:
            damage.append(index)
        copy = self.damage_taken[:]
        self.damage_taken.clear()
        return copy

    def go_up(self):
        self.dy = -self.speed
        if self.dx != 0:
            self.dy = -((self.speed ** 2)/2) ** 0.5

    def go_down(self):
        self.dy = self.speed
        if self.dx != 0:
            self.dy = ((self.speed ** 2)/2) ** 0.5

    def go_left(self):
        self.dx = -self.speed
        if self.dy != 0:
            self.dx = -((self.speed ** 2)/2) ** 0.5

    def go_right(self):
        self.dx = self.speed
        if self.dy != 0:
            self.dx = ((self.speed ** 2)/2) ** 0.5

    def stop_x(self):
        self.dx = 0

    def stop_y(self):
        self.dy = 0
