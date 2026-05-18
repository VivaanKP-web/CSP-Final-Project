"""
sprites.py
----------
All game sprite classes.

Hierarchy:
    pygame.sprite.Sprite
    └── GameObject          (position, image, facing, camera offset)
        └── MovingGameObject (velocity, gravity, friction, collision)
            ├── Player
            ├── Enemy
            ├── Projectile
            └── Platform
"""
import pygame
import util
import constants as C


class Camera:
    """
    Tracks the world-space offset applied when converting a sprite's game
    position to a screen pixel coordinate.

    Only the Player should call Camera.set(); all other sprites just read it
    via Camera.offset when they call set_rect().
    """
    offset = pygame.Vector2(0, 0)

    @classmethod
    def set(cls, x, y):
        cls.offset.x = x
        cls.offset.y = y


#Base sprite
class GameObject(pygame.sprite.Sprite):
    """
    A stationary sprite with a position, a size, a facing direction, and an
    image.  It pre-builds left/right/up/down variants of the image and masks
    so subclasses just call set_image_facing().

    All position values are in *game coordinates*:
        x grows rightward
        y grows upward
    set_rect() converts to pygame screen coordinates (y-flipped).
    """

    SCREEN_SIZE = pygame.Vector2(C.SCREEN_WIDTH, C.SCREEN_HEIGHT)

    #all sprites have these properties
    def __init__(self, position=None, size=None, facing=C.FACING_RIGHT, image_file=None):
        super().__init__()

        self.position = pygame.Vector2(position) if position else pygame.Vector2(0, 0)
        self.size = pygame.Vector2(size) if size else pygame.Vector2(C.MEDIUM_SPRITE_SIZE)
        self.facing = facing

        # Load and pre-flip / rotate the image for each facing direction
        image_file = image_file or util.get_image_path("placeholder.png")
        w, h = int(self.size.x), int(self.size.y)

        self.image_right = pygame.transform.scale(pygame.image.load(image_file), (w, h))
        self.image_left  = pygame.transform.flip(self.image_right, True, False)
        self.image_up    = pygame.transform.rotate(self.image_right, 90)
        self.image_down  = pygame.transform.rotate(self.image_right, -90)

        self.mask_right = pygame.mask.from_surface(self.image_right)
        self.mask_left  = pygame.mask.from_surface(self.image_left)
        self.mask_up    = pygame.mask.from_surface(self.image_up)
        self.mask_down  = pygame.mask.from_surface(self.image_down)

        # self.image and self.rect must exist before the first draw call
        self.image = self.image_right
        self.mask  = self.mask_right
        self.rect  = pygame.Rect((0, 0), self.size)

        # Child sprites can fire projectiles; they live in this group
        self.projectiles = pygame.sprite.Group()

        self.set_rect()
        self.set_image_facing()


    def set_rect(self):
        """Convert game-space position to screen-space."""
        sx = self.position.x - Camera.offset.x
        sy = self.SCREEN_SIZE.y - (self.position.y - Camera.offset.y)
        self.rect = pygame.Rect((sx, sy), self.size)

    def set_image_facing(self):
        #simple dictionary to store images, masks - Add to this if you want to add animations (or add an animation helper class that manages all images)
        lookup = {
            C.FACING_RIGHT: (self.image_right, self.mask_right),
            C.FACING_LEFT:  (self.image_left,  self.mask_left),
            C.FACING_UP:    (self.image_up,     self.mask_up),
            C.FACING_DOWN:  (self.image_down,   self.mask_down),
        }
        self.image, self.mask = lookup.get(self.facing, (self.image_right, self.mask_right))

    def fire_projectile(self, launch_velocity=None, rel_velocity=None, image_file=None, lifetime=C.PROJECTILE_DEFAULT_LIFETIME, floating=True):
        """
        Spawn a Projectile from this sprite's centre.

        launch_velocity : base velocity (direction is auto-flipped to match
                          self.facing if needed)
        rel_velocity    : added on top (useful for moving enemies/players)
        """
        from sprites import Projectile  # local import avoids circular issues

        velocity = pygame.Vector2(launch_velocity) if launch_velocity else pygame.Vector2(C.PROJECTILE_DEFAULT_SPEED, 0)
        rel_vel  = pygame.Vector2(rel_velocity)    if rel_velocity    else pygame.Vector2(0, 0)

        # Flip horizontal component to match the sprite's facing direction (\ is used to split boolean expressions in python)
        if (self.facing == C.FACING_LEFT and velocity.x > 0) or \
           (self.facing == C.FACING_RIGHT and velocity.x < 0):
            velocity.x *= -1

        # Spawn at the horizontal and vertical centre of the owner sprite
        size = pygame.Vector2(C.SMALL_SPRITE_SIZE)
        pos  = pygame.Vector2(self.position)
        pos.x += self.size.x / 2 - size.x / 2
        pos.y -= self.size.y / 2 - size.y / 2

        image_file = image_file or util.get_image_path("ice_block.png") #use ice_block as default
        self.projectiles.add(Projectile(pos, size, velocity + rel_vel, image_file, lifetime, floating))


    def update(self, platforms=None):
        self.set_rect()
        self.set_image_facing()
        self.projectiles.update(platforms)


