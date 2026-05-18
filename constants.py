"""
constants.py
------------
All the magic numbers for the game in one place.
This is the best file to tweak when adjusting game feel!
"""
import pygame

#Screen
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
MAX_FPS       = 45

#Sprite sizes (width, height)
SMALL_SPRITE_SIZE  = pygame.Vector2(20, 20)
MEDIUM_SPRITE_SIZE = pygame.Vector2(40, 40)
LARGE_SPRITE_SIZE  = pygame.Vector2(60, 60)
XL_SPRITE_SIZE     = pygame.Vector2(80, 80)

#Physics constants
GRAVITY               = pygame.Vector2(0, -1)   # applied every frame when airborne
FRICTION              = pygame.Vector2(0.1, 0)  # x-deceleration when grounded
COLLISION_ENERGY_LOSS = 0.5                      # fraction of velocity kept after a wall hit

#Player constants
PLAYER_MAX_SPEED            = 8
PLAYER_SPEED_INCREMENT      = 2
PLAYER_JUMP_SPEED           = 25
PLAYER_PROJECTILE_RECHARGE  = 15   # frames between shots
PLAYER_START_LIVES          = 3

#Projectile constants
PROJECTILE_DEFAULT_SPEED    = 15
PROJECTILE_DEFAULT_LIFETIME = 90   # frames

#Facing directions (used across multiple classes)
FACING_RIGHT = 0
FACING_LEFT  = 1
FACING_UP    = 2
FACING_DOWN  = 3

#Game-state identifiers 
STATE_PLAYING   = 0
STATE_PAUSED    = 1
STATE_GAME_OVER = 2
STATE_WIN       = 3

#Keys the game cares about
ACTIONABLE_KEYS = [
    pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d,
    pygame.K_SPACE, pygame.K_j,
]