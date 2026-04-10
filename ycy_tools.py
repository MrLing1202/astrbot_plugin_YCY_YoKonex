import asyncio
import random
from typing import Dict, List, Optional, Any, Callable


class YCYTools:
    def __init__(self, server, waves):
        self.server = server
        self.waves = waves
        self.timers: Dict[str, Any] = {}
        self.quick_fire_increments: Dict[str, Dict[str, int]] = {}

    async def set_strength(self, session_id: str, channel: str, mode: int, value: int):
        if channel not in ["A", "B", "AB"]:
            return
        
        if channel == "AB":
            await self.server.send_strength(session_id, "A", mode, value)
            await self.server.send_strength(session_id, "B", mode, value)
        else:
            await self.server.send_strength(session_id, channel, mode, value)

    async def send_wave(self, session_id: str, channel: str, wave_name: str):
        wave_data = self.waves.get_wave(wave_name)
        if not wave_data:
            return
        
        wave = wave_data["wave"]
        
        if channel == "AB":
            await self.server.send_wave(session_id, "A", wave)
            await self.server.send_wave(session_id, "B", wave)
        elif channel in ["A", "B"]:
            await self.server.send_wave(session_id, channel, wave)

    async def send_wave_combo(self, session_id: str, channel: str, 
                             wave_names: List[str], iterations: int = 1):
        for _ in range(iterations):
            for wave_name in wave_names:
                await self.send_wave(session_id, channel, wave_name)
                await asyncio.sleep(0.1)

    async def send_custom_wave(self, session_id: str, channel: str, wave: List[int]):
        if channel == "AB":
            await self.server.send_wave(session_id, "A", wave)
            await self.server.send_wave(session_id, "B", wave)
        elif channel in ["A", "B"]:
            await self.server.send_wave(session_id, channel, wave)

    async def timed_switch_wave(self, session_id: str, channel: str, 
                                wave_names: List[str], interval: int):
        if session_id in self.timers:
            self._cancel_timer(session_id)

        async def switch_loop():
            current_index = 0
            while True:
                wave_name = wave_names[current_index % len(wave_names)]
                await self.send_wave(session_id, channel, wave_name)
                current_index += 1
                await asyncio.sleep(interval)

        task = asyncio.create_task(switch_loop())
        self.timers[session_id] = task

    async def clear_timed_switch(self, session_id: str):
        self._cancel_timer(session_id)

    def _cancel_timer(self, session_id: str):
        if session_id in self.timers:
            self.timers[session_id].cancel()
            del self.timers[session_id]

    async def quick_fire(self, session_id: str):
        increments = self.quick_fire_increments.get(session_id, {"A": 10, "B": 10})
        await self.server.send_strength(session_id, "A", 1, increments["A"])
        await self.server.send_strength(session_id, "B", 1, increments["B"])

    async def set_quick_fire_increment(self, session_id: str, a: Optional[int] = None, 
                                       b: Optional[int] = None):
        if session_id not in self.quick_fire_increments:
            self.quick_fire_increments[session_id] = {"A": 10, "B": 10}
        
        if a is not None:
            self.quick_fire_increments[session_id]["A"] = max(1, min(30, a))
        if b is not None:
            self.quick_fire_increments[session_id]["B"] = max(1, min(30, b))

    async def get_status(self, session_id: str) -> Dict[str, Any]:
        return self.server.get_status(session_id)

    async def clear_wave(self, session_id: str, channel: str):
        if channel == "AB":
            await self.server.clear_queue(session_id, "A")
            await self.server.clear_queue(session_id, "B")
        elif channel in ["A", "B"]:
            await self.server.clear_queue(session_id, channel)

    async def stop_output(self, session_id: str):
        await self.server.stop_output(session_id)
        await self.clear_timed_switch(session_id)

    async def random_wave(self, session_id: str, channel: str):
        wave_names = self.waves.get_wave_names()
        if wave_names:
            wave_name = random.choice(wave_names)
            await self.send_wave(session_id, channel, wave_name)
            return wave_name
        return None
