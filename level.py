"""
level.py
--------
GameLevel owns all the sprites for a single level and runs collision logic
each frame.

Edit build_level() to design your own layout.  The helper
methods make_platform() and make_enemy() give you a readable shorthand.
"""
import pygame
import util
import constants as C
from sprites  import Player, Enemy, Platform, Camera
from components import JumpingEnemyAI, ShootingEnemyAI, PatrolEnemyAI, HorizontalMover, VerticalMover



class GameLevel:

    def __init__(self, screen, player_spawn=None):
        self.screen = screen
        self.background = pygame.transform.scale(pygame.image.load(util.get_image_path("ice_background.jpeg")), screen.get_size())

        # Sprite groups
        self.platforms      = pygame.sprite.Group()
        self.enemy_objects  = pygame.sprite.Group()
        self.player_objects = pygame.sprite.GroupSingle()

        # Spawn player
        spawn = pygame.Vector2(player_spawn) if player_spawn else pygame.Vector2(100, 200)
        self.player = Player(spawn)
        self.player_objects.add(self.player)

        self.build_level()


    def build_level(self):
        """
        Define all platforms and enemies here.
        Use make_platform() and make_enemy() for readability.

        This is your canvas — change everything below!
        """
        sw = self.screen.get_width()    # 800
        sh = self.screen.get_height()   # 600

        #--Platforms--
        # Ground (spans well beyond the screen on both sides)
        self.platforms.add(self.make_platform(x=-sw, y=20, w=sw * 10, h=50))

        # Static platforms
        self.platforms.add(self.make_platform(x=200, y=210, w=sw, h=30))

        # Moving platforms
        self.platforms.add(self.make_platform(x=400, y=410, w=sw // 2, h=30, movers=[HorizontalMover(speed=2, move_range=250)]))
        self.platforms.add(self.make_platform(x=100, y=320, w=sw // 3, h=30, movers=[VerticalMover(speed=2, move_range=150)]))

        #--Enemies--
        # A hovering still enemy
        self.enemy_objects.add(self.make_enemy(x=600, y=120, floating=True))

        # A jumping enemy 
        self.enemy_objects.add(self.make_enemy(x=300, y=270, image="leopard_seal.png", size=C.LARGE_SPRITE_SIZE, ai_list=[JumpingEnemyAI(jump_height=20, frames_to_pause=20)]))

        # A patrolling enemy that also shoots
        self.enemy_objects.add(self.make_enemy(x=500, y=270, image="leopard_seal.png", facing=C.FACING_LEFT, 
            ai_list=[PatrolEnemyAI(speed=2, patrol_range=200), ShootingEnemyAI(launch_velocity=pygame.Vector2(8, 0), recharge_time=60)]))


    #Helper methods for making game objects
    def make_platform(self, x, y, w, h, image="ice_platform.png", movers=None):
        return Platform(position=pygame.Vector2(x, y), size=pygame.Vector2(w, h), image_file=util.get_image_path(image), mover_list=movers or [])

    def make_enemy(self, x, y, image="placeholder.png", size=None, facing=C.FACING_RIGHT, floating=False, ai_list=None):
        return Enemy(position=pygame.Vector2(x, y), size=pygame.Vector2(size) if size else pygame.Vector2(C.MEDIUM_SPRITE_SIZE),
            facing=facing, image_file=util.get_image_path(image), floating=floating, ai_list=ai_list)

    #Per frame update of level -> apply physics and checks collisions
    def update(self, keys_pressed):
        # Physics
        self.platforms.update()
        self.player_objects.update(self.platforms, keys_pressed)
        self.enemy_objects.update(self.platforms)

        # Collisions
        self.check_collisions()

    def check_collisions(self):
        player = self.player

        # Fall off the bottom of the world
        if player.position.y <= -200:
            player.alive = False
            return

        # Player touches an enemy directly
        if pygame.sprite.spritecollide(player, self.enemy_objects, False, collided=pygame.sprite.collide_mask):
            player.alive = False #Player ties (could change this to take damage instead)
            return

        # Player hit by an enemy projectile
        for enemy in self.enemy_objects:
            if pygame.sprite.spritecollide(player, enemy.projectiles, True, collided=pygame.sprite.collide_mask):
                player.alive = False
                return

        # Player projectile destroys enemy
        pygame.sprite.groupcollide(player.projectiles, self.enemy_objects, True, True, collided=pygame.sprite.collide_mask)

        # Player projectile cancels enemy projectile
        for enemy in self.enemy_objects:
            pygame.sprite.groupcollide(player.projectiles, enemy.projectiles, True, True, collided=pygame.sprite.collide_mask)


    #Drawing the level - draw all the game components from the sprite groups
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.platforms.draw(self.screen)
        self.player_objects.draw(self.screen)
        self.player.projectiles.draw(self.screen)
        self.enemy_objects.draw(self.screen)
        for enemy in self.enemy_objects:
            enemy.projectiles.draw(self.screen)