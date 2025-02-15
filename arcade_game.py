import json
from enum import Enum
import arcade
from arcade.arcade_types import TiledObject

# general settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Platformer"
GRID_PIXEL_SIZE = 18

RIGHT_FACING = 0
LEFT_FACING = 1

# player settings
PLAYER_MOVEMENT_SPEED = 5
PLAYER_START_X = 60
PLAYER_START_Y = 330
PLAYER_JUMP_SPEED = 15
CHARACTER_SCALING = 0.4
GRAVITY = 1
TILE_SCALING = 1


class layers(Enum):
    # Layer Names from our TileMap
    PLATFORMS = "platforms"
    COINS = "coins"
    BACKGROUND = "background"
    GROUND = "ground"
    TRAPS = "traps"
    BUTTONS = "buttons"


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

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_needs_reset = False
        self.shoot_pressed = False
        self.score = 0

        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        self.camera = arcade.Camera(self.window.width, self.window.height)

        self.gui_camera = arcade.Camera(self.window.width, self.window.height)

        map_name = f"tiles/Map2.json"

        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING)  # , layer_options)
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite("Player", self.player_sprite)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            gravity_constant=GRAVITY,
            walls=[self.scene["ground"], self.scene["platforms"]],
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
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
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
