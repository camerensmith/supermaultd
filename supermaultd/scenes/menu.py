import pygame
import pygame_gui
from config import *
from scenes.game_scene import GameScene
import json
import os

class MenuScene:
    def __init__(self, game, screen_width, screen_height):
        self.game = game
        self.screen_width = screen_width   # Store actual screen width
        self.screen_height = screen_height # Store actual screen height
        
        self.font = pygame.font.Font(None, 36) # Smaller font for more options
        self.title_font = pygame.font.Font(None, 64)
        self.desc_font = pygame.font.Font(None, 28) # Font for description
        
        # Load Race Data
        self.race_data = self.load_race_data("supermaultd/data/tower_races.json")
        self.race_ids = list(self.race_data.keys())
        
        # Menu States: 'main', 'race_select'
        self.state = "main"
        
        # Main Menu options
        self.main_options = ["Start Game", "Select Race", "Options", "Quit"]
        self.selected_main_option = 0
        
        # Race Selection options
        self.selected_race_option = 0
        self.selected_race_id = self.race_ids[0] if self.race_ids else None # Default to first race
        self.current_race_description = ""
        self.race_list_labels = [] # Store UI Labels for race list
        self.update_race_preview() # Initial description update
        
        # Define area for preview panel using actual screen dimensions
        self.preview_panel_rect = pygame.Rect(
            self.screen_width * 0.6, 
            self.screen_height * 0.2, 
            self.screen_width * 0.35, 
            self.screen_height * 0.6
        )
        
        # Need access to the UIManager
        self.manager = self.game.manager # Assuming game instance has a manager

    def load_race_data(self, file_path):
        """Loads race names and descriptions from the JSON file."""
        races = {}
        if not os.path.isfile(file_path):
            print(f"Warning: Race data file not found: {file_path}")
            return races
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            for race_id, race_info in data.get("races", {}).items():
                if "description" in race_info and "towers" in race_info: # Basic check
                    races[race_id] = race_info # Store the whole info dict
            print(f"Loaded {len(races)} races.")
        except json.JSONDecodeError as e:
            print(f"Error decoding race JSON file {file_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred loading race data {file_path}: {e}")
        return races

    def update_race_preview(self):
        """Updates the description text based on the selected race option."""
        if not self.race_ids:
            self.current_race_description = "No races available."
            return
        
        preview_race_id = self.race_ids[self.selected_race_option]
        race_info = self.race_data.get(preview_race_id, {})
        self.current_race_description = race_info.get("description", "No description found.")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.state == "main":
                if event.key == pygame.K_UP:
                    self.selected_main_option = (self.selected_main_option - 1) % len(self.main_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_main_option = (self.selected_main_option + 1) % len(self.main_options)
                elif event.key == pygame.K_RETURN:
                    self.handle_selection()
                    
            elif self.state == "race_select":
                prev_selected = self.selected_race_option
                if event.key == pygame.K_UP:
                    if self.race_ids:
                        self.selected_race_option = (self.selected_race_option - 1) % len(self.race_ids)
                elif event.key == pygame.K_DOWN:
                     if self.race_ids:
                        self.selected_race_option = (self.selected_race_option + 1) % len(self.race_ids)
                elif event.key == pygame.K_RETURN:
                    if self.race_ids:
                        self.selected_race_id = self.race_ids[self.selected_race_option]
                        print(f"Race selected: {self.selected_race_id}")
                        self.state = "main"
                        self.clear_race_list_ui() # Clear UI when leaving
                elif event.key == pygame.K_ESCAPE:
                    self.state = "main"
                    self.clear_race_list_ui() # Clear UI when leaving
                    
                # Update preview and highlight if selection changed
                if self.selected_race_option != prev_selected:
                    self.update_race_preview()
                    self.update_selected_race_highlight()

    def handle_selection(self):
        selected_text = self.main_options[self.selected_main_option]
        if selected_text == "Start Game":
            if self.selected_race_id:
                self.game.scene = GameScene(self.game, self.selected_race_id, self.screen_width, self.screen_height)
            else:
                print("Error: No race selected!")
        elif selected_text == "Select Race":
            self.state = "race_select"
            self.create_race_list_ui()
        elif selected_text == "Options":
            pass
        elif selected_text == "Quit":
            self.game.running = False
            
    def update(self):
        if self.manager:
            time_delta = self.game.clock.tick(60)/1000.0
            self.manager.update(time_delta)

    def draw(self, screen):
        title = self.title_font.render("Tower Defense", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, self.screen_height // 4))
        screen.blit(title, title_rect)
        
        if self.state == "main":
            self.draw_main_menu(screen)
        elif self.state == "race_select":
            self.draw_race_select(screen)
            
        if self.manager:
            self.manager.draw_ui(screen)

    def draw_main_menu(self, screen):
        option_start_y = self.screen_height // 2 - (len(self.main_options) * 35)
        for i, option in enumerate(self.main_options):
            color = GREEN if i == self.selected_main_option else WHITE
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(center=(self.screen_width // 2, option_start_y + i * 60))
            screen.blit(text, text_rect)
            
    def draw_race_select(self, screen):
        # Draw Title above the list area (left side)
        select_title = self.font.render("Select Race", True, WHITE)
        # Adjust X position to be centered over the list area (approx 0.1 to 0.5 width)
        select_title_rect = select_title.get_rect(center=(self.screen_width * 0.3, self.screen_height * 0.15)) # Raised Y a bit
        screen.blit(select_title, select_title_rect)
        
        # Draw the Description Panel Outline (right side)
        pygame.draw.rect(screen, GRAY, self.preview_panel_rect, 2)
        
        # --- Description Panel Content ---
        if self.race_ids: # Only draw content if races exist
            # Get selected race ID and Name
            preview_race_id = self.race_ids[self.selected_race_option]
            race_name_formatted = preview_race_id.replace('_', ' ').title()
            
            # Draw Race Name at the top of the panel
            race_name_text = self.font.render(race_name_formatted, True, WHITE)
            # Position slightly below the panel's top edge
            race_name_rect = race_name_text.get_rect(midtop=(self.preview_panel_rect.centerx, self.preview_panel_rect.top + 15))
            screen.blit(race_name_text, race_name_rect)
            
            # Define area for the description text below the name
            # Add padding (e.g., 10px) from panel edges and below name
            desc_padding = 10
            desc_area_rect = pygame.Rect(
                self.preview_panel_rect.left + desc_padding,
                race_name_rect.bottom + desc_padding, # Start below name
                self.preview_panel_rect.width - (2 * desc_padding),
                self.preview_panel_rect.bottom - (race_name_rect.bottom + desc_padding) - desc_padding # Fill remaining height
            )
            
            # Draw the wrapped description text
            self.draw_text_wrapped(screen, self.current_race_description, self.desc_font, WHITE, desc_area_rect)
        else:
            # Optional: Display a message if no races are loaded
            no_races_text = self.font.render("No Races Loaded", True, RED)
            no_races_rect = no_races_text.get_rect(center=self.preview_panel_rect.center)
            screen.blit(no_races_text, no_races_rect)
        # --- End Description Panel Content ---
        
        # NOTE: The pygame_gui labels for the list are drawn by self.manager.draw_ui(screen)

    def create_race_list_ui(self):
        self.clear_race_list_ui()
        list_start_y = self.screen_height * 0.3
        label_height = 40
        label_width = self.screen_width * 0.4
        
        for i, race_id in enumerate(self.race_ids):
            race_info = self.race_data.get(race_id, {})
            description = race_info.get("description", "No description.")
            display_name = race_id.replace('_', ' ').title()
            
            label_rect = pygame.Rect(self.screen_width * 0.1, list_start_y + i * (label_height + 5), label_width, label_height)
            
            object_id = "#race_label_selected" if i == self.selected_race_option else "#race_label"
            
            label = pygame_gui.elements.UILabel(
                relative_rect=label_rect,
                text=display_name,
                manager=self.manager,
                object_id=object_id,
                tool_tip_text=description
            )
            self.race_list_labels.append(label)
        self.update_selected_race_highlight()

    def clear_race_list_ui(self):
        for label in self.race_list_labels:
            label.kill()
        self.race_list_labels = []
        
    def update_selected_race_highlight(self):
        for i, label in enumerate(self.race_list_labels):
            if i == self.selected_race_option:
                label.set_object_id("#race_label_selected")
            else:
                label.set_object_id("#race_label")
            label.rebuild()
        
    def draw_text_wrapped(self, surface, text, font, color, rect):
        words = text.split(' ')
        lines = []
        current_line = ""
        line_height = font.get_linesize()
        space_width = font.size(' ')[0]

        for word in words:
            word_surface = font.render(word, True, color)
            word_width, _ = word_surface.get_size()
            
            line_width = font.size(current_line)[0]
            
            if line_width + (space_width if current_line else 0) + word_width <= rect.width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)

        y = rect.top
        for line in lines:
            if y + line_height > rect.bottom:
                 break
            line_surface = font.render(line, True, color)
            line_rect = line_surface.get_rect(centerx=rect.centerx, top=y)
            surface.blit(line_surface, line_rect)
            y += line_height
