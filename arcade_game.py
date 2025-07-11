import time
from enum import Enum

import arcade

# general settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Platformer"
GRID_PIXEL_SIZE = 18

RIGHT_FACING = 0
LEFT_FACING = 1

# player settings
PLAYER_MOVEMENT_SPEED = 3.5
PLAYER_JUMP_SPEED = 15
CHARACTER_SCALING = 0.4
GRAVITY = 1.2
TILE_SCALING = 1


respawn_points = {
    1: [3 * GRID_PIXEL_SIZE, 12 * GRID_PIXEL_SIZE],
    2: [3 * GRID_PIXEL_SIZE, 4 * GRID_PIXEL_SIZE],
}


class layers(Enum):
    # Layer Names from our TileMap
    PLATFORMS = "platforms"
    COINS = "coins"
    BACKGROUND = "background"
    GROUND = "ground"
    TRAPS = "traps"
    BUTTONS = "buttons"
    PORTAL_TRAP = "portal_trap"
    PORTALS = "portals"
    LASERS = "lasers"
    BULLETS = "bullets"
    MOVING_TRAPS = "moving_traps"


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]


class Entity(arcade.Sprite):
    def __init__(self, name_folder, name_file):
        super().__init__()

        self.scale = CHARACTER_SCALING
        main_path = f":resources:images/animated_characters/{name_folder}/{name_file}"

        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.texture = self.idle_texture_pair[0]


class PlayerCharacter(Entity):
    """Player Sprite"""

    def __init__(self):
        # Set up parent class
        super().__init__("male_person", "malePerson")


