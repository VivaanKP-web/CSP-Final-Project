"""
components.py
-------------
Behaviour components that can be attached to sprites.

Enemy AI components are passed in a list to Enemy(..., ai_list=[...]).
Each component implements a single update(owner) method that mutates
the owner sprite's state.  You can mix and match — an enemy can jump
AND shoot at the same time just by including both components.

Platform mover components work the same way for Platform sprites.
"""
import pygame
import util


# Enemy AI components
class StillEnemyAI:
    """Does nothing — the enemy just stands (or floats) in place."""

    def update(self, enemy):
        pass


class JumpingEnemyAI:
    """
    Makes the enemy jump every `frames_to_pause` frames while it is grounded.

    Parameters
    ----------
    jump_height     : upward velocity applied on each jump
    frames_to_pause : how many grounded frames to wait between jumps
    """

    def __init__(self, jump_height=12, frames_to_pause=45):
        self.frame_count    = 0
        self.jump_height    = jump_height
        self.frames_to_pause = frames_to_pause

    def update(self, enemy):
        if enemy.grounded:
            self.frame_count += 1
        if enemy.grounded and self.frame_count >= self.frames_to_pause:
            self.frame_count = 0
            enemy.velocity[1] = self.jump_height


class ShootingEnemyAI:
    """
    Makes the enemy fire a projectile every `recharge_time` frames.

    Parameters
    ----------
    launch_velocity       : pygame.Vector2 — initial velocity of the projectile
    rel_velocity          : pygame.Vector2 — added to the enemy's own velocity
                            (so moving enemies fire straight relative to
                            themselves); defaults to zero
    projectile_image_file : path to the projectile sprite image
    recharge_time         : frames between shots
    lifetime              : frames before the projectile disappears
    floating              : whether the projectile is affected by gravity
    """

    def __init__(self, launch_velocity=None, rel_velocity=None, projectile_image_file=None, recharge_time=45, lifetime=90, floating=False):
        self.launch_velocity        = launch_velocity or pygame.Vector2(8, 0)
        self.rel_velocity           = rel_velocity    or pygame.Vector2(0, 0)
        self.projectile_image_file  = projectile_image_file or util.get_image_path("seal.png")
        self.recharge_time          = recharge_time
        self.lifetime               = lifetime
        self.floating               = floating
        self.frame_count            = 0

    def update(self, enemy):
        self.frame_count += 1
        if self.frame_count >= self.recharge_time:
            self.frame_count = 0
            enemy.fire_projectile(pygame.Vector2(self.launch_velocity), pygame.Vector2(self.rel_velocity), self.projectile_image_file, self.lifetime, self.floating)


class PatrolEnemyAI:
    """
    Makes the enemy walk back and forth across a fixed horizontal range.

    Parameters
    ----------
    speed       : horizontal speed while patrolling
    patrol_range: pixels to travel in each direction before turning
    """

    def __init__(self, speed=3, patrol_range=150):
        self.speed        = speed
        self.patrol_range = patrol_range
        self.start_x      = None
        self.direction    = 1   # 1 = right, -1 = left

    def update(self, enemy):
        # Latch the starting position on the first frame
        if self.start_x is None:
            self.start_x = enemy.position[0]

        enemy.velocity[0] = self.speed * self.direction

        # Flip direction when reaching patrol boundary
        distance = enemy.position[0] - self.start_x
        if distance > self.patrol_range:
            self.direction = -1
        elif distance < 0:
            self.direction = 1

        # Keep facing consistent with movement direction
        from constants import FACING_LEFT, FACING_RIGHT
        enemy.facing = FACING_RIGHT if self.direction == 1 else FACING_LEFT


# Platform mover components
class HorizontalMover:
    """
    Moves a platform left and right between two x-positions.

    Parameters
    ----------
    speed       : pixels per frame
    move_range  : total horizontal distance to travel (half each way)
    """

    def __init__(self, speed=2, move_range=200):
        self.speed      = speed
        self.move_range = move_range
        self.start_x    = None
        self.direction  = 1

    def update(self, platform):
        if self.start_x is None:
            self.start_x = platform.position[0]

        platform.velocity[0] = self.speed * self.direction

        distance = platform.position[0] - self.start_x
        if distance > self.move_range / 2:
            self.direction = -1
        elif distance < -self.move_range / 2:
            self.direction = 1


class VerticalMover:
    """
    Moves a platform up and down between two y-positions.

    Parameters
    ----------
    speed       : pixels per frame
    move_range  : total vertical distance to travel (half each way)
    """

    def __init__(self, speed=2, move_range=150):
        self.speed      = speed
        self.move_range = move_range
        self.start_y    = None
        self.direction  = 1

    def update(self, platform):
        if self.start_y is None:
            self.start_y = platform.position[1]

        platform.velocity[1] = self.speed * self.direction

        distance = platform.position[1] - self.start_y
        if distance > self.move_range / 2:
            self.direction = -1
        elif distance < -self.move_range / 2:
            self.direction = 1