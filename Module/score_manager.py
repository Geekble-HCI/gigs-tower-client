from .sound_manager import SoundManager

class ScoreManager:
    def __init__(self):
        self.sound_manager = SoundManager()
        self.reset_score()
    
    def reset_score(self):
        """점수 초기화"""
        self.total_score = 0
        
    def add_score(self, score):
        """점수 추가"""
        self.total_score += score
        if self.total_score > 100:
            self.total_score = 100
        self.sound_manager.play_sfx('get')
        
    def get_total_score(self):
        """현재까지의 총점 반환"""
        return self.total_score