#Moving sprite base
class MovingGameObject(GameObject):
    """
    Adds velocity, gravity, friction, and platform collision to GameObject.

    floating=True  -> gravity is not applied (used for enemies that hover and
                     for moving platforms)
    grounded=True  -> the sprite is standing on a platform (set automatically
                     by collision logic)
    """

    def __init__(self, position=None, size=None, velocity=None, facing=C.FACING_RIGHT, image_file=None, grounded=False, ground=None, floating=False):
        super().__init__(position, size, facing, image_file)
        self.velocity = pygame.Vector2(velocity) if velocity else pygame.Vector2(0, 0)
        self.floating = floating
        self.grounded = grounded
        self.ground   = ground
        if ground is None:
            self.grounded = False


    #Update per frame
    def update(self, platforms=None):
        self.apply_collisions(platforms)
        self.apply_friction()
        self.apply_gravity()
        self.position += self.velocity
        super().update(platforms)   # refresh rect, image, projectiles

    #Physic helper functions
    def apply_gravity(self):
        if not self.grounded and not self.floating:
            self.velocity += C.GRAVITY

    def apply_friction(self):
        if not self.grounded:
            return
        fx = C.FRICTION.x
        if self.velocity.x > 0:
            self.velocity.x = max(0.0, self.velocity.x - fx)
        elif self.velocity.x < 0:
            self.velocity.x = min(0.0, self.velocity.x + fx)

    def apply_collisions(self, platforms):
        """
        Resolve pixel-perfect collisions between this sprite and every
        platform in the group.

        Strategy
        --------
        1. Find all platforms currently overlapping this sprite.
        2. If none then clear grounded state.
        3. For each overlapping platform:
           a. Calculate a collision normal from mask overlap differences.
           b. Walk the sprite backwards along its velocity until it no longer
              overlaps.
           c. Decide: landing on top (grounded) or side/bottom bounce.

        Moving-platform support
        -----------------------
        When the sprite is riding a moving platform (self.ground is set) we
        inherit the platform's velocity each frame so the rider moves with it.
        """
        if platforms is None:
            return

        # Carry the rider along with a moving platform before collision checks
        if self.grounded and self.ground is not None and hasattr(self.ground, "velocity"):
            self.position += self.ground.velocity

        hits = pygame.sprite.spritecollide(self, platforms, False, collided=pygame.sprite.collide_mask)

        if not hits:
            self.grounded = False
            self.ground   = None
            return

        # If we're still standing on our current ground platform that's fine
        if self.ground not in hits:
            self.grounded = False
            self.ground   = None

        for other in hits:
            # Already grounded on this exact platform → side nudge only
            if self.grounded and other is self.ground:
                continue

            # Grounded but hit a *different* platform → bounce off the side
            if self.grounded and other is not self.ground:
                self.velocity.x *= -C.COLLISION_ENERGY_LOSS
                continue

            # Airborne collision: resolve via mask overlap normal 
            offset = (
                int(self.rect.left - other.rect.left),
                int(self.rect.top  - other.rect.top),
            )
            nx = (
                other.mask.overlap_area(self.mask, (offset[0] + 1, offset[1])) -
                other.mask.overlap_area(self.mask, (offset[0] - 1, offset[1]))
            )
            ny = (
                other.mask.overlap_area(self.mask, (offset[0], offset[1] + 1)) -
                other.mask.overlap_area(self.mask, (offset[0], offset[1] - 1))
            )

            # Guard against zero-velocity edge case
            if self.velocity.length() == 0:
                self.grounded = True
                self.ground   = other
                continue

            # Walk backwards along the velocity vector until clear
            step = self.velocity.normalize()
            while pygame.sprite.collide_mask(other, self):
                self.position -= step
                self.set_rect()

            # Determine landing vs. wall/ceiling hit
            # "Landing" means the collision came from above (sprite top > platform top)
            collision_pt = pygame.sprite.collide_mask(other, self)
            if collision_pt is None:
                # We backed completely clear — check if we were coming down
                if self.velocity.y <= 0:
                    # Re-seat on top of platform
                    self.position += step  # one step back onto surface
                    self.velocity.y  = 0
                    self.grounded    = True
                    self.ground      = other
                else:
                    self.velocity    *= C.COLLISION_ENERGY_LOSS
                    self.reflect_velocity(nx, ny)
            else:
                # Still overlapping after backing up — push out and land
                self.velocity.y = 0
                self.grounded   = True
                self.ground     = other

    def reflect_velocity(self, nx, ny):
        """Reflect velocity off the collision normal (wall / ceiling bounce)."""
        if nx == 0 and ny == 0:
            return
        normal = pygame.Vector2(-nx, ny).normalize()
        angle  = (-self.velocity).angle_to(normal)
        self.velocity.rotate_ip(angle * 2 + 180)
        self.velocity *= C.COLLISION_ENERGY_LOSS



