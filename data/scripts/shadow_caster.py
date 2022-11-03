import pygame
from scipy import spatial
from shapely import geometry, ops
from threading import Thread


class Shadow:
    def __init__(self, rect, polygon):
        self.rect = rect
        self.polygon = polygon
        self.shapely = geometry.Polygon(self.polygon)


class ShadowCaster:
    def __init__(self, player, map, shadow_color):
        self.player = player
        self.map = map
        self.render_width = 1024
        self.render_height = 576

        self.colors = {
            'black': (0, 0, 0),
            'shadows': shadow_color,
            'green': (0, 255, 0),
            'red': (255, 0, 0)
        }
        
        self.render_surface = pygame.Surface((self.render_width, self.render_height))
        self.render_surface.set_colorkey(self.colors['black'])

        self.last_player_center = (0, 0)

    def update(self, debug=False):
        if (int(self.player.center[0]), int(self.player.center[1])) != self.last_player_center:
            self.last_player_center = (int(self.player.center[0]), int(self.player.center[1]))
            self.render_surface.fill(self.colors['black'])

            for wall in self.map.inside_walls:
                nearest_point = list(ops.nearest_points(geometry.Point(self.player.center), wall.shapely)[1].coords)[0]
                wall.distance = round(((nearest_point[0] - self.player.center[0]) ** 2 + (nearest_point[1] - self.player.center[1]) ** 2) ** .5, 2)

            wall_shadows = []

            for wall in sorted(self.map.inside_walls, key=lambda x: x.distance):
                allpoints = []

                new_points = []

                skip = False
                for finished_shadow in wall_shadows:
                    if finished_shadow.shapely.contains(wall.shapely):
                        skip = True
                        break

                if skip:
                    continue

                for corner in wall.corners:
                    vx = corner[0] - self.player.center[0]
                    vy = corner[1] - self.player.center[1]

                    evx = vx / (vx ** 2 + vy ** 2) ** .5
                    evy = vy / (vx ** 2 + vy ** 2) ** .5

                    if evx < 0:
                        shadow_length_x = (0 - corner[0]) / evx
                    elif evx > 0:
                        shadow_length_x = (self.render_width - corner[0]) / evx
                    else:
                        shadow_length_x = 10 ** 10

                    if evy < 0:
                        shadow_length_y = (0 - corner[1]) / evy
                    elif evy > 0:
                        shadow_length_y = (self.render_height - corner[1]) / evy
                    else:
                        shadow_length_y = 10 ** 10

                    shadow_length = min(shadow_length_x, shadow_length_y)

                    nx = corner[0] + evx * shadow_length
                    ny = corner[1] + evy * shadow_length

                    new_point = [int(nx), int(ny)]

                    allpoints.append(corner)
                    allpoints.append(new_point)
                    new_points.append(new_point)

                    if debug:
                        pygame.draw.circle(self.render_surface, self.colors['red'], corner, 2)
                        pygame.draw.circle(self.render_surface, self.colors['green'], new_point, 2)

                        pygame.draw.aaline(self.render_surface, self.colors['red'], self.player.center, corner)
                        pygame.draw.aaline(self.render_surface, self.colors['green'], corner, new_point)

                x_values = [i[0] for i in new_points]
                y_values = [i[1] for i in new_points]
                left = 0 in x_values
                right = self.render_width in x_values
                top = 0 in y_values
                bottom = self.render_height in y_values

                if left and top:
                    allpoints.append([0, 0])

                if right and top:
                    allpoints.append([self.render_width, 0])

                if left and bottom:
                    allpoints.append([0, self.render_height])

                if right and bottom:
                    allpoints.append([self.render_width, self.render_height])

                if left and right and not top and not bottom:
                    if self.player.center[1] > max(y_values):
                        allpoints.append([0, 0])
                        allpoints.append([self.render_width, 0])

                    if self.player.center[1] < min(y_values):
                        allpoints.append([0, self.render_height])
                        allpoints.append([self.render_width, self.render_height])

                if top and bottom and not left and not right:
                    if self.player.center[0] > max(x_values):
                        allpoints.append([0, 0])
                        allpoints.append([0, self.render_height])

                    if self.player.center[0] < min(x_values):
                        allpoints.append([self.render_width, 0])
                        allpoints.append([self.render_width, self.render_height])

                shadow_indices = spatial.ConvexHull(allpoints).vertices
                shadow_shape = [allpoints[i] for i in shadow_indices]

                x_values = [i[0] for i in allpoints]
                y_values = [i[1] for i in allpoints]

                x = min(x_values)
                y = min(y_values)
                width = max(x_values) - x
                height = max(y_values) - y

                shadow_rect = pygame.Rect(x, y, width, height)
                wall_shadows.append(Shadow(shadow_rect, shadow_shape))

                pygame.draw.polygon(self.render_surface, self.colors['shadows'], shadow_shape)

    def render(self, surface):
        surface.blit(self.render_surface, (0, 0))
