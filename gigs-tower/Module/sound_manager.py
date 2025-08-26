import pygame
from paths import snd

class SoundManager:
    _instance = None  # 싱글톤 인스턴스

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print("[SOUND] Initializing SoundManager singleton")
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, game_type=1):
        if self._initialized:
            return
        pygame.mixer.init()
        self._initialized = True
        
        self.game_type = min(max(1, game_type), 6)  # 1~6 사이의 값으로 제한
        
        # BGM 사운드
        self.bgm_sounds = {
            "init":      self._load_sound(snd("init.mp3")),
            "waiting":   self._load_sound(snd("wait.wav")),
            "countdown": self._load_sound(snd("countdown.wav")),
            "playing":   self._load_sound(snd(f"playing_{self.game_type}.wav")),
            "score":     self._load_sound(snd("score.wav")),
            "result":    self._load_sound(snd("result.wav")),
            "enter":     self._load_sound(snd("enter.wav")),    # 새로운 사운드 추가
            "exit":      self._load_sound(snd("exit.wav")),     # 새로운 사운드 추가
        }
        
        # SFX 사운드 (예시)
        self.sfx_sounds = {
            'get': self._load_sound('Sound/get_big.wav'),
        }
        
        self.current_bgm = None
        self.current_sfx = None
        self.volume = 1.0  # Default volume (0.0-1.0)

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
        print(f"[DEBUG] sound name: {sound}")

        if sound:
            self._apply_volume(sound)
            sound.play(0)  # 0은 한번만 재생
            self.current_bgm = sound
            print(f"[DEBUG] current sound name: {self.current_bgm}")

    def play_bgm_loop(self, sound_name):
        if self.current_bgm:
            self.current_bgm.stop()
        
        sound = self.bgm_sounds.get(sound_name)
        if sound:
            self._apply_volume(sound)
            sound.play(-1)
            self.current_bgm = sound

    def play_sfx(self, sound_name):
        sound = self.sfx_sounds.get(sound_name)
        if sound:
            self._apply_volume(sound)
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
    
    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        print(f"[SOUND] Volume set to {self.volume:.2f} ({int(self.volume * 100)}%)")

        if self.current_bgm:
            print(f"[DEBUG] BGM before volume: {self.current_bgm.get_volume()}")
            self.current_bgm.set_volume(self.volume)
            print(f"[DEBUG] BGM after volume: {self.current_bgm.get_volume()}")
        else:
            print("[DEBUG] No BGM currently playing")

        for sfx in self.sfx_sounds.values():
            if sfx:
                sfx.set_volume(self.volume)
    
    def get_volume(self):
        """Get current master volume"""
        return self.volume
    
    def _apply_volume(self, sound):
        """Apply current volume to a sound object"""
        if sound:
            sound.set_volume(self.volume)