class Player(MovingGameObject):
    """
    The player character.  Reads a list of currently-held keys each frame
    and moves accordingly.
    """

    def __init__(self, position=None, size=None, image_file=None, floating=False):
        size = size or pygame.Vector2(20, 30)
        image_file = image_file or util.get_image_path("penguin.png")
        super().__init__(position, size, image_file=image_file, floating=floating)
        self.alive = True
        self.recharge_projectile_count = C.PLAYER_PROJECTILE_RECHARGE  # ready to fire immediately

    def update(self, platforms=None, keys_pressed=None):
        self.recharge_projectile_count += 1
        super().update(platforms)
        if keys_pressed:
            self.handle_keys(keys_pressed)
        self.update_camera()

    def handle_keys(self, keys_pressed):
        """
        Translate currently-held key list into velocity / state changes.

        Uses direct pygame key constants to avoid chr() crashes on special keys.
        """
        for key in keys_pressed:
            if key == pygame.K_w and not self.grounded:
                # Toggle float mode (cheat / debug feature)
                self.floating  = True
                self.velocity.y = 0

            elif key == pygame.K_s:
                self.floating = False

            elif key == pygame.K_a:
                self.facing = C.FACING_LEFT
                self.velocity.x -= C.PLAYER_SPEED_INCREMENT
                self.velocity.x  = max(self.velocity.x, -C.PLAYER_MAX_SPEED)

            elif key == pygame.K_d:
                self.facing = C.FACING_RIGHT
                self.velocity.x += C.PLAYER_SPEED_INCREMENT
                self.velocity.x  = min(self.velocity.x, C.PLAYER_MAX_SPEED)

            elif key == pygame.K_SPACE and self.grounded:
                self.velocity.y = C.PLAYER_JUMP_SPEED

            elif key == pygame.K_j:
                if self.recharge_projectile_count >= C.PLAYER_PROJECTILE_RECHARGE:
                    self.fire_projectile()
                    self.recharge_projectile_count = 0

    def update_camera(self):
        """Keep the player horizontally centred on screen."""
        Camera.set(self.position.x - C.SCREEN_WIDTH / 2, 0)


#Can be used by any sprite
class Projectile(MovingGameObject):
    """
    A short-lived moving sprite fired by the player or an enemy.

    Projectiles are destroyed when they hit a platform or exceed their
    lifetime, so they do not bounce off walls the way the player does. (feel free to change this behavior)
    """

    def __init__(self, position, size, velocity, image_file, lifetime=C.PROJECTILE_DEFAULT_LIFETIME, floating=True):
        super().__init__(position, size, velocity, image_file=image_file, floating=floating)
        self.frames_alive = 0
        self.lifetime     = lifetime

    def update(self, platforms=None):
        # Destroy on platform contact instead of bouncing
        if platforms and pygame.sprite.spritecollide(self, platforms, False, collided=pygame.sprite.collide_mask):
            self.kill() #Destroy the projectile on collision
            return

        # Normal physics (gravity unless floating)
        self.apply_gravity()
        self.position += self.velocity
        super(MovingGameObject, self).update(platforms)  # skip collision resolution

        self.frames_alive += 1
        if self.frames_alive >= self.lifetime:
            self.kill()


class Enemy(MovingGameObject):
    """
    An NPC sprite driven by a list of AI components.

    Pass ai_list=[JumpingEnemyAI(), ShootingEnemyAI()] to combine behaviours.
    """

    def __init__(self, position=None, size=None, velocity=None, facing=C.FACING_RIGHT, image_file=None, grounded=False, ground=None, floating=False, ai_list=None):
        image_file = image_file or util.get_image_path("placeholder.png") #broken jpeg placeholer
        super().__init__(position, size, velocity, facing, image_file, grounded, ground, floating)

        from components import StillEnemyAI
        self.ai_list = ai_list if ai_list is not None else [StillEnemyAI()]

    def update(self, platforms=None):
        for ai in self.ai_list:
            ai.update(self)
        super().update(platforms)


class Platform(MovingGameObject):
    """
    A solid surface sprites can stand on.

    Static platforms: leave mover_list empty (or don't pass one).
    Moving platforms: pass mover_list=[HorizontalMover(), ...] from components.py.

    Platforms are floating=True by default so gravity does not pull them down.
    """

    def __init__(self, position=None, size=None, image_file=None, mover_list=None):
        image_file = image_file or util.get_image_path("ice_platform.png")
        super().__init__(position, size, image_file=image_file, floating=True)
        self.mover_list = mover_list or []

    def update(self, platforms=None):
        # Run any mover components
        for mover in self.mover_list:
            mover.update(self)

        # Moving platforms update their own position; static ones skip physics
        if self.mover_list:
            self.position += self.velocity

        # Refresh rect and image (skip collision logic — platforms don't collide)
        self.set_rect()
        self.set_image_facing()
        self.projectiles.update(platforms)