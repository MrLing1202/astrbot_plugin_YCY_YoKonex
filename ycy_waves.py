from typing import Dict, List, Any
import os
import json


class YCYWaves:
    def __init__(self, waveforms_dir: str, uploaded_wave_files: List[str] = None):
        self.waveforms_dir = waveforms_dir
        self.uploaded_wave_files = uploaded_wave_files or []
        self.waves = {}
        self._init_builtin_waves()
        self._load_uploaded_waves()

    def _init_builtin_waves(self):
        self.waves["breathe"] = {
            "name": "呼吸",
            "duration": 4000,
            "wave": self._generate_breathe_wave()
        }
        self.waves["tide"] = {
            "name": "潮汐",
            "duration": 8000,
            "wave": self._generate_tide_wave()
        }
        self.waves["combo"] = {
            "name": "连击",
            "duration": 2000,
            "wave": self._generate_combo_wave()
        }
        self.waves["fast_pinch"] = {
            "name": "快速按捏",
            "duration": 3000,
            "wave": self._generate_fast_pinch_wave()
        }
        self.waves["pinch_crescendo"] = {
            "name": "按捏渐强",
            "duration": 5000,
            "wave": self._generate_pinch_crescendo_wave()
        }
        self.waves["heartbeat"] = {
            "name": "心跳节奏",
            "duration": 3000,
            "wave": self._generate_heartbeat_wave()
        }
        self.waves["compress"] = {
            "name": "压缩",
            "duration": 4000,
            "wave": self._generate_compress_wave()
        }
        self.waves["rhythm_step"] = {
            "name": "节奏步伐",
            "duration": 4000,
            "wave": self._generate_rhythm_step_wave()
        }

    def _generate_breathe_wave(self) -> List[int]:
        wave = []
        for i in range(40):
            if i < 20:
                strength = int(i * 5)
            else:
                strength = int((40 - i) * 5)
            wave.extend([strength, 0] * 5)
        return wave

    def _generate_tide_wave(self) -> List[int]:
        wave = []
        for i in range(80):
            if i < 40:
                strength = int(i * 2.5)
            else:
                strength = int((80 - i) * 2.5)
            wave.extend([strength, 0] * 5)
        return wave

    def _generate_combo_wave(self) -> List[int]:
        wave = []
        for i in range(10):
            wave.extend([30, 0, 30, 0, 10, 0, 30, 0, 30, 0, 0, 0])
        return wave

    def _generate_fast_pinch_wave(self) -> List[int]:
        wave = []
        for i in range(30):
            wave.extend([40, 0, 20, 0])
        return wave

    def _generate_pinch_crescendo_wave(self) -> List[int]:
        wave = []
        for i in range(50):
            strength = int(i * 2)
            wave.extend([strength, 0, int(strength * 0.5), 0])
        return wave

    def _generate_heartbeat_wave(self) -> List[int]:
        wave = []
        for i in range(15):
            wave.extend([50, 0, 0, 0, 30, 0, 0, 0, 0, 0])
        return wave

    def _generate_compress_wave(self) -> List[int]:
        wave = []
        for i in range(40):
            if i < 20:
                strength = int(50 - i * 2)
            else:
                strength = int(10 + (i - 20) * 2)
            wave.extend([strength, 0] * 5)
        return wave

    def _generate_rhythm_step_wave(self) -> List[int]:
        wave = []
        pattern = [40, 0, 0, 0, 20, 0, 20, 0, 0, 0]
        for i in range(20):
            wave.extend(pattern)
        return wave

    def _load_uploaded_waves(self):
        if not self.uploaded_wave_files:
            return
        
        if not os.path.exists(self.waveforms_dir):
            os.makedirs(self.waveforms_dir)
        
        for filename in self.uploaded_wave_files:
            filepath = os.path.join(self.waveforms_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "name" in data and "wave" in data:
                            wave_name = filename.replace(".json", "").replace(".pulse", "")
                            self.waves[wave_name] = {
                                "name": data.get("name", wave_name),
                                "duration": data.get("duration", len(data.get("wave", [])) * 10),
                                "wave": data.get("wave", [])
                            }
                except Exception as e:
                    print(f"加载波形文件 {filename} 失败: {e}")

    def get_wave_names(self) -> List[str]:
        return list(self.waves.keys())

    def get_wave(self, name: str) -> Optional[Dict[str, Any]]:
        return self.waves.get(name)

    def get_wave_info(self, name: str) -> Optional[Dict[str, Any]]:
        wave = self.get_wave(name)
        if wave:
            return {
                "name": wave["name"],
                "duration": wave["duration"],
                "frame_count": len(wave["wave"]),
                "first_frame": wave["wave"][:5] if wave["wave"] else [],
                "last_frame": wave["wave"][-5:] if wave["wave"] else []
            }
        return None
