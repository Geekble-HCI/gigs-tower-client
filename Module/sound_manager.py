import pygame

class SoundManager:
    def __init__(self, game_type=1):
        pygame.mixer.init()
        self.game_type = min(max(1, game_type), 6)  # 1~6 사이의 값으로 제한
        self.sounds = {
            'init': self._load_sound('Sound/init.mp3'),
            'waiting': self._load_sound('Sound/wait.wav'),
            'countdown': self._load_sound('Sound/countdown.wav'),
            'playing': self._load_sound(f'Sound/playing_{self.game_type}.wav'),
            'score': self._load_sound('Sound/score.wav'),
            'result': self._load_sound('Sound/result.wav'),
        }
        self.current_sound = None

    def _load_sound(self, path):
        try:
            return pygame.mixer.Sound(path)
        except:
            print(f"Failed to load sound: {path}")
            return None

    def play_sound(self, sound_name):
        if self.current_sound:
            self.current_sound.stop()
        
        sound = self.sounds.get(sound_name)
        if sound:
            sound.play(0)  # 0은 한번만 재생
            self.current_sound = sound

    def play_sound_loop(self, sound_name):
        if self.current_sound:
            self.current_sound.stop()
        
        sound = self.sounds.get(sound_name)
        if sound:
            sound.play(-1)
            self.current_sound = sound

    def stop_sound(self):
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound = None
