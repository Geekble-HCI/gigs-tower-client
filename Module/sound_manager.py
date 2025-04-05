import pygame

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {
            'init': self._load_sound('Sound/init.mp3'),
            'waiting': self._load_sound('Sound/waiting.mp3'),
            'countdown': self._load_sound('Sound/countdown.mp3'),
            'playing': self._load_sound('Sound/playing.mp3'),
            'score': self._load_sound('Sound/score.mp3'),
            'result': self._load_sound('Sound/result.mp3'),
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
