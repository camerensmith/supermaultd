# SuperMaulTD - Tower Defense Game

## Table of Contents
- [Introduction](#introduction)
- [Game Modes](#game-modes)
- [Core Gameplay](#core-gameplay)
- [Races & Towers](#races--towers)
- [Towers: Types & Mechanics](#towers-types--mechanics)
- [Enemies](#enemies)
- [Damage & Effects](#damage--effects)
- [Economy & Resource Management](#economy--resource-management)
- [Pathfinding & Map Mechanics](#pathfinding--map-mechanics)
- [Controls & UI](#controls--ui)
- [Installation & Requirements](#installation--requirements)
- [Development Status](#development-status)
- [Appendix](#appendix)

## Introduction
SuperMaulTD is a feature-rich, grid-based tower defense game where you strategically place towers (from a wide variety of races/factions) to stop waves of enemies from reaching your base. The game features deep mechanics, unique races, advanced pathfinding, and a robust damage/armor system. The base game is fully featured, while Advanced and Wild modes are currently works in progress (WIP).

## Game Modes
- **Base Mode:**
  - The core, fully featured experience. All races, towers, and mechanics are available and balanced for standard play.
- **Advanced Mode (WIP):**
  - Planned to introduce new challenges, modifiers, and advanced mechanics. Not all features are implemented yet.
- **Wild Mode (WIP):**
  - Experimental mode with unique rules, randomization, or special events. Still under development.

## Core Gameplay
1. **Select a Race:** Choose from a diverse roster, each with unique towers and playstyles.
2. **Tower Placement:** Spend gold to build towers on valid grid cells. Towers cannot be placed on enemy paths or restricted zones. Larger towers occupy multiple cells.
3. **Enemy Waves:** Enemies spawn in waves, following the shortest path to your base. Each enemy that reaches your base costs you a life.
4. **Combat:** Towers automatically attack enemies in range, using projectiles, beams, auras, or special effects.
5. **Economy:** Earn gold by defeating enemies. Spend gold to build or upgrade towers. Some races/towers generate or manipulate gold in special ways.
6. **Survival:** Survive as many waves as possible! Running out of lives means game over.

## Races & Towers
SuperMaulTD features a wide array of races (factions), each with a unique theme, mechanics, and tower lineup. Below is a comprehensive, up-to-date list of all races in the base game. (Advanced/Wild races may be added in the future.)

### Race Overview Table
| Race                | Theme/Description                                      | Notable Mechanics/Strengths                |
|---------------------|-------------------------------------------------------|--------------------------------------------|
| Gaia                | Nature, area control, DoT, siege                      | Splash, DoT, critical hits                 |
| Stronghold Knights  | Defensive, human, man & machine                       | High armor, melee, execution               |
| Bomb Brigade        | Explosives, AOE, siege                                | Huge splash, siege damage                  |
| Stone Summoners     | Earth/stone, crits, splash                            | Double crit splash, instant attacks        |
| Alchemists Guild    | Chemical, poison, DoT, armor melt                     | DoT, armor shred, poison, auras            |
| Igloo               | Ice, slow, freeze, shatter                            | Slow, bonechill, shatter bonus             |
| Astralists          | Space/cosmic, high damage, low rate                   | High single-target, chain beams            |
| Goblin Hovel        | Mechanical, rapid fire, chaos                         | Fast attacks, self-destruct, armor shred   |
| Deepseers           | Water/ocean, pull, control                            | Harpoon, pull, whirlpool, gold on kill     |
| Spark               | Electricity, chain, stun                              | Chain lightning, stun, attack speed auras  |
| Space Husks         | Void/entropy, HP reduction, DoT                       | Max HP reduction, rampage, stacking damage |
| Titan Assemblage    | Mechanical giants, high damage, slow                  | Ignore armor, double strike, reaper effect |
| Police Station      | Law, stun, pierce, auras                              | Stun, shotgun, adjacency buffs             |
| Tech Center         | Advanced tech, precision, debuffs                     | Mark for death, freeze, time manipulation  |
| Seadogs             | Pirate, harpoon, plunder                              | Harpoon pull, gold, broadside, whip        |
| Heaven              | Divine, healing, buffs, armor ignore                  | Ignore armor, healing, armor reduction     |
| Solar               | Sun/light, beams, radiance                            | Radiance aura, beam, adjacency synergy     |
| Wandering Nomads    | Trading, economy, support                             | Gold generation, bounty, boomerang         |
| Crystal Castle      | Chaos, snipers, chain beams                           | Armor bypass, high DPS, chain attacks      |
| Pyro                | Fire, burn, splash, auras                             | DoT, burn, fire traps, auras               |
| Tank Legion         | Heavy siege, slow, fortified                          | Siege, distance bonus, AOE                 |
| Zork                | Swarm, AOE, numbers                                   | Swarmers, attack speed auras, horde        |
| Brine               | Deep sea, arcane, bash                                | Bash, splash, vortex, stun                 |
| Ogre Stronghold     | Melee, crit, brute force                              | High crit, berserk, stun                   |
| Industry            | Machines, gold, salvo, gattling                       | Gold gen, salvo, gattling, fallout         |
| Alien               | Cosmic, orbs, black hole                              | Orbiting orbs, black hole, chain           |
| Void Husks          | Undead, void, lifedrain                               | Max HP reduction, rampage, stacking damage |
| TAC (Titan Assembly Command) | Titans, special effects, reaper, ignore armor | Every Nth strike, double strike, reaper    |
| Nomad Clans         | Versatile, land, resourceful                          | Bounty, boomerang, pass-through, gold      |

#### (See Appendix for full race/tower details and special effects)

## Towers: Types & Mechanics
- **Grid Sizes:** Towers come in various sizes (1x1, 2x2, 3x3, etc.), affecting placement and blocking.
- **Attack Types:**
  - `projectile`: Fires a visible projectile.
  - `instant`: Deals damage instantly (melee, lightning, etc.).
  - `beam`: Continuous damage beam.
  - `aura`: Passive effect in a radius (buff, debuff, DoT, etc.).
  - `none`: No attack (walls, support structures).
- **Targeting:** Towers may target "ground", "air", or both. Some target specific armor types.
- **Special Effects:** Many towers have unique effects (DoT, slow, armor shred, gold on kill, etc.).
- **Upgrades:** (Planned) Towers may be upgradable for increased stats or new abilities.

## Enemies
- **Types:** Ground and air units, each with unique movement and resistances.
- **Armor Types:**
  - `Light`, `Medium`, `Heavy`, `Fortified`, `Ethereal`, `Unarmored`
- **Armor Value:** Numeric modifier to damage taken (positive = less, negative = more).
- **Special Abilities:** Some enemies may have unique effects (planned).

## Damage & Effects
- **Damage Types:**
  - `normal`, `piercing`, `siege`, `arcane`, `chaos`
- **Calculation:**
  - Base damage × armor type multiplier × armor value × special multipliers × crit chance
- **Special Effects:**
  - **DoT (Damage over Time):** Burns, poison, bleed, etc.
  - **Slow:** Reduces enemy speed.
  - **Splash:** Damages nearby enemies.
  - **Pierce/Bounce:** Hits multiple targets.
  - **Max HP Reduction:** Permanently lowers enemy max HP.
  - **Rampage:** Stacking damage on consecutive hits.
  - **Armor Shred:** Permanently reduces armor.
  - **Random Bombardment:** Periodic explosions.
  - **Auras:** Buff/debuff in an area (damage, slow, crit, etc.).
  - **Harpoon Pull:** Pulls enemies toward tower.
  - **Gold Generation:** Earn extra gold from kills or passively.
  - **See Appendix for full list.**

## Economy & Resource Management
- **Gold:** Earned by defeating enemies, spent on towers/upgrades.
- **Special Towers:** Some generate gold passively or on kill (Nomads, Industry, Seadogs, etc.).
- **Resource Management:** Key to survival and high scores.

## Pathfinding & Map Mechanics
- **Enemy Pathfinding:** Enemies find the shortest path to the exit, dynamically updating if the map changes (walls/towers placed).
- **Blocking:** Towers/walls can block or redirect paths, but cannot fully seal off the map.
- **Map Layouts:** (Planned) Multiple maps and layouts.

## Controls & UI
- **Left Click:** Select/place towers
- **Right Click:** Cancel placement
- **Space:** Pause/Resume
- **ESC:** Open menu
- **S:** Spawn test enemy
- **UI:** Panel for tower selection, resources, and info.

## Installation & Requirements
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the game: `python main.py`

**Requirements:**
- Python 3.8+
- Pygame
- Pymunk (for physics)
- See `requirements.txt` for full list

## Development Status
- **Base Game:** Fully featured and playable
- **Advanced/Wild Modes:** WIP, not all features implemented
- **Planned:**
  - More complex tower abilities
  - Additional special effects
  - New races/towers
  - Enhanced visuals and sound
  - Upgrades and meta-progression

## Appendix
### Full Race & Tower List
(See `data/tower_races.json` for exhaustive details. Below is a summary; for full stats and effects, consult the JSON or in-game encyclopedia.)

- **Gaia:** Forest guardians, splash/DoT, critical hits. Notable: Forest Warden, Treant Boulder Thrower, Gaia's Box, Gnome, Ursa.
- **Stronghold Knights:** Defensive, melee, execution. Notable: Footman, Watchtower, Arcanum Tower, Ballista, Knight.
- **Bomb Brigade:** Explosives, AOE, siege. Notable: Bomb Lobber, Mine Field, Grenade Launcher, Bombardier, Bombardment Beacon.
- **Stone Summoners:** Crits, splash, instant. Notable: Pebble Shooter, Stonebreaker, Golem, Tremor Totem, Earth Spine.
- **Alchemists Guild:** DoT, poison, armor melt. Notable: Poison Dart Launcher, Miasma Pillar, Toxin Lab, Caustic Cannon, Plague Reactor.
- **Igloo:** Slow, freeze, shatter. Notable: Snowball Tosser, Glacial Heart, Frost Pulse, Icicle Launcher, Yeti, Glacier Cannon.
- **Astralists:** High damage, chain beams. Notable: (See JSON for full list.)
- **Goblin Hovel:** Rapid fire, chaos, self-destruct. Notable: Snotlinz, Junkka, Skrappaaa, Skrap Tank, Katapult Skwad, Shreddaaa.
- **Deepseers:** Pull, control, gold. Notable: Kraken, Whirlpool, Harpoon Tower.
- **Spark:** Chain, stun, auras. Notable: Static Post, Arc Tower, Zap Coil, Lightning Rod, Power Plant, Storm Generator.
- **Space Husks:** HP reduction, rampage. Notable: Void Leecher, Soulless, Void Stalker, Entropy Trooper, Rift Walker, Void Horror.
- **Titan Assemblage:** Ignore armor, double strike, reaper. Notable: Assembly Golem, Jaguar Mech, Samurai Mech, Athena Mech, Pummeler Mech, Reaper Mech.
- **Police Station:** Stun, shotgun, adjacency buffs. Notable: Peacekeeper, SWAT Officer, Breacher, Sniper Tower, Police HQ.
- **Tech Center:** Mark for death, freeze, time. Notable: Laser, Upgraded Laser, Particle Accelerator, Targeting Computer, Freeze Ray, Railgun, Time Machine.
- **Seadogs:** Harpoon, gold, broadside. Notable: Saltwater Scoundrel, Grog Barrel Launcher, Chain Shot Cannon, Slaver, Broadside, Cannoneer, Harpoon Tower.
- **Heaven:** Ignore armor, healing, armor reduction. Notable: Wrath Tower, Retribution Tower, Judgment Tower, Beacon of Light, Archangel, Seraphim.
- **Solar:** Radiance, beam, adjacency. Notable: Sun Spot, Solar Ray, Photon Relay, Helios, Corona, Star Forge.
- **Wandering Nomads:** Gold, bounty, boomerang. Notable: Dune Raider, Seer, Bazaar, Spirit Ward, Caravan Guard, Bounty Hunter, Boomeranger, Caravan Depot.
- **Crystal Castle:** Chaos, snipers, chain. Notable: Crystal Wall, Crystal Shooter, Diamond Cutter, Crystal Cannon, Crystal Fury, Facet Focuser, Gemstone Blaster, Crystal Dissolver.
- **Pyro:** Burn, splash, auras. Notable: Fire Wall, Flare Tower, Fire Trap, Flame Dancer, Pyromaniac, Searing Tower, Incinerator.
- **Tank Legion:** Siege, distance bonus, AOE. Notable: Tank Wall, Tank Defender, MK I, Blasto Mortar Tank, Hercules Javelin Tank, Cauldron Juggernaut.
- **Zork:** Swarm, AOE, horde. Notable: Zork Wall, Zorkling Spawner, Slime Spewer, Creep Colony, Horde Hurler, Swarmers, Brood Lord.
- **Brine:** Bash, splash, vortex. Notable: Altar of the Deep, Coral Trident, Serpent Coiler, Cascade Monument, Naga Depth Guard, Tidal Guardian, Vortex Monument.
- **Ogre Stronghold:** Melee, crit, berserk. Notable: Spike Wall, Ogrekin, Ogre Mage, Ogre Brute, War Drums, Stomping Grounds, Ogre Smasher, Ogre Chieftain.
- **Industry:** Gold, salvo, gattling, fallout. Notable: Factory Wall, Machinist, Factory, Oil Rig, Missile Battery Platform, Gattling Gun, Nuclear Silo.
- **Alien:** Orbs, black hole, chain. Notable: Alien Wall, Alien Drone, Prober, UFO, Tachyon Lance, Orbiter, Black Hole Generator.
- **Void Husks:** Lifedrain, rampage, HP reduction. Notable: Dead Space, Void Leecher, Soulless, Void Stalker, Entropy Trooper, Rift Walker, Void Horror.
- **TAC:** Every Nth strike, double strike, reaper. Notable: Machine Core, Assembly Golem, Jaguar Mech, Samurai Mech, Athena Mech, Pummeler Mech, Reaper Mech.
- **Nomad Clans:** Bounty, boomerang, pass-through. Notable: Sand Rock, Dune Raider, Seer, Bazaar, Spirit Ward, Caravan Guard, Bounty Hunter, Boomeranger, Caravan Depot.

### Special Effects Reference
- See [Damage & Effects](#damage--effects) for a summary of all implemented and planned effects.
- For full technical details, see `data/tower_races.json` and in-game encyclopedia.

https://lucid.app/lucidchart/0958e48e-ec1e-4be5-88b3-c9a945190759/edit?viewport_loc=-785%2C-736%2C4246%2C2161%2C0_0&invitationId=inv_cb3c4bc4-da41-4435-aaa8-964046aee371

---

Feel free to submit issues and pull requests! 
