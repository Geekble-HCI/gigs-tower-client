import sys
import time
import os

# 프로젝트 루트 디렉토리 설정
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)
sys.path.append(project_root)

from Module.sound_manager import SoundManager

def test_sounds():
    print(f"Current working directory: {os.getcwd()}")
    sound_mgr = SoundManager()
    
    # List of sounds to test
    sound_list = ['waiting', 'countdown', 'playing', 'score']
    
    # Test each sound
    for sound_name in sound_list:
        print(f"Testing {sound_name} sound...")
        sound_mgr.play_sound(sound_name)
        time.sleep(3)  # Play each sound for 3 seconds
        sound_mgr.stop_sound()
        time.sleep(1)  # Pause between sounds
    
    print("Audio test completed!")

if __name__ == "__main__":
    test_sounds()
