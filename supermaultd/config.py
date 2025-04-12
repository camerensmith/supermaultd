import os

# Window settings
WINDOWED_FULLSCREEN = True # Set to True for borderless fullscreen
WIDTH = 1280  # Used if WINDOWED_FULLSCREEN is False
HEIGHT = 720 # Used if WINDOWED_FULLSCREEN is False
FPS = 60

# Layout settings
ENEMY_PREVIEW_HEIGHT = 64 # Height for bottom enemy preview area
UI_PANEL_WIDTH_PERCENT = 0.40 # Panel takes 40% of the right side
UI_PANEL_PADDING = 10 # Padding around panel / between grid/panel

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)

# More Colors
LIGHT_GRAY = (211, 211, 211)
DARK_GRAY = (105, 105, 105)
CHARCOAL = (54, 69, 79)
BROWN = (165, 42, 42)
SADDLE_BROWN = (139, 69, 19)
CHOCOLATE = (210, 105, 30)
PURPLE = (128, 0, 128)
VIOLET = (238, 130, 238)
INDIGO = (75, 0, 130)
PINK = (255, 192, 203)
HOT_PINK = (255, 105, 180)
DEEP_PINK = (255, 20, 147)
LIME_GREEN = (50, 205, 50)
FOREST_GREEN = (34, 139, 34)
OLIVE_DRAB = (107, 142, 35)
TEAL = (0, 128, 128)
STEEL_BLUE = (70, 130, 180)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
SKY_BLUE = (135, 206, 235)

# Game settings
GRID_SIZE = 32  # Size of each grid cell in pixels
STARTING_MONEY = 10000
STARTING_LIVES = 10
RESTRICTED_TOWER_AREA_HEIGHT = 1  # Number of rows at top and bottom where towers cannot be placed
RESTRICTED_TOWER_AREA_WIDTH = 1   # Number of columns at left and right where towers cannot be placed

# Spawn area settings
SPAWN_AREA_WIDTH = 3  # Width of spawn area in grid cells
SPAWN_AREA_HEIGHT = 2  # Height of spawn area in grid cells
SPAWN_AREA_COLOR = (128, 0, 128)  # Purple color for spawn area

# Objective area settings
OBJECTIVE_AREA_WIDTH = 3  # Width of objective area in grid cells
OBJECTIVE_AREA_HEIGHT = 1  # Height of objective area in grid cells
OBJECTIVE_AREA_COLOR = (255, 0, 0)  # Red color for objective area

# Path settings
ASSETS_DIR = "assets"
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
ENEMY_IMAGES_DIR = os.path.join(ASSETS_DIR, "enemies") # Add path for enemy sprites
TOWER_IMAGES_DIR = os.path.join(IMAGES_DIR, "towers") # Specify tower image path

# Animation Constants
BLOOD_SPLATTER_FADE_DURATION = 0.75 # Seconds for the splatter to fade out
BLOOD_SPLATTER_HOLD_DURATION = 0.2 # Seconds to keep splatter fully visible before fading

