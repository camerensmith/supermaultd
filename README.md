# SuperMaulTD - Tower Defense Game

## Table of Contents
- [Introduction](#introduction)
- [Core Gameplay](#core-gameplay)
- [Key Mechanics](#key-mechanics)
  - [Towers](#towers)
  - [Enemies](#enemies)
  - [Damage System](#damage-system)
  - [Special Effects](#special-effects)
- [Available Races](#available-races)
- [How to Play](#how-to-play)
- [Development Status](#development-status)

## Introduction
SuperMaulTD is a tower defense game where you place defensive towers to stop waves of enemies from reaching the end of a path. Strategically choosing and placing towers is key to survival.

## Core Gameplay
1. **Tower Placement:** You spend money to build towers on designated grid squares. Towers automatically attack incoming enemies within their range.
2. **Enemy Waves:** Enemies spawn periodically and follow a set path towards an objective zone.
3. **Objective:** Prevent enemies from reaching the objective. Each enemy that reaches it costs you a life. Running out of lives means game over.
4. **Economy:** You start with a set amount of money and gain more by defeating enemies. Managing your money to build and upgrade towers is crucial.

## Key Mechanics

### Towers
- **Races:** Choose from a variety of races, each with a unique set of towers.
- **Cost:** Each tower costs money to build.
- **Placement:** Towers occupy specific grid cells and cannot be placed on the enemy path or restricted zones (edges, top/bottom rows). Larger towers occupy multiple cells.
- **Range:** Towers attack enemies within their range (measured in pixels). Some towers have a minimum range they cannot shoot within.
- **Attack Types:**
  - `projectile`: Fires a visible projectile that travels to the target.
  - `instant`: Deals damage instantly to the target (e.g., lightning, melee).
  - `beam`: Fires a continuous beam at the target.
  - `aura`: Affects enemies or towers within a radius.
  - `none`: Does not attack (e.g., walls, support structures).
- **Targeting:** Towers can target "ground", "air", or both. Some may specifically target certain "armor_type" enemies.
- **Damage:** Towers deal damage based on their `damage_min`, `damage_max`, and `damage_type`.
- **Attack Speed:** Defined by `attack_interval` (seconds between attacks). Lower is faster.

### Enemies
- **Health:** Amount of damage an enemy can take.
- **Speed:** How fast the enemy moves along the path.
- **Armor Types:**
  - `Light`: Takes reduced damage from normal attacks
  - `Medium`: Balanced armor
  - `Heavy`: Takes reduced damage from piercing attacks
  - `Fortified`: Takes reduced damage from siege attacks
  - `Ethereal`: Takes reduced damage from physical attacks
  - `Unarmored`: Takes full damage from all sources
- **Armor Value:** Numerical armor rating that further modifies damage taken (positive reduces, negative increases).
- **Movement Type:** "ground" or "air".
- **Value:** Money awarded when the enemy is defeated.

### Damage System
- **Damage Types:**
  - `normal`: Standard damage type
  - `piercing`: Effective against light armor
  - `siege`: Effective against heavy armor
  - `arcane`: Effective against ethereal enemies
  - `chaos`: Ignores armor type modifiers
- **Damage Calculation:**
  - Base damage is modified by:
    - Armor type multiplier
    - Armor value reduction
    - Special effect multipliers
    - Critical hit chance

### Special Effects

#### Implemented Effects
1. **DoT (Damage over Time)**
   - Deals damage periodically after initial hit
   - Examples: `pyro_pyromaniac`, `alchemist_acid_sprayer`

2. **Slow**
   - Reduces enemy movement speed
   - Examples: `igloo` towers, `zork_creep_colony`

3. **Splash Damage**
   - Deals 25% of initial damage to nearby enemies
   - Radius defined by `splash_radius`

4. **Pierce Adjacent**
   - Hits primary target and nearest enemy
   - Deals 75% damage to secondary target
   - Range: `GRID_SIZE * 0.6` pixels

5. **Bounce**
   - Projectile bounces to nearest enemy
   - Damage reduced by `bounce_damage_falloff` (default 50%)
   - No crit or special effects on bounce

6. **Max HP Reduction**
   - Permanently reduces target's max HP
   - Example: `husk_entropy_spike`

7. **Rampage Damage Stack**
   - Gains bonus damage per consecutive hit
   - Stacks reset after `decay_duration`
   - Example: `husk_void_horror`

8. **Chance Ignore Armor**
   - Random chance to ignore armor
   - Example: `titan_assembly_golem`

9. **Armor Shred**
   - Permanently reduces target's armor
   - Example: `goblin_ripper_mech`

10. **Random Bombardment**
    - Periodically triggers explosions
    - Example: `bomb_barrage_beacon`

11. **Bonechill & Shatter**
    - Combo effect between towers
    - Example: `igloo_glacial_heart`, `igloo_icicle_cannon`

12. **Harpoon Pull**
    - Pulls enemies towards tower
    - Applies shear damage multiplier
    - Example: `seadog_harpoon_tower`

#### Pending Implementation
- Auras (Damage, Slow, Buffs)
- Chain Lightning
- Income Generation
- More complex tower interactions

## Available Races

### Gaia
- Nature-themed towers
- Focus on area control and DoT effects
- Notable towers: `gaia_forest_warden`, `gaia_gaias_box`

### Stronghold Knights
- Defensive towers
- High armor and health
- Notable towers: `knight_stronghold`, `knight_catapult`

### Bomb Brigade
- Explosive damage
- Splash and area effects
- Notable towers: `bomb_barrage_beacon`, `bomb_sticky_bomb_launcher`

### Stone Summoners Circle
- Earth and stone magic
- Defensive structures
- Notable towers: `stone_earthquake_totem`, `stone_rock_thrower`

### Alchemists Guild
- Chemical effects
- DoT and status effects
- Notable towers: `alchemist_acid_sprayer`, `alchemist_potion_mixer`

### Igloo
- Ice and cold effects
- Slow and freeze mechanics
- Notable towers: `igloo_glacial_heart`, `igloo_icicle_cannon`

### Astralists
- Space and cosmic effects
- High damage, low rate of fire
- Notable towers: `astral_void_caller`, `astral_star_cannon`

### Goblin Hovel
- Rapid fire, low damage
- Mechanical contraptions
- Notable towers: `goblin_ripper_mech`, `goblin_rocket_launcher`

### Deepseers
- Water and ocean themes
- Pull and control effects
- Notable towers: `deepseer_kraken`, `deepseer_whirlpool`

### Spark
- Electricity and lightning
- Chain effects
- Notable towers: `spark_lightning_tower`, `spark_thunder_cannon`

### Space Husks
- Void and entropy effects
- HP reduction and DoT
- Notable towers: `husk_entropy_spike`, `husk_void_horror`

### Titan Assemblage
- Mechanical giants
- High damage, slow attack
- Notable towers: `titan_assembly_golem`, `titan_assembly_cannon`

### Police Station
- Law enforcement theme
- Stun and capture effects
- Notable towers: `police_station`, `police_sniper`

### Tech Center
- Advanced technology
- Precision targeting
- Notable towers: `tech_ground_targeting_computer`, `tech_laser_tower`

### Seadogs
- Pirate theme
- Harpoon and pull mechanics
- Notable towers: `seadog_harpoon_tower`, `seadog_cannoneer`

### Heaven
- Divine powers
- Healing and buff effects
- Notable towers: `heaven_angel_tower`, `heaven_judgment_cannon`

### Solar
- Sun and light powers
- Beam attacks
- Notable towers: `solar_beam_tower`, `solar_flare_cannon`

### Wandering Nomads
- Trading and economy
- Support and buff towers
- Notable towers: `nomad_trading_post`, `nomad_caravan`

## How to Play
1. Launch the game and select a race
2. Observe the enemy path and potential tower placement spots
3. Use the UI panel to view available towers and resources
4. Click a tower button to select it (if affordable)
5. Place towers on valid grid locations
6. Towers automatically attack enemies in range
7. Defeat enemies to earn money
8. Survive as long as possible!

## Development Status
This game is actively under development. Core mechanics are implemented, including:
- Tower placement and targeting
- Enemy pathfinding
- Basic attack types (projectile, instant, beam)
- Special effects (DoT, Slow, Splash, Pierce, Bounce)
- Damage calculation and armor system
- Harpoon pull mechanics

Future updates will include:
- More complex tower abilities
- Additional special effects
- New races and towers
- Enhanced visual effects
- Sound and music improvements

## Features

- Multiple tower types with unique abilities
- Various enemy types with different behaviors
- Resource management and tower upgrades
- Pathfinding for enemies
- Visual effects and animations
- Sound effects and music

## Tower Types

### Police Towers

- **Police Blockade**: Basic wall tower that blocks enemy movement
- **Peacekeeper**: Fast-firing tower with moderate damage
- **Grenade Launcher**: Fires bouncing grenades that detonate after a delay
  - Grenades follow a natural arc trajectory
  - Can bounce off towers up to 3 times
  - Creates area-of-effect explosions
  - Damage falls off with distance from explosion center
- **Taser Turret**: Instant-damage tower that stuns enemies
- **Breacher**: Shotgun-style tower that fires multiple pellets
- **Police HQ**: Aura tower that boosts adjacent tower damage

### Other Races

[Previous race descriptions remain unchanged...]

## Game Mechanics

- **Tower Placement**: Place towers on a grid-based map
- **Enemy Pathfinding**: Enemies find the shortest path to the exit
- **Resource Management**: Earn money by defeating enemies
- **Tower Upgrades**: Improve tower stats and unlock new abilities
- **Special Effects**: Various visual and gameplay effects

## Controls

- Left Click: Select and place towers
- Right Click: Cancel tower placement
- Space: Pause/Resume game
- ESC: Open menu
- S: Spawn test enemy

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the game: `python main.py`

## Requirements

- Python 3.8+
- Pygame
- Pymunk (for physics)
- Other dependencies listed in requirements.txt

## Contributing

Feel free to submit issues and pull requests.

## License

[License information remains unchanged...] 