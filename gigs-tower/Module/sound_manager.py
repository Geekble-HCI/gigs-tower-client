from typing import Dict, Optional
import pygame
from paths import snd

class SoundManager:
    _instance: Optional["SoundManager"] = None  # 싱글톤 인스턴스

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print("[SOUND] Initializing SoundManager singleton")
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self, 
        game_type: int = 1,
        preinit_freq: int = 44100,
        preinit_size: int = -16,
        preinit_channels: int = 2,
        preinit_buffer: int = 512, # 지연 줄이려면 buffer를 512~1024로 조정해서 테스트
        bgm_channel_index: int = 0,
        num_channels: int = 16,  # 동시 재생 채널 수(기본 8 → 16으로 상향)
        base_dir: str = ".",       
    ):
        if self._initialized:
            return
        
        # ---- mixer 사전 설정 (지연/노이즈 트레이드오프) ----
        pygame.mixer.pre_init(
            frequency=preinit_freq,
            size=preinit_size,
            channels=preinit_channels,
            buffer=preinit_buffer,
        )
        pygame.init()
        pygame.mixer.init()

        # 채널 수 확장(필요 시)
        pygame.mixer.set_num_channels(num_channels)

        self._initialized = True
        
        self.game_type = min(max(1, game_type), 6)  # 1~6 사이의 값으로 제한
        self.muted: bool = False
        self.volume: float = 1.0

        # ---- BGM 전용 채널/사운드 핸들 ----
        self.bgm_channel = pygame.mixer.Channel(bgm_channel_index)
        self.current_bgm: Optional[pygame.mixer.Sound] = None
        
        # BGM 사운드
        self.bgm_sounds: Dict[str, Optional[pygame.mixer.Sound]] = {
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
        self.sfx_sounds: Dict[str, Optional[pygame.mixer.Sound]] = {
            'get': self._load_sound('Sound/get_big.wav'),
        }

        self._apply_bgm_volume()
        
        # self.current_bgm = None
        # self.current_sfx = None
        # self.volume = 1.0  # Default volume (0.0-1.0)

    # ---- 내부 유틸 ----
    def _load_sound(self, path: str) -> Optional[pygame.mixer.Sound]:
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"[SOUND][ERROR] failed to load: {path} ({e})")
            return None
        
    def _effective_volume(self) -> float:
        return 0.0 if self.muted else self.volume
    
    def _apply_bgm_volume(self) -> None:
        """BGM 채널 볼륨 즉시 반영 (재생 중인 소리에도 즉시 적용)"""
        self.bgm_channel.set_volume(self._effective_volume())
    
    def _apply_sfx_volume_to(self, ch: pygame.mixer.Channel) -> None:
        ch.set_volume(self._effective_volume())

    # ---- 퍼블릭 API ----
    def play_bgm(self, name: str) -> None:
        snd = self.bgm_sounds.get(name)
        if not snd:
            print(f"[SOUND][WARN] BGM not found: {name}")
            return
        # 현재 BGM 중지 후 교체
        self.bgm_channel.stop()
        self.current_bgm = snd
        self._apply_bgm_volume()
        self.bgm_channel.play(snd, loops=0)

    def play_bgm_loop(self, name: str) -> None:
        snd = self.bgm_sounds.get(name)
        if not snd:
            print(f"[SOUND][WARN] BGM not found: {name}")
            return
        self.bgm_channel.stop()
        self.current_bgm = snd
        self._apply_bgm_volume()
        self.bgm_channel.play(snd, loops=-1)

        # if self.current_bgm:
        #     self.current_bgm.stop()
        
        # sound = self.bgm_sounds.get(sound_name)
        # if sound:
        #     self._apply_volume(sound)
        #     sound.play(-1)
        #     self.current_bgm = sound

    def stop_bgm(self) -> None:
        self.bgm_channel.stop()
        self.current_bgm = None
    
        # if self.current_bgm:
        #     self.current_bgm.stop()
        #     self.current_bgm = None
    
    def fadeout_bgm(self, ms: int = 200) -> None:
        """클릭/팝 노이즈 완화용 페이드아웃"""
        self.bgm_channel.fadeout(ms)
        self.current_bgm = None

    def play_sfx(self, name: str) -> None:
        snd = self.sfx_sounds.get(name)
        if not snd:
            print(f"[SOUND][WARN] SFX not found: {name}")
            return
        ch = pygame.mixer.find_channel()
        if ch is None:
            print("[SOUND][WARN] no free SFX channel")
            return
        self._apply_sfx_volume_to(ch)
        ch.play(snd, loops=0) # SFX는 한번만 재생

    def stop_all(self) -> None:
        self.stop_bgm()
        for i in range(pygame.mixer.get_num_channels()):
            pygame.mixer.Channel(i).stop()
    
   # ---- 볼륨/뮤트 ----
    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, float(volume)))
        print(f"[SOUND] Volume {self.volume:.2f} ({int(self.volume * 100)}%)")
        self._refresh_all_volumes()

    def get_volume(self) -> float:
        return self.volume

    def mute(self) -> None:
        self.muted = True
        self._refresh_all_volumes()
        print("[SOUND] Muted")

    def unmute(self) -> None:
        self.muted = False
        self._refresh_all_volumes()
        print("[SOUND] Unmuted")

    def toggle_mute(self) -> None:
        if self.is_muted():
            self.unmute()
        else:
            self.mute()

    def is_muted(self) -> bool:
        return self.muted

    def _refresh_all_volumes(self) -> None:
        """현재 상태(뮤트/볼륨)를 모든 채널/사운드에 반영"""
        # BGM은 채널 기준으로 즉시 반영
        self._apply_bgm_volume()
        # SFX는 다음 재생 채널에 반영되도록 기본 볼륨만 유지
        # 이미 재생 중인 SFX에 대해서도 즉시 반영하고 싶다면 모든 채널 순회:
        for i in range(pygame.mixer.get_num_channels()):
            ch = pygame.mixer.Channel(i)
            # BGM 채널이면 이미 처리됨
            if ch is self.bgm_channel:
                continue
            if ch.get_busy():
                ch.set_volume(self._effective_volume())

    # ---- 자원 정리 ----
    def quit(self) -> None:
        """프로세스 종료 전 자원 정리(선택적)"""
        try:
            self.stop_all()
            pygame.mixer.quit()
            pygame.quit()
            self._initialized = False
            SoundManager._instance = None
            print("[SOUND] Quit")
        except Exception as e:
            print(f"[SOUND][ERROR] quit failed: {e}")