# --- Enemy Data --- 
ENEMY_DATA = {
    "dust_mite": { 
        "health": 60,
        "speed": 5,
        "value": 1, "armor_value": 0,
        "armor_type": "unarmored",
        "type": "air"
    },
    "village_peasant": { #wave 1, 25 units
        "health": 150,
        "speed": 2.0, 
        "value": 1, "armor_value": 1,
        "armor_type": "light",
        "type": "ground"
    },
    "heavily_armored_piglet": { #wave 4, 25 units
        "health": 222,
        "speed": 2.4,
        "value": 1, "armor_value": 5,
        "armor_type": "heavy",
        "type": "ground"
    },
    "pixie": {
        "health": 70,
        "speed": 3.0,
        "value": 2,
        "armor_type": "ethereal", 
        "type": "air"
    },
    "fruit_crab": { #wave 3, 25 units
        "health": 310,
        "speed": 1.6,
        "value": 1, "armor_value": 7,
        "armor_type": "medium",
        "type": "ground"
    },
    "spectre": {
        "health": 80, 
        "speed": 2.5,
        "value": 12,
        "armor_type": "ethereal",
        "type": "ground",
    },
    "imp": {
        "health": 90,
        "speed": 2.9,
        "value": 8,
        "armor_type": "unarmored",
        "type": "ground"
    },
    "frost_imp": {
        "health": 100,
        "speed": 2.9,
        "value": 10,
        "armor_type": "ethereal", 
        "type": "ground"
    },
    "witch_doctor": { #wave 11, 25 units, 55 gold for wave completion
        "health": 1500,
        "speed": 3.2,
        "value": 9, "armor_value": 10,
        "armor_type": "unarmored",
        "type": "ground"
    },
    "gnoll": { #wave 12, 25 units, 60 gold for wave completion
        "health": 120,
        "speed": 2.0, 
        "value": 8,
        "armor_type": "medium",
        "type": "ground",
    },
    "magus": {
        "health": 120,
        "speed": 1.8,
        "value": 20,
        "armor_type": "magic_resistant",
        "type": "ground"
    },
    "skeleton_warrior": {
        "health": 130,
        "speed": 1.5,
        "value": 12,
        "armor_type": "light", # Could be medium too
        "type": "ground"
    },
    "fire_elemental": {
        "health": 150,
        "speed": 2.2,
        "value": 18,
        "armor_type": "ethereal", 
        "type": "ground"
    },
    "vampire": {
        "health": 150,
        "speed": 3.1,
        "value": 18,
        "armor_type": "light",
        "type": "ground"
    },
    "iron_golem": {
        "health": 160,
        "speed": 2.1,
        "value": 15,
        "armor_type": "fortified",
        "type": "ground"
    },
    "dark_elf": {
        "health": 170,
        "speed": 2.2,
        "value": 17,
        "armor_type": "medium",
        "type": "ground"
    },
    "mudrunner": { # wave 2, 25 units
        "health": 120,
        "speed": 1.8,
        "value": 14, "armor_value": 3,
        "armor_type": "medium",
        "type": "ground"
    },
    "hired_goon": {
        "health": 180,
        "speed": 1.8,
        "value": 15,
        "armor_type": "medium",
        "type": "ground"
    },
    "centaur_strider": {
        "health": 190,
        "speed": 2.7,
        "value": 18,
        "armor_type": "light",
        "type": "ground"
    },
    "soldier": {
        "health": 200, 
        "speed": 1.5, 
        "value": 15,
        "armor_type": "medium",
        "type": "ground",
    },
    "wyvern": { #wave 5, 15 units
        "health": 200,
        "speed": 2.8,
        "value": 1, "armor_value": 8,
        "armor_type": "light",
        "type": "air" # Flying
    },
    "disgusting_ooze": {
        "health": 200,
        "speed": 1.0, # Slow ooze
        "value": 15,
        "armor_type": "magic_resistant",
        "type": "ground"
    },
    "orc": {
        "health": 220,
        "speed": 1.7,
        "value": 16,
        "armor_type": "medium",
        "type": "ground"
    },
    "scarlet_rider": {
        "health": 220,
        "speed": 2.9,
        "value": 20,
        "armor_type": "light",
        "type": "ground"
    },
    "fel_orc": {
        "health": 250,
        "speed": 1.9,
        "value": 25,
        "armor_type": "normal",
        "type": "ground"
    },
    "dragon_whelp": {
        "health": 250,
        "speed": 2.4,
        "value": 28,
        "armor_type": "medium",
        "type": "air"
    },
    "cyborg": {
        "health": 280,
        "speed": 1.6,
        "value": 22,
        "armor_type": "medium",
        "type": "ground"
    },
    "granite_golem": {
        "health": 300,
        "speed": 1.5,
        "value": 25,
        "armor_type": "magic_resistant",
        "type": "ground"
    },
    "bloodfist_ogre": { #wave 9, 50 units, 50 gold for wave completion
        "health": 950,
        "speed": 2,
        "value": 1, "armor_value": 9,
        "armor_type": "heavy",
        "type": "ground"
    },
    "cenobite": { 
        "health": 400,
        "speed": 1.4,
        "value": 35,
        "armor_type": "ethereal",
        "type": "ground"
    },
    "black_guard": {
        "health": 450,
        "speed": 1.6,
        "value": 40,
        "armor_type": "heavy",
        "type": "ground"
    },
    "war_machine": {
        "health": 500,
        "speed": 0.8,
        "value": 30,
        "armor_type": "fortified",
        "type": "ground"
    },
    "hill_troll": {
        "health": 600,
        "speed": 1.1,
        "value": 38,
        "armor_type": "unarmored",
        "type": "ground"
    },
    "green_dragon": {
        "health": 700,
        "speed": 2.0,
        "value": 60,
        "armor_type": "heavy",
        "type": "air"
    },
    "doomlord": {
        "health": 800,
        "speed": 1.0,
        "value": 50,
        "armor_type": "medium",
        "type": "ground"
    },
    "crazed_treant": {
        "health": 900,
        "speed": 0.7,
        "value": 45,
        "armor_type": "light",
        "type": "ground"
    },
    "lord_supermaul": {
        "health": 5000, # Boss
        "speed": 1.0,
        "value": 250, # Big reward
        "armor_type": "normal",
        "type": "ground"
    },
    "red_dragon": {
        "health": 650,
        "speed": 2.2,
        "value": 55,
        "armor_type": "unarmored",
        "type": "air"
    },
    "blue_dragon": {
        "health": 650,
        "speed": 2.0,
        "value": 65,
        "armor_type": "magic_resistant",
        "type": "air"
    },
    # --- New Enemies ---
    "zombie": {
        "health": 200,
        "speed": 1.0,
        "value": 5,
        "armor_type": "unarmored",
        "type": "ground"
    },
    "wild_boar": { #wave 6, 25 units, 38 gold for wave completion
        "health": 440,
        "speed": 3.0,
        "value": 10, "armor_value": 8,
        "armor_type": "light",
        "type": "ground"
    },
    "tusken_fighter": {
        "health": 180,
        "speed": 1.8,
        "value": 15,
        "armor_type": "medium",
        "type": "ground"
    },
    "wendigo": {
        "health": 250,
        "speed": 3.5,
        "value": 25,
        "armor_type": "magic_resistant",
        "type": "ground"
    },
    "wisp": {
        "health": 40,
        "speed": 4.0,
        "value": 8,
        "armor_type": "ethereal",
        "type": "ground"
    },
    "battlemech": { #wave 10, 25 units, 53 gold for wave completion
        "name": "Battlemech", "health": 1540, "speed": 0.8, "value": 2, "armor_value": 24,
        "armor_type": "fortified", "type": "ground"
    },
    "spaceship": {
        "name": "Spaceship", "health": 600, "speed": 2.5, "value": 50, 
        "armor_type": "fortified", "type": "air"
    },
    "crazy_panda": {
        "name": "Crazy Panda", "health": 220, "speed": 2.0, "value": 18, 
        "armor_type": "medium", "type": "ground" 
    },
    "mutant_roach": { #wave 7, 25 units, 40 gold for wave completion
        "name": "Mutant Roach", "health": 440, "speed": 2, "value": 2,  "armor_value": 20,
        "armor_type": "fortified", "type": "ground" 
    },
    "evil_clown": { #wave 8, 25 units, 48 gold for wave completion
        "name": "Evil Clown", "health": 200, "speed": 3.5, "value": 22, "armor_value": 8,
        "armor_type": "unarmored", "type": "ground"
    }
}