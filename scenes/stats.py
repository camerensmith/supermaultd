import pygame
from config import *

class StatsScene:
    def __init__(self, game):
        self.game = game
        from utils.fonts import get_font
        self.font = get_font(48)
        self.title_font = get_font(64)
        
        # Stats to display
        self.stats = {
            "Games Played": 0,
            "Total Kills": 0,
            "Highest Wave": 0,
            "Total Money Earned": 0
        }
        
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # TODO: Return to menu
                pass
                
    def update(self):
        # TODO: Update stats from saved data
        pass
        
    def draw(self, screen):
        # Draw title
        title = self.title_font.render("Statistics", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title, title_rect)
        
        # Draw stats
        for i, (stat_name, value) in enumerate(self.stats.items()):
            text = self.font.render(f"{stat_name}: {value}", True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 60))
            screen.blit(text, text_rect)
            
        # Draw back instruction
        back_text = self.font.render("Press ESC to return", True, GRAY)
        back_rect = back_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        screen.blit(back_text, back_rect)
