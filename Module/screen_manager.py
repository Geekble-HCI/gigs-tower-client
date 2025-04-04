import pygame
import queue
import threading

class ScreenManager:
    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        
        self.bg_image = pygame.image.load("Image/bg.png")
        self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
        
        try:
            self.font = pygame.font.Font("Font/RoundSquare.ttf", 74)
        except:
            print("폰트 로드 실패, 기본 폰트 사용")
            self.font = pygame.font.Font(None, 74)
        
        self.message_queue = queue.Queue()

    def draw_text(self, text):
        lines = text.split('\n')
        y = self.height // 2 - (len(lines) * 40)
        for line in lines:
            text_surface = self.font.render(line, True, (0, 255, 0))
            text_rect = text_surface.get_rect(center=(self.width//2, y))
            self.screen.blit(text_surface, text_rect)
            y += 80

    def update_screen(self, text):
        if threading.current_thread() is threading.main_thread():
            self.screen.blit(self.bg_image, (0, 0))
            self.draw_text(text)
            pygame.display.flip()
        else:
            self.message_queue.put(text)

    def process_message_queue(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.screen.blit(self.bg_image, (0, 0))
                self.draw_text(message)
                pygame.display.flip()
        except queue.Empty:
            pass
