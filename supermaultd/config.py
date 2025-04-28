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
STARTING_MONEY = 100
STARTING_LIVES = 20
STARTING_MONEY_ADVANCED = 100
STARTING_LIVES_ADVANCED = 10
RESTRICTED_TOWER_AREA_HEIGHT = 1  # Number of rows at top and bottom where towers cannot be placed
RESTRICTED_TOWER_AREA_WIDTH = 1   # Number of columns at left and right where towers cannot be placed

# Spawn area settings
SPAWN_AREA_WIDTH = 2  # Width of spawn area in grid cells
SPAWN_AREA_HEIGHT = 1  # Height of spawn area in grid cells
SPAWN_AREA_COLOR = (105, 105, 105)  # Purple color for spawn area

# Objective area settings
OBJECTIVE_AREA_WIDTH = 2  # Width of objective area in grid cells
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
    "imp": {  # these will be a bonus fun wave
        "health": 5000,
        "speed": 5,
        "value": 1, "armor_value": 5,
        "armor_type": "Unarmored",
        "type": "air"
    },
    "ratling": { #wave 1, 25 units
        "health": 54,
        "speed": 1, 
        "value": 1, "armor_value": 0,
        "armor_type": "Unarmored",
        "type": "ground"
    },
    "mudrunner": {  
        "health": 110,
        "speed": 1.0,
        "value": 1, "armor_value": 3,
        "armor_type": "Light",
        "type": "ground"
    },
    "quillpig": {  
        "health": 308,
        "speed": 0.7,
        "value": 1, "armor_value": 7,
        "armor_type": "Light",
        "type": "ground"
    },
    "bugbear": {  
        "health": 264,
        "speed": 1,
        "value": 1,
        "armor_type": "Heavy", 
        "armor_value": 5,
        "type": "ground"
    },
    "red_flyer": {  #advanced only, value increases 2
        "health": 440,
        "speed": 0.3,
        "value": 1, "armor_value": 6,
        "armor_type": "Light",
        "type": "air"
    },
    "redrum": { #classic only, value increases 2
        "health": 482,
        "speed": 0.8,
        "value": 1,
        "armor_type": "Light",
        "armor_value": 6,
        "type": "ground"
    },
    "brawler": {
        "health": 440, 
        "speed": 0.5,
        "value": 2,
        "armor_type": "Fortified",
        "armor_value": 20,
        "type": "ground",
    },
    "mongoose": {
        "health": 660,
        "speed": 1.2,
        "value": 2,
        "armor_type": "Unarmored",
        "armor_value": 11,
        "type": "ground"
    },
    "manboar": {
        "health": 1000,
        "speed": 1.1,
        "value": 2,
        "armor_type": "Heavy", 
        "armor_value": 10,
        "type": "ground"
    },
    "groundhogger": {
        "health": 1340,
        "speed": 0.4,
        "value": 2, "armor_value": 24,
        "armor_type": "Fortified",
        "type": "ground"
    },
    "djinn": { 
        "health": 1400,
        "speed": 1.3, 
        "value": 2,
        "armor_type": "Magic_Resistant",
        "armor_value": 10,
        "type": "ground",
    },
    "gnoll_berserker": {
        "health": 1980,
        "speed": 1.4,
        "value": 2,
        "armor_type": "Medium",
        "armor_value": 8,
        "type": "ground"
    },
    "fire_elemental": {
        "health": 8800,
        "speed": 0.1,
        "value": 2,
        "armor_type": "Ethereal", 
        "type": "ground"
    },
    "green_dragon": { #advanced only, gold increase after wave
        "health": 2000,
        "speed": 0.4,
        "value": 2,
        "armor_type": "Unarmored", 
        "armor_value": 15,
        "type": "air"
    },
    "terrorizer": { #classic only, value increases 2
        "health": 2000,
        "speed": 1.3,
        "value": 2,
        "armor_type": "Unarmored",
        "armor_value": 9,
        "type": "ground"
    },
    "bruiser": {
        "health": 3200,
        "speed": 1,
        "value": 3,
        "armor_type": "Heavy",
        "armor_value": 15,
        "type": "ground"
    },
    "goblin_renegade": {
        "health": 3600,
        "speed": 1.5,
        "value": 3,
        "armor_type": "Medium",
        "armor_value": 10,
        "type": "ground"
    },
    "goon": {
        "health": 5000,
        "speed": 0.4,
        "value": 3,
        "armor_type": "Fortified",
        "armor_value": 30,
        "type": "ground"
    },
    "war_turtle": { 
        "health": 33000,
        "speed": 0.3,
        "value": 3, "armor_value": 0,
        "armor_type": "Light",
        "type": "ground"
    },
    "gremlin": { #gold increase
        "health": 5000,
        "speed": 1.5,
        "value": 3,
        "armor_type": "Medium",
        "armor_value": 22,
        "type": "ground"
    },
    "witch_doctor": {
        "health": 6000,
        "speed": 1.2,
        "value": 4,
        "armor_type": "Heavy",
        "armor_value": 20,
        "type": "ground"
    },
    "spectral_dog": {
        "health": 1300, 
        "speed": 0.6, 
        "value": 4,
        "armor_type": "Ethereal",
        "armor_value": 28,
        "type": "ground",
    },
    "polywog": {
        "health": 9000,
        "speed": 1.4, 
        "value": 4,
        "armor_type": "Medium",
        "armor_value": 11,
        "type": "ground"
    },
    "blue_dragon": { # advanced only, gold increase after wave
        "health": 4600,
        "speed": 0.5,
        "value": 4, "armor_value": 30,
        "armor_type": "Unarmored",
        "type": "air" # Flying
    },
    "glinter": { #classic only, value increases 1
        "health": 4600,
        "speed": 0.9,
        "value": 4,
        "armor_type": "Unarmored",
        "armor_value": 30,
        "type": "ground"
    },
    "hexer": {
        "health": 13600,
        "speed": 0.4,
        "value": 5,
        "armor_type": "Light",
        "armor_value": 35,
        "type": "ground"
    },
    "satyr": {
        "health": 12000,
        "speed": 1.8,
        "value": 5,
        "armor_type": "Unarmored",
        "armor_value": 35,
        "type": "ground"
    },
    "hellasaur": {
        "health": 75000,
        "speed": 0.2,
        "value": 5,
        "armor_type": "Medium",
        "armor_value": 0,
        "type": "ground"
    },
    "hill_troll": {
        "health": 14000,
        "speed": 1.6,
        "value": 5,
        "armor_type": "Heavy",
        "armor_value": 50,
        "type": "ground"
    },
    "crone": {
        "health": 7000,
        "speed": 1.6,
        "value": 5,
        "armor_type": "Unarmored",
        "armor_value": 38,
        "type": "air"
    },
    "scarlet_knight": {
        "health": 16000,
        "speed": 1.5,
        "value": 5,
        "armor_type": "Fortified",
        "armor_value": 50,
        "type": "ground"
    },
    "ice_demon": {
        "health": 37000,
        "speed": 1.5,
        "value": 5, "armor_value": 9,
        "armor_type": "Magic_Resistant",
        "armor_value": 13,
        "type": "ground"
    },
    "black_bear": {
        "health": 23300,
        "speed": 2,
        "value": 5,
        "armor_type": "Unarmored",
        "armor_value": 0,
        "type": "air"
    },
    "orc": {
        "health": 120000,
        "speed": 0.6,
        "value": 5,
        "armor_type": "Light",
        "armor_value": 0,
        "type": "air"
    },
    "tusken_fighter": {
        "health": 73000,
        "speed": 1.3,
        "value": 6,
        "armor_type": "Unarmored",
        "armor_value": 0,
        "type": "ground"
    },
    "spike_lizard": {
        "health": 67875,
        "speed": 1.5,
        "value": 6,
        "armor_type": "Heavy",
        "armor_value": 23,
        "type": "ground"
    },
    "swamp_monster": {
        "health": 95575,
        "speed": 1,
        "value": 6,
        "armor_type": "Medium",
        "armor_value": 35,
        "type": "ground"
    },
    "cave_troll": {
        "health": 145000,
        "speed": 1,
        "value": 6,
        "armor_type": "Magic_Resistant",
        "armor_value": 28,
        "type": "ground"
    },
    "wendigo": {
        "health": 200000,
        "speed": 0.6,
        "value": 6,
        "armor_type": "Unarmored",
        "armor_value": 0,
        "type": "ground"
    },
    "captain": {
        "health": 88000,
        "speed": 1,
        "value": 6,
        "armor_type": "Heavy",
        "armor_value": 50,
        "type": "ground"
    },
    "lord_supermaul": {
        "health": 255000, # Boss
        "speed": 0.7,
        "value": 250, # Big reward
        "armor_type": "Medium",
        "armor_value": 100,
        "type": "ground"
    },

    #additive
