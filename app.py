import os
import random
import math
import pygame
import socket
import json
from os import listdir
from os.path import isfile, join
from client import connect_to_server, send_game_state, receive_game_state

pygame.init()

pygame.display.set_caption("Platformer")


WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)

        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Extra", "Box.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


def get_floor(size):
    path = join("assets", "Extra", "Grass.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


def get_tree(size):
    path = join("assets", "Extra", "Tree.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return surface


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "PinkMan", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        
        self.sprite = self.SPRITES["idle_left"][0]
        

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 3:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Floor(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_floor(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Tree(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        self.image = get_tree(size)
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, players, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    for player in players:
        player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 3)
    collide_right = collide(player, objects, PLAYER_VEL * 3)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()


def main(window):
    client_socket, player_id = connect_to_server()

    clock = pygame.time.Clock()
    background, bg_image = get_background("Sky.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    all_players = {player_id: player}
    # Fires
    fire = Fire(200, HEIGHT - block_size - 64, 16, 32)
    fire1 = Fire(600, HEIGHT - block_size - 64, 16, 32)
    fire2 = Fire(1100, HEIGHT - block_size - 64, 16, 32)
    fire3 = Fire(1170, HEIGHT - block_size - 64, 16, 32)
    fire4 = Fire(1320, 400 - 64, 16, 32)
    fire5 = Fire(1600, 400 - 64, 16, 32)
    fire6 = Fire(2050, HEIGHT - block_size - 64, 16, 32)
    fire7 = Fire(4800, 300 - 64, 16, 32)
    fire.on()
    fire1.on()
    fire2.on()
    fire3.on()
    fire4.on()
    fire5.on()
    fire6.on()
    fire7.on()

    tree = Tree(3500, HEIGHT - block_size - 192, 232)
    tree2 = Tree(3900, HEIGHT - block_size - 192, 232)

    floor = [Floor(i * block_size, HEIGHT - block_size, block_size)
             for i in range((-WIDTH * 2) // block_size, (WIDTH * 3) // block_size)]
    
    last_x = (len(floor) - 1) * block_size
    floor2 = [Floor(last_x - 1550 + i * block_size, HEIGHT - block_size, block_size)
              for i in range(10)]
    
    lastblock_floor2 = last_x - 1550 + (10 * block_size) 

# Add the desired spacing 
    firstblock_floor3 = lastblock_floor2 + 1250

# Create the third section of floor blocks
    floor3 = [Floor(firstblock_floor3 + i * block_size, HEIGHT - block_size, block_size)
          for i in range(10)]
    
    objects = []

    offset_x = 0
    scroll_area_width = 200

    # Function to create a section with 2 blocks
    def create_section_2(x, y, size):
        section_blocks = [Block(x, y, size), Block(x + size, y, size)]
        return section_blocks

    # Function to create a section with 3 blocks
    def create_section_3(x, y, size):
        section_blocks = [
            Block(x, y, size),
            Block(x + size, y, size),
            Block(x + 2 * size, y, size),
        ]
        return section_blocks

    # Function to create a section with 4 blocks
    def create_section_4(x, y, size):
        section_blocks = [
            Block(x, y, size),
            Block(x + size, y, size),
            Block(x + 2 * size, y, size),
            Block(x + 3 * size, y, size),
        ]
        return section_blocks

    # Function to create a vertical section
    def create_vertical_section(x, y, size):
        section_blocks = [
            Block(x, y, size),
            Block(x, y - size, size),
            Block(x, y - 2 * size, size),
            Block(x, y - 3 * size, size),
        ]
        return section_blocks

    run = True
    while run:
        clock.tick(FPS)

        objects.clear()

        # Add sections of blocks
        section1_blocks = create_section_2(300, 400, block_size)
        section2_blocks = create_section_3(800, 320, block_size)
        section3_blocks = create_section_4(1300, 400, block_size)
        section4_blocks = create_section_2(4400, 500, block_size)
        section5_blocks = create_section_4(4600, 300, block_size)
        section_vertical = create_vertical_section(
            50, HEIGHT - block_size * 2, block_size
        )
        section_vertical2 = create_vertical_section(
            1900, HEIGHT - block_size * 2, block_size
        )

        # Extend the 'objects' list
        objects.extend(section1_blocks)
        objects.extend(section2_blocks)
        objects.extend(section3_blocks)
        objects.extend(section4_blocks)
        objects.extend(section5_blocks)
        objects.extend(section_vertical)
        objects.extend(section_vertical2)

        objects.extend(floor)
        objects.extend(floor2)
        objects.extend(floor3)
        objects.extend(
            [
                Block(-400, HEIGHT - block_size * 2, block_size),
                Block(-200, HEIGHT - block_size * 3, block_size),
                Block(1800, HEIGHT - block_size * 2, block_size),
                Block(2200, HEIGHT - block_size * 3, block_size),
                Block(2200, HEIGHT - block_size * 4, block_size),
                Block(2600, HEIGHT - block_size * 3, block_size),
                Block(5300, HEIGHT - block_size // 2, block_size),
                fire,
                fire1,
                fire2,
                fire3,
                fire4,
                fire5,
                fire6,
                fire7,
                tree,
                tree2,
            ]
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
        # Send game state to sever
        send_game_state(client_socket, player.rect.x, player.rect.y)

        # Receive and Update Game State from Server
        game_state, _ = receive_game_state(client_socket)
        for p_id, coords in game_state.items():
            if p_id in all_players:
                all_players[p_id].rect.x = coords["x"]
                all_players[p_id].rect.y = coords["y"]
            else:
                new_player = Player(coords["x"], coords["y"], 50, 50)
                all_players[p_id] = new_player

        player.loop(FPS)

        # animate fires
        for obj in objects:
            if isinstance(obj, Fire):
                obj.loop()

        handle_move(player, objects)
        draw(
            window, background, bg_image, list(all_players.values()), objects, offset_x
        )

        if (
            (
                player.rect.right - offset_x >= WIDTH - scroll_area_width
                and player.x_vel > 0
            )
            or (player.rect.left - offset_x <= scroll_area_width)
            and player.x_vel < 0
        ):
            offset_x += player.x_vel

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
