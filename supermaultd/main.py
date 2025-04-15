import pygame
import json
import os
# Keep the Game import from the original structure
from game import Game 

def load_game_data(file_path):
    """
    Load all game definitions from the consolidated JSON file.

    :param file_path: The path to the tower_races JSON file.
    :return: A dictionary containing all game data.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def main():
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()
    
    game_data = {} # Default to empty data
    try:
        # Define paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, 'data')
        os.makedirs(data_dir, exist_ok=True) # Ensure data directory exists
        game_data_path = os.path.join(data_dir, 'tower_races.json')
        
        # Create a sample tower_races.json if it doesn't exist 
        # (using the structure you provided)
        if not os.path.exists(game_data_path):
            sample_data = { 
              "tower_sizes": {
                "small": {"grid_width": 1,"grid_height": 1,"description": "..."},
                "medium": {"grid_width": 2,"grid_height": 2,"description": "..."},
                "large": {"grid_width": 3,"grid_height": 3,"description": "..."}
              },
              "ranges": {
                "melee": { "min": 1, "max": 1 },
                "short": { "min": 1, "max": 3 },
                "medium": { "min": 1, "max": 6 },
                "long": { "min": 1, "max": 9 },
                "global": { "min": 1, "max": 9999 }
              },
              "damagetypes": {
                "normal": {"description": "...", "multiplier": 1.0, "effective_against": []},
                "piercing": {"description": "...", "multiplier": 1.1, "effective_against": ["light"]},
                # ... other damage types ...
              },
              "races": {
                "crystal_castle": {
                  "description": "...",
                  "towers": {
                    "shard_launcher": { # Example tower
                      "name": "Shard Launcher", "size": "small", "cost": 50, "damage": 120,
                      "damage_type": "chaos", "range_category": "medium", "attack_interval": 0.6,
                      "projectile_speed": 350, "unique": "..."
                    }
                    # ... other towers for this race ...
                  }
                }
                # ... other races ...
              }
            } # Note: Truncated sample data for brevity
            with open(game_data_path, 'w') as f:
                json.dump(sample_data, f, indent=2) # Use indent=2 for readability
            print(f"Created sample game data file at: {game_data_path}")
        
        # Load the consolidated game data
        game_data = load_game_data(game_data_path)
        print("Loaded Game Data from tower_races.json")
        # Optional: Print sections for confirmation
        if "races" in game_data:
            print(f" - Loaded {len(game_data['races'])} race(s)")
        if "damagetypes" in game_data:
             print(f" - Loaded {len(game_data['damagetypes'])} damage type(s)")
        # ... add prints for ranges, tower_sizes if needed

    except FileNotFoundError:
        # Use f-string for the error message
        print(f"Error: Could not find the game data file at {game_data_path}") 
    except json.JSONDecodeError as e:
        # Provide context for JSON errors
        print(f"Error: Could not decode JSON from {game_data_path}. Details: {e}") 
    except KeyError as e:
        print(f"Error: Missing expected key in {game_data_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while loading data: {e}")
        # It might be useful to print the full traceback in debug scenarios
        # import traceback
        # traceback.print_exc()
    
    # Create and run the Game object, passing the consolidated data
    # Note: The Game class in game.py needs to be updated
    game = Game(game_data) 
    game.run()

    pygame.quit()

if __name__ == '__main__':
    main()

# Clean up old comments