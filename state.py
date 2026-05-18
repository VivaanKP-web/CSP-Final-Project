"""
state.py
--------
GameState is the top-level state machine.  It owns the clock, the current
level, the lives counter, and decides what to draw each frame.

State transitions
-----------------
    PLAYING  →  (player dies, lives > 0)  →  PLAYING  (respawn)
    PLAYING  →  (player dies, lives == 0) →  GAME_OVER
    GAME_OVER → (press R)                 →  PLAYING  (full reset)
"""
import pygame
import constants as C
import level as level_module


class GameState:

    def __init__(self, screen):
        self.screen = screen
        self.state = C.STATE_PLAYING
        self.lives = C.PLAYER_START_LIVES
        self.level_number = 1
        self.game_running = True

        self.clock = pygame.time.Clock()
        self.ui_font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 64)
        self.sub_font = pygame.font.SysFont("Arial", 28)

        # Keys currently held down
        self.keys_pressed = []

        self.load_level()

    def load_level(self):
        self.level = level_module.GameLevel(self.screen)


    def manage_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.game_running = False

            elif event.type == pygame.KEYDOWN:
                # R always restarts from scratch
                if event.key == pygame.K_r:
                    self.lives = C.PLAYER_START_LIVES
                    self.level_number = 1
                    self.state = C.STATE_PLAYING
                    self.load_level()

                # Escape quits
                elif event.key == pygame.K_ESCAPE:
                    self.game_running = False

                # Track actionable keys to avoid duplicates
                elif event.key in C.ACTIONABLE_KEYS and event.key not in self.keys_pressed:
                    self.keys_pressed.append(event.key)

            elif event.type == pygame.KEYUP:
                if event.key in self.keys_pressed:
                    self.keys_pressed.remove(event.key)

    # Per-frame logic
    def update_state(self):
        if self.state == C.STATE_PLAYING:
            self.level.update(self.keys_pressed)

            if not self.level.player.alive:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = C.STATE_GAME_OVER
                else:
                    # Respawn — reload the level but keep lives / level number
                    self.load_level()

    # Draw current state - Add other states here (like a menu)
    def draw_state(self):
        if self.state == C.STATE_PLAYING:
            self.level.draw()
            self.draw_ui()

        elif self.state == C.STATE_GAME_OVER:
            self.draw_game_over()

        pygame.display.flip()
        self.clock.tick(C.MAX_FPS)

    def draw_ui(self):
        """Draw lives counter and level number in the top-left corner."""
        #Feel free to modify this to add many more things to your UI as you deem necessary for your game
        lives_surf = self.ui_font.render(f"Lives: {self.lives}", True, pygame.Color("White"))
        level_surf = self.ui_font.render(f"Level: {self.level_number}", True, pygame.Color("White"))
        for surf, x, y in [(lives_surf, 12, 10), (level_surf, 12, 42)]:
            self.screen.blit(surf, (x, y))

    def draw_game_over(self):
        """Full-screen game-over overlay."""
        # Dark semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        cx = self.screen.get_width()  // 2
        cy = self.screen.get_height() // 2

        title  = self.big_font.render("GAME OVER", True, pygame.Color("red"))
        prompt = self.sub_font.render("Press R to try again  |  Esc to quit", True, pygame.Color("white"))

        self.screen.blit(title,  title.get_rect(center=(cx, cy - 40)))
        self.screen.blit(prompt, prompt.get_rect(center=(cx, cy + 30)))