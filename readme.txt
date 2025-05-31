=========================
 SuperMaulTD - Game Guide
=========================

Introduction
------------
SuperMaulTD is a tower defense game where you place defensive towers to stop waves of enemies from reaching the end of a path. Strategically choosing and placing towers is key to survival.

Core Gameplay
-------------
1.  **Tower Placement:** You spend money to build towers on designated grid squares. Towers automatically attack incoming enemies within their range.
2.  **Enemy Waves:** Enemies spawn periodically and follow a set path towards an objective zone.
3.  **Objective:** Prevent enemies from reaching the objective. Each enemy that reaches it costs you a life. Running out of lives means game over.
4.  **Economy:** You start with a set amount of money and gain more by defeating enemies. Managing your money to build and upgrade towers is crucial.

Key Mechanics
-------------
*   **Towers:**
    *   **Races:** Choose from a variety of races, each with a unique set of towers.
    *   **Cost:** Each tower costs money to build.
    *   **Placement:** Towers occupy specific grid cells and cannot be placed on the enemy path or restricted zones (edges, top/bottom rows). Larger towers occupy multiple cells.
    *   **Range:** Towers attack enemies within their range (measured in pixels). Some towers have a minimum range they cannot shoot within.
    *   **Attack Types:**
        *   `projectile`: Fires a visible projectile that travels to the target.
        *   `instant`: Deals damage instantly to the target (e.g., lightning, melee).
        *   `beam`: Fires a continuous beam at the target.
        *   `aura`: Affects enemies or towers within a radius (implementation for many auras is pending).
        *   `none`: Does not attack (e.g., walls, support structures).
    *   **Targeting:** Towers can target "ground", "air", or both. Some may specifically target certain "armor_type" enemies (e.g., "ethereal").
    *   **Damage:** Towers deal damage based on their `damage_min`, `damage_max`, and `damage_type`.
    *   **Attack Speed:** Defined by `attack_interval` (seconds between attacks). Lower is faster.

*   **Enemies:**
    *   **Health:** Amount of damage an enemy can take.
    *   **Speed:** How fast the enemy moves along the path.
    *   **Armor Type:** Affects how much damage is taken from different Damage Types (e.g., "Light", "Medium", "Heavy", "Fortified", "Ethereal", "Unarmored").
    *   **Armor Value:** Numerical armor rating that further modifies damage taken (positive reduces, negative increases).
    *   **Movement Type:** "ground" or "air".
    *   **Value:** Money awarded when the enemy is defeated.

*   **Damage Types:** Towers deal specific damage types (e.g., "normal", "piercing", "siege", "arcane", "chaos"). These interact with enemy Armor Types.

*   **Special Effects (Implemented):**
    *   **DoT (Damage over Time):** Deals damage periodically after an initial hit (e.g., `gaia_cauldron_juggernaut`, `alchemist_acid_sprayer`). Applied by projectiles, instant attacks, and beams.
    *   **Slow:** Reduces enemy movement speed for a duration (e.g., `igloo` towers, `bomb_sticky_bomb_launcher`). Applied by projectiles and beams.
    *   **Splash Damage:** Deals 25% of the initial hit's damage to enemies near the primary target upon projectile impact or instant attack. Radius defined by `splash_radius`.
    *   **Pierce Adjacent:** Allows a projectile to hit its primary target and then deal 75% of the projectile's base damage to the single nearest valid enemy within a short range (`GRID_SIZE * 0.6` pixels).
    *   **Bounce:** Allows a projectile to hit its primary target and then create a new projectile aimed at the closest valid enemy within `bounce_range_pixels`. The bounced projectile deals damage reduced by `bounce_damage_falloff` (default 50%) and does not crit or re-apply special effects.
    *   **Max HP Reduction:** Permanently reduces the target's maximum HP by a percentage defined by `reduction_percentage` on each hit (e.g., `husk_entropy_spike`). Applied by projectiles via `apply_special_effects`.
    *   **Rampage Damage Stack:** Tower gains bonus flat damage (`damage_per_stack`) on each consecutive instant hit, up to `max_stacks`. Stacks reset if the tower doesn't hit anything for `decay_duration` seconds (e.g., `husk_void_horror`).
    *   **Chance Ignore Armor:** Has a `chance_percent` on hit to calculate damage as if the target's armor was lower by `ignore_amount` for that specific hit (e.g., `titan_assembly_golem`). Applied by projectiles via `apply_damage`.
    *   **Armor Shred:** Permanently reduces the target's armor by `armor_reduction_amount` on hit, based on `chance_percent` (e.g., `goblin_ripper_mech`). Applied by instant attacks via `Tower.attack`.
    *   **Random Bombardment:** Periodically triggers an explosion at a random point within `bombardment_radius`. Deals damage (`strike_damage_min/max`) in a small AoE (`strike_aoe_radius`) at the impact point (e.g., `bomb_barrage_beacon`). Managed in `Tower.update`.
    *   **Bonechill & Shatter:** `bonechill_pulse_aura` applies a status effect. Projectiles with `shatter` deal bonus damage (`shatter_damage_multiplier`) when hitting a `bonechill`-ed enemy. (e.g., `igloo_glacial_heart`, `igloo_icicle_cannon`).

*   **Special Effects (Defined but Pending Implementation):**
    *   Auras (Damage, Slow, Buffs like Attack Speed/Range/Defense)
    *   Stuns
    *   Unique interactions (Chain Lightning, Armor Reduction, etc.)
    *   Income Generation (e.g., `nomad_trading_post`)

Available Races
---------------
*   Gaia
*   Stronghold Knights
*   Bomb Brigade
*   Stone Summoners Circle
*   Alchemists Guild
*   Igloo
*   Astralists
*   Goblin Hovel
*   Deepseers
*   Spark
*   Space Husks
*   Titan Assemblage
*   Police Station
*   Tech Center
*   Seadogs
*   Heaven
*   Solar
*   Wandering Nomads

How to Play (Basic Steps)
-------------------------
1.  Launch the game and select a race.
2.  Observe the enemy path and potential tower placement spots.
3.  Use the UI panel on the right to view available towers and your current money/lives.
4.  Click a tower button to select it (if affordable).
5.  Move your mouse over the grid; a preview will show the tower and placement validity (Green=OK, Red=Invalid).
6.  Click on a valid grid location to place the selected tower. Money will be deducted.
7.  Towers will automatically start attacking enemies in range that match their targeting criteria.
8.  Defeat enemies to earn money for more towers.
9.  Survive as long as possible!

Current Status
--------------
This game is actively under development. Many features, especially complex tower abilities and aura effects, are defined in the data files but require further code implementation to be fully functional. The core mechanics of placing towers, enemy pathing, and basic attacks (projectile, instant, beam) along with DoT, Slow, Splash, and Pierce are implemented.