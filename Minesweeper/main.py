import random

import numpy as np
import pygame

WIDTH, HEIGHT = 500, 550
FPS = 15
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minesweeper!")
pygame.font.init()

dblock = pygame.transform.scale(pygame.image.load('assets/defaultblock.png'), (50, 50))
nblocks = [pygame.transform.scale(pygame.image.load(f'assets/{n}.png'), (50, 50)) for n in range(9)]
fblock = pygame.transform.scale(pygame.image.load('assets/flag.png'), (50, 50))
bblock = pygame.transform.scale(pygame.image.load('assets/bomb.png'), (50, 50))
flag = pygame.transform.scale(pygame.image.load('assets/flag2.png'), (50, 50))

NON = 0
LOS = 1
VIC = 2


def generate_map(num_bombs=20):
    rand = random.Random()
    selected = []
    while len(selected) < num_bombs:
        selection = rand.randint(0, 99)
        if selection not in selected:
            selected.append(selection)

    selected.sort()

    bomb_map = np.array([
        [0 if (10 * row + col) not in selected else -1 for col in range(10)] for row in range(10)
    ])

    final_map = np.zeros((10, 10), dtype=int)

    bomb_map_padded = np.pad(bomb_map, ((1, 1), (1, 1)))

    for row in range(1, 11):
        for col in range(1, 11):
            if bomb_map_padded[row, col] == 0:
                val = -bomb_map_padded[row-1:row+2, col-1:col+2].sum()
                final_map[row-1, col-1] = val
            else:
                final_map[row-1, col-1] = -1

    return final_map


def draw_view(view, state=NON):
    WIN.fill((200, 200, 200))

    for row in range(10):
        for col in range(10):
            if view[row, col] == -3:
                WIN.blit(bblock, (col * 50, row * 50 + 50))
            if view[row, col] == -2:
                WIN.blit(dblock, (col * 50, row * 50 + 50))
            if view[row, col] == -1:
                WIN.blit(fblock, (col * 50, row * 50 + 50))
            elif view[row, col] in range(0, 9):
                WIN.blit(nblocks[int(view[row, col])], (col * 50, row * 50 + 50))

    WIN.blit(flag, (0, 0))
    font = pygame.font.SysFont("Comic Sans MS", 45)
    numflags = font.render(f"{np.count_nonzero(view == -1)}", True, (0, 0, 0))
    WIN.blit(numflags, (50, -8))

    if state == LOS:
        font = pygame.font.SysFont("Comic Sans MS", 45)
        text = font.render(f"You Lost!", True, (0, 0, 0))
        WIN.blit(text, (150, -8))

        play_again = pygame.Rect(375, 5, 50, 40)
        pygame.draw.rect(WIN, (0, 255, 0), play_again)
        stop = pygame.Rect(430, 5, 50, 40)
        pygame.draw.rect(WIN, (255, 0, 0), stop)

    pygame.display.update()


def handle_input(mouse_press, mouse_loc, map, view):
    loc = (mouse_loc[1] // 50 - 1, mouse_loc[0] // 50)

    if mouse_press[0]:
        val = map[loc]

        if val == -1:
            view[loc] = -3
            return LOS
        elif val == 0:
            clear_zeros(map, view, loc)
        else:
            view[loc] = val

    if mouse_press[2]:
        if view[loc] == -2:
            view[loc] = -1
        elif view[loc] == -1:
            view[loc] = -2


def clear_zeros(map, view, loc):
    view[loc] = map[loc]
    if map[loc] == 0:
        for row in range(loc[0] - 1, loc[0] + 2):
            for col in range(loc[1] - 1, loc[1] + 2):
                if 0 <= row < 10 and 0 <= col < 10 and (row, col) != loc and view[row, col] == -2:
                    clear_zeros(map, view, (row, col))


def lose(map, view):
    for row in range(10):
        for col in range(10):
            if map[row, col] == -1:
                view[row, col] = -3

    draw_view(view, LOS)


def win():
    print("You Won")


def postgame_input(mouse_press, mouse_loc):
    if mouse_press[0]:
        if 375 < mouse_loc[0] < 425 and 5 < mouse_loc[1] < 45:
            return 1
        elif 430 < mouse_loc[0] < 480 and 5 < mouse_loc[1] < 45:
            return 0


def main():
    map = generate_map()
    view = np.ones_like(map) * -2

    print(map)

    clock = pygame.time.Clock()
    running = True
    state = NON
    decision = None
    CHEAT_MODE_FOR_TESTING = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if state == NON:
            _state = handle_input(pygame.mouse.get_pressed(), pygame.mouse.get_pos(), map, view)
            if _state is not None and not CHEAT_MODE_FOR_TESTING:
                state = _state

        draw_view(view, state)

        if state == LOS:
            lose(map, view)
            decision = postgame_input(pygame.mouse.get_pressed(), pygame.mouse.get_pos())
            if decision is not None:
                running = False
        if np.array_equal(map, view) or state == VIC:
            state = VIC
            win()
            decision = postgame_input(pygame.mouse.get_pressed(), pygame.mouse.get_pos())
            if decision is not None:
                running = False

    if decision == 0:
        pygame.quit()
    elif decision == 1:
        main()


if __name__ == '__main__':
    main()