class GameView(arcade.View):
    """
    Main application class.
    """

    def __init__(self):
        # Level
        self.level = 1
        super().__init__()
        self.camera = None
        self.gui_camera = None
        self.physics_engine = None
        self.platforms_to_fall = {}

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_needs_reset = False
        self.shoot_pressed = False
        self.score = 0
        self.hp = 3
        self.invulnerable_timer = 0
        self.boost_time_start = 0

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        self.camera = arcade.Camera(self.window.width, self.window.height)

        self.gui_camera = arcade.Camera(self.window.width, self.window.height)
        self.platfotms_to_fall = {}

        map_name = f"tiles/Map{self.level}.json"

        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING)  # , layer_options)
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.can_shoot = True
        self.shoot_timer = 0
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = respawn_points[self.level][0]
        self.player_sprite.center_y = respawn_points[self.level][1]
        self.scene.add_sprite("Player", self.player_sprite)

        if self.level == 2:
            walls = [
                self.scene["ground"],
                self.scene["platforms"],
                self.scene["failing_platforms"],
            ]
        else:
            walls = [
                self.scene["ground"],
                self.scene["platforms"],
            ]

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=walls
        )

    def process_keychange(self):
        """
        Called when we change a key up/down or we move on/off a ladder.
        """

        # Process up/down
        if self.up_pressed and not self.down_pressed:
            if (
                self.physics_engine.can_jump(y_distance=10)
                and not self.jump_needs_reset
            ):
                if time.time() - self.boost_time_start < 3:
                    jump_speed_multiplier = 2
                else:
                    jump_speed_multiplier = 1

                self.player_sprite.change_y = PLAYER_JUMP_SPEED * jump_speed_multiplier
                self.jump_needs_reset = True

        # Process left/right
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True

        self.process_keychange()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
            self.jump_needs_reset = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

        self.process_keychange()

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )

        # Don't let camera travel past 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)

    def on_update(self, delta_time):
        """Movement and game logic"""

        # Move the player with the physics engine
        self.physics_engine.update()

        if (
            self.player_sprite.center_x >= self.end_of_map
            or self.player_sprite.center_x <= 0
        ):
            self.setup()

        self.center_camera_to_player()

        coin_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["coins"]
        )

        for coin in coin_hit_list:
            # Remove the coin
            coin.remove_from_sprite_lists()
            # Play a sound
            self.score += 1
        if self.level == 2:
            boost_list = arcade.check_for_collision_with_list(
                self.player_sprite, self.scene["boost"]
            )
            if boost_list:
                self.boost_time_start = time.time()
                for boost in boost_list:
                    # Remove the coin
                    boost.remove_from_sprite_lists()

        if self.level == 1:
            if arcade.check_for_collision_with_list(
                self.player_sprite, self.scene[layers.PORTAL_TRAP.value]
            ):
                self.player_sprite.change_x = 0
                self.player_sprite.change_y = 0
                self.player_sprite.center_x = 44 * GRID_PIXEL_SIZE
                self.player_sprite.center_y = 6 * GRID_PIXEL_SIZE

        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[layers.PORTALS.value]
        ):
            self.level += 1

            self.setup()

        if self.can_shoot:
            for laser in self.scene[layers.LASERS.value]:
                bullet = arcade.Sprite(
                    ":resources:images/space_shooter/laserBlue01.png"
                )

                bullet.change_x = -12

                bullet.center_x = laser.center_x
                bullet.center_y = laser.center_y

                self.scene.add_sprite(layers.BULLETS.value, bullet)

            self.can_shoot = False
        else:
            self.shoot_timer += 1
            if self.shoot_timer == 100:
                self.can_shoot = True
                self.shoot_timer = 0

        if self.level == 1:
            self.scene.update_animation(delta_time, [layers.MOVING_TRAPS.value])
            self.scene.update([layers.MOVING_TRAPS.value])
        if self.level == 2:
            self.scene.update([layers.BULLETS.value])
            self.scene.update(["failing_platforms"])
        if self.level == 1:
            if arcade.check_for_collision_with_list(
                self.player_sprite, self.scene[layers.TRAPS.value]
            ):
                if time.time() - self.invulnerable_timer < 2:
                    pass
                else:
                    self.hp -= 1
                    self.invulnerable_timer = time.time()
        if self.level == 2:
            if arcade.check_for_collision_with_list(
                self.player_sprite, self.scene[layers.BULLETS.value]
            ):
                bullet_hit_list = arcade.check_for_collision_with_list(
                    self.player_sprite, self.scene["bullets"]
                )
                for bullet in bullet_hit_list:
                    bullet.remove_from_sprite_lists()
                self.hp -= 1

        if self.level == 2:
            l = []
            platforms_hit_list = arcade.check_for_collision_with_list(
                self.player_sprite, self.scene["failing_platforms"]
            )
            for i in platforms_hit_list:
                if i._properties["number"] not in self.platforms_to_fall:
                    self.platforms_to_fall[i._properties["number"]] = time.time()
            for i in self.scene["failing_platforms"]:
                if (
                    i._properties["number"] in self.platforms_to_fall
                    and time.time()
                    > self.platforms_to_fall[i._properties["number"]] + 3
                ):
                    l.append(i)
            for i in l:
                if i in self.scene["failing_platforms"]:
                    self.scene["failing_platforms"].remove(i)

        if self.level == 1:
            button_hit_list = arcade.check_for_collision_with_list(
                self.player_sprite, self.scene["buttons"]
            )
            if button_hit_list != []:
                for moving_sprite in self.scene[layers.MOVING_TRAPS.value]:
                    if (
                        moving_sprite.boundary_top
                        # and moving_sprite.change_y > 0
                        and moving_sprite.top > moving_sprite.boundary_top
                    ):
                        moving_sprite.change_y = 0
                    elif (
                        moving_sprite.boundary_bottom
                        and moving_sprite.change_y < 0
                        and moving_sprite.bottom < moving_sprite.boundary_bottom
                    ):
                        moving_sprite.change_y = 0
                    elif moving_sprite.change_y == 0:
                        moving_sprite.change_y = 1

            if button_hit_list == []:
                for moving_sprite in self.scene[layers.MOVING_TRAPS.value]:
                    if (
                        moving_sprite.boundary_bottom
                        # and moving_sprite.change_y > 0
                        and moving_sprite.bottom < moving_sprite.boundary_bottom
                    ):
                        moving_sprite.change_y = 0
                    elif (
                        moving_sprite.boundary_top
                        and moving_sprite.change_y > 0
                        and moving_sprite.top > moving_sprite.boundary_top
                    ):
                        moving_sprite.change_y = 0
                    elif moving_sprite.change_y == 0:
                        moving_sprite.change_y = -1

            if arcade.check_for_collision_with_list(
                self.player_sprite, self.scene[layers.MOVING_TRAPS.value]
            ):
                if time.time() - self.invulnerable_timer < 2:
                    pass
                else:
                    self.hp -= 1
                    self.invulnerable_timer = time.time()
        if self.hp == 0:
            self.level = 1
            self.score = 0
            self.hp = 3
            self.setup()

    def on_draw(self):
        """Render the screen."""

        self.clear()
        # Activate our Camera
        self.camera.use()
        # Draw our Scene
        self.scene.draw()

        self.gui_camera.use()

        score_text = f"Score: {self.score}"
        arcade.draw_text(
            score_text,
            10,
            10,
            arcade.csscolor.WHITE,
            18,
        )
        score_text = f"HP: {self.hp}"
        arcade.draw_text(
            score_text,
            SCREEN_WIDTH - 680,
            10,
            arcade.csscolor.WHITE,
            18,
        )

    def on_show_view(self):
        self.setup()


def main():
    """Main function"""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_view = GameView()
    window.show_view(game_view)

    arcade.run()


if __name__ == "__main__":
    main()
