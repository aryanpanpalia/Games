import os
import random
import sys
from typing import List

import numpy as np
import pygame

import model

WIDTH, HEIGHT = 400, 800
FPS = 60
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minesweeper!")
pygame.font.init()
clock = pygame.time.Clock()


def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


empty = pygame.transform.scale(pygame.image.load(resource_path('assets/Empty.png')), (40, 40))
game_over = pygame.transform.scale(pygame.image.load(resource_path('assets/GameOver.png')), (200, 200))

PLAYING = 0
LOST = 1
WON = 2

COLORS = [(0, 0, 255), (255, 0, 0), (255, 165, 0), (0, 255, 0), (255, 192, 203), (255, 0, 255), (255, 255, 0)]


def is_open(blocks: List[model.Block], spots: List[list]):
    for block in blocks:
        for element in block.elements:
            if element in spots:
                return False
    return True


def is_valid(spots: List[list]):
    for spot in spots:
        if not (0 <= spot[0] < 21 and 0 <= spot[1] < 10):
            return False
    return True


def handle_input(events, blocks: List[model.Block]):
    for event in events:
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()

            if keys[pygame.K_UP]:
                preview = blocks[-1].rotate_preview()

                if is_open(blocks[:-1], preview) and is_valid(preview):
                    blocks[-1].rotate()
                    return True

            elif keys[pygame.K_DOWN]:
                # drop max amount
                for _ in range(21):
                    preview = blocks[-1].drop_preview()

                    if is_open(blocks[:-1], preview) and is_valid(preview):
                        blocks[-1].drop()

                blocks[-1].is_falling = False
                return False

            elif keys[pygame.K_LEFT]:
                preview = blocks[-1].move_left_preview()

                if is_open(blocks[:-1], preview) and is_valid(preview):
                    blocks[-1].move_left()
                    return True

            elif keys[pygame.K_RIGHT]:
                preview = blocks[-1].move_right_preview()

                if is_open(blocks[:-1], preview) and is_valid(preview):
                    blocks[-1].move_right()
                    return True


def draw_view(blocks: List[model.Block]):
    view = np.zeros((21, 10))
    for block in blocks:
        for element in block.elements:
            if element is not None:
                color = block.color
                color_index = COLORS.index(color)
                view[element[0], element[1]] = color_index + 1

    for row in range(1, 21):
        for col in range(10):
            if view[row, col] != 0:
                rect = pygame.Rect(col * 40, (row - 1) * 40, 40, 40)
                color = COLORS[int(view[row, col]) - 1]
                WIN.fill(color, rect=rect)
            else:
                WIN.blit(empty, (col * 40, (row - 1) * 40))

    pygame.display.update()


def clear_full_rows(blocks: List[model.Block]):
    view = np.zeros((21, 10))
    for block in blocks:
        for element in block.elements:
            view[element[0], element[1]] = 1

    full_rows = []

    for row in range(21):
        if 0 not in view[row]:
            full_rows.append(row)

    to_remove = []

    for block in blocks:
        for element in block.elements:
            if element[0] in full_rows:
                to_remove.append([block, element])

    for block, element in to_remove:
        block.remove(element)

    if len(full_rows) > 0:
        draw_view(blocks)
        clock.tick(2)

    for num_drops_already, row in enumerate(reversed(full_rows)):
        # for every row removed, drop every row above it down one starting from the bottom row
        to_drop = []
        for block in blocks:
            for element in block.elements:
                # since the elements are being drop right after this, while the full-rows arent changing, the number of
                # already done drops has to be accounted for to see if a certain row qualifies for a drop
                if element[0] < row + num_drops_already:
                    to_drop.append([block, element])

        for block, element in to_drop:
            block.drop_element(element)

        draw_view(blocks)
        clock.tick(2)

    # clear out any blocks that no longer have any elements remaining on the board
    blocks_to_remove = []
    for block in blocks:
        if len(block.elements) == 0:
            blocks_to_remove.append(block)

    for block in blocks_to_remove:
        blocks.remove(block)


def choose_random_block():
    options = [model.IBlock(), model.JBlock(), model.LBlock(), model.OBlock(), model.SBlock(), model.ZBlock(), model.TBlock()]
    return random.choice(options)


def main():
    running = True
    state = PLAYING

    blocks = [choose_random_block()]
    time_since_moved = 999
    time_since_dropped = 0

    while running:
        clock.tick(FPS)
        time_since_moved += 1 / FPS
        time_since_dropped += 1 / FPS
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        if state == PLAYING:
            if len(blocks) == 0 or not blocks[-1].is_falling:
                clear_full_rows(blocks)
                new_block = choose_random_block()
                if is_open(blocks, new_block.elements):
                    blocks.append(new_block)
                    clock.tick(2)
                    time_since_dropped = 0
                else:
                    state = LOST
            else:
                moved = handle_input(events, blocks)
                if moved:
                    time_since_moved = 0

                if time_since_moved > 0.25 and time_since_dropped > 0.5:
                    preview = blocks[-1].drop_preview()

                    if is_open(blocks[:-1], preview) and is_valid(preview):
                        blocks[-1].drop()
                    else:
                        blocks[-1].is_falling = False

                    time_since_dropped = 0

            draw_view(blocks)

        if state == LOST:
            WIN.blit(game_over, (100, 300))

            mouse_press, mouse_loc = pygame.mouse.get_pressed(), pygame.mouse.get_pos()

            if mouse_press[0]:
                if 300 + 125 < mouse_loc[1] < 300 + 125 + 100 and 100 + 70 < mouse_loc[0] < 100 + 70 + 60:
                    main()
                    return

            pygame.display.update()


if __name__ == '__main__':
    main()
