"""
main.py
-------
Entry point.  Run this file to start the game.

    python main.py
"""
import pygame
import state
import constants as C


def main():
    pygame.init()
    screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
    pygame.display.set_caption("Penguin Platformer")

    game = state.GameState(screen)

    while game.game_running:
        game.manage_events(pygame.event.get())
        game.update_state()
        game.draw_state()

    pygame.quit()


if __name__ == "__main__":
    main()