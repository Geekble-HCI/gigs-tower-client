import pygame

class SoundManager:
    def __init__(self, game_type=1):
        pygame.mixer.init()
        self.game_type = min(max(1, game_type), 6)  # 1~6 사이의 값으로 제한
        
        # BGM 사운드
        self.bgm_sounds = {
            'init': self._load_sound('Sound/init.mp3'),
            'waiting': self._load_sound('Sound/wait.wav'),
            'countdown': self._load_sound('Sound/countdown.wav'),
            'playing': self._load_sound(f'Sound/playing_{self.game_type}.wav'),
            'score': self._load_sound('Sound/score.wav'),
            'result': self._load_sound('Sound/result.wav'),
            'enter': self._load_sound('Sound/enter.wav'),  # 새로운 사운드 추가
            'exit': self._load_sound('Sound/exit.wav'),    # 새로운 사운드 추가
        }
        
        # SFX 사운드 (예시)
        self.sfx_sounds = {
            'get': self._load_sound('Sound/get_big.wav'),
        }
        
        self.current_bgm = None
        self.current_sfx = None

    def _load_sound(self, path):
        try:
            return pygame.mixer.Sound(path)
        except:
            print(f"Failed to load sound: {path}")
            return None

    def play_bgm(self, sound_name):
        if self.current_bgm:
            self.current_bgm.stop()
        
        sound = self.bgm_sounds.get(sound_name)
        if sound:
            sound.play(0)  # 0은 한번만 재생
            self.current_bgm = sound

    def play_bgm_loop(self, sound_name):
        if self.current_bgm:
            self.current_bgm.stop()
        
        sound = self.bgm_sounds.get(sound_name)
        if sound:
            sound.play(-1)
            self.current_bgm = sound

    def play_sfx(self, sound_name):
        sound = self.sfx_sounds.get(sound_name)
        if sound:
            sound.play(0)  # SFX는 한번만 재생

    def stop_bgm(self):
        if self.current_bgm:
            self.current_bgm.stop()
            self.current_bgm = None

    def stop_all(self):
        self.stop_bgm()
        for sound in self.sfx_sounds.values():
            if sound:
                sound.stop()
