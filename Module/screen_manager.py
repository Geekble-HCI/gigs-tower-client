import pygame
import queue
import threading

class ScreenManager:
    # LCD 마진 설정
    MARGIN_LEFT = 200  # 좌측 마진
    MARGIN_TOP = 300   # 상단 마진

    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        
        # 실제 사용 가능한 화면 크기 계산
        self.usable_width = self.width - self.MARGIN_LEFT
        self.usable_height = self.height - self.MARGIN_TOP
        
        # 배경 이미지를 사용 가능한 영역 크기로 조정
        self.bg_image = pygame.image.load("Image/bg.png")
        self.bg_image = pygame.transform.scale(self.bg_image, (self.usable_width, self.usable_height))
        
        try:
            self.font = pygame.font.Font("Font/RoundSquare.ttf", 74)
        except:
            print("폰트 로드 실패, 기본 폰트 사용")
            self.font = pygame.font.Font(None, 74)
        
        self.message_queue = queue.Queue()

    def draw_text(self, text):
        lines = text.split('\n')
        # 마진을 고려한 시작 y 위치 계산
        y = self.MARGIN_TOP + (self.usable_height // 2 - (len(lines) * 40))
        for line in lines:
            text_surface = self.font.render(line, True, (0, 255, 0))
            # 마진을 고려한 중앙 정렬
            text_rect = text_surface.get_rect()
            text_rect.centerx = self.MARGIN_LEFT + (self.usable_width // 2)
            text_rect.y = y
            self.screen.blit(text_surface, text_rect)
            y += 80

    def update_screen(self, text):
        if threading.current_thread() is threading.main_thread():
            # 화면을 검은색으로 초기화
            self.screen.fill((0, 0, 0))
            # 마진을 고려하여 배경 이미지 표시
            self.screen.blit(self.bg_image, (self.MARGIN_LEFT, self.MARGIN_TOP))
            self.draw_text(text)
            pygame.display.flip()
        else:
            self.message_queue.put(text)

    def process_message_queue(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                # 화면을 검은색으로 초기화
                self.screen.fill((0, 0, 0))
                # 마진을 고려하여 배경 이미지 표시
                self.screen.blit(self.bg_image, (self.MARGIN_LEFT, self.MARGIN_TOP))
                self.draw_text(message)
                pygame.display.flip()
        except queue.Empty:
            pass
