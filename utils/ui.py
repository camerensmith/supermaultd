import pygame
from config import *

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        """
        Initialize a button with the given properties.
        
        :param x: X position
        :param y: Y position
        :param width: Button width
        :param height: Button height
        :param text: Button text
        :param color: Normal color
        :param hover_color: Color when mouse is hovering
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        from utils.fonts import get_font
        self.font = get_font(36)
        self.is_hovered = False
        
    def handle_event(self, event):
        """Handle mouse events for the button"""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            self.current_color = self.hover_color if self.is_hovered else self.color
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False
        
    def draw(self, screen):
        """Draw the button on the screen"""
        pygame.draw.rect(screen, self.current_color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class TextBox:
    def __init__(self, x, y, width, height, text, font_size=36):
        """
        Initialize a text box with the given properties.
        
        :param x: X position
        :param y: Y position
        :param width: Box width
        :param height: Box height
        :param text: Text to display
        :param font_size: Font size
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        from utils.fonts import get_font
        self.font = get_font(font_size)
        
    def set_text(self, text):
        """Update the text content"""
        self.text = text
        
    def draw(self, screen):
        """Draw the text box on the screen"""
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class ProgressBar:
    def __init__(self, x, y, width, height, max_value, color, background_color):
        """
        Initialize a progress bar with the given properties.
        
        :param x: X position
        :param y: Y position
        :param width: Bar width
        :param height: Bar height
        :param max_value: Maximum value
        :param color: Fill color
        :param background_color: Background color
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.max_value = max_value
        self.current_value = max_value
        self.color = color
        self.background_color = background_color
        
    def set_value(self, value):
        """Update the current value"""
        self.current_value = max(0, min(value, self.max_value))
        
    def draw(self, screen):
        """Draw the progress bar on the screen"""
        # Draw background
        pygame.draw.rect(screen, self.background_color, self.rect)
        
        # Draw fill
        fill_width = int(self.rect.width * (self.current_value / self.max_value))
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(screen, self.color, fill_rect)
        
        # Draw border
        pygame.draw.rect(screen, WHITE, self.rect, 2)