"turtlesaur": {
    "health": 133700,
    "speed": 1,
    "value": 7,
    "armor_type": "Fortified",
    "armor_value": 60,
    "type": "ground"
},
"beasttamer": {
    "health": 80000,
    "speed": 1.0,
    "value": 7,
    "armor_type": "Light",
    "armor_value": 50,
    "type": "ground"
},
"bladeodon": {
    "health": 135000,
    "speed": 0.8,
    "value": 7,
    "armor_type": "Medium",
    "armor_value": 85,
    "type": "ground"
},
"carnifex": {
    "health": 180000,
    "speed": 0.6,
    "value": 7,
    "armor_type": "Ice",
    "armor_value": 100,
    "type": "ground"
},
"curseborn": {
    "health": 200000,
    "speed": 1.0,
    "value": 7,
    "armor_type": "Dark",
    "armor_value": 120,
    "type": "ground"
},
"darkjaw": {
    "health": 250000,
    "speed": 1.2,
    "value": 7,
    "armor_type": "Magic_Resistant",
    "armor_value": 130,
    "type": "ground"
},
"dragon_guard": {
    "health": 300000,
    "speed": 0.5,
    "value": 7,
    "armor_type": "Heavy",
    "armor_value": 150,
    "type": "ground"
},
"etherhunter": {
    "health": 120000,
    "speed": 1.1,
    "value": 7,
    "armor_type": "Ethereal",
    "armor_value": 80,
    "type": "ground"
},
"gremlin_king": {
    "health": 160000,
    "speed": 1.3,
    "value": 7,
    "armor_type": "Unarmored",
    "armor_value": 120,
    "type": "ground"
},
"grutto_guard": {
    "health": 180000,
    "speed": 1.0,
    "value": 7,
    "armor_type": "Ice",
    "armor_value": 150,
    "type": "ground"
},
"legionnaire": {
    "health": 210000,
    "speed": 1.2,
    "value": 7,
    "armor_type": "Medium",
    "armor_value": 100,
    "type": "ground"
},
"lieutenant_krug": {
    "health": 220000,
    "speed": 0.9,
    "value": 500,
    "armor_type": "Heavy",
    "armor_value": 160,
    "type": "ground"
},
"lizard_wizard": {
    "health": 190000,
    "speed": 1.2,
    "value": 8,
    "armor_type": "Unarmored",
    "armor_value": 70,
    "type": "ground"
},
"mechadon": {
    "health": 200000,
    "speed": 0.6,
    "value": 8,
    "armor_type": "Heavy",
    "armor_value": 200,
    "type": "ground"
},
"rift_devil": {
    "health": 230000,
    "speed": 0.8,
    "value": 8,
    "armor_type": "Caustic",
    "armor_value": 190,
    "type": "ground"
},
"supermaul_demon_spawn": {
    "health": 270000,
    "speed": 0.7,
    "value": 8,
    "armor_type": "Hellish",
    "armor_value": 210,
    "type": "ground"
},
"voodoo_demon": {
    "health": 300000,
    "speed": 1.1,
    "value": 8,
    "armor_type": "Dark",
    "armor_value": 230,
    "type": "ground"
},
"voodoo_overlord": {
    "health": 350000,
    "speed": 1.0,
    "value": 9,
    "armor_type": "Psychic",
    "armor_value": 250,
    "type": "ground"
},
"voodoo_tyrant": {
    "health": 400000,
    "speed": 0.9,
    "value": 9,
    "armor_type": "Hellish",
    "armor_value": 270,
    "type": "ground"
},
"lord_supermaul_reborn": {
    "health": 450000,
    "speed": 0.5,
    "value": 400,
    "armor_type": "Hero",
    "armor_value": 150,
    "type": "ground"
}

}