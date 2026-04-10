import os
import asyncio
import time
from typing import Dict, List, Optional, Any
from astrbot.api.star import Star, register
from astrbot.api.event import MessageEvent, MessageChain, Plain, Image
from astrbot.api.platform import Platform
from astrbot.api.message_components import Source

from ycy_server import YCYServer
from ycy_waves import YCYWaves
from ycy_tools import YCYTools
from billing_db import BillingDB
from afdian_api import AfdianAPI


@register
class YCYPlugin(Star):
    name = "ycy"
    description = "役次元玩具控制插件，让大模型控制你的役次元设备"
    author = "YCY-YOKONEX"
    version = "1.0.0"

    def __init__(self):
        self.config = {}
        self.server: Optional[YCYServer] = None
        self.waves: Optional[YCYWaves] = None
        self.tools: Optional[YCYTools] = None
        self.db: Optional[BillingDB] = None
        self.afdian: Optional[AfdianAPI] = None
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.data_dir = None
        self.waveforms_dir = None
        self.server_running = False
        self.server_start_lock = asyncio.Lock()
        self.active_sessions = set()
        self.shared_persona_id = None

    async def on_load(self):
        self.config = self.get_config()
        self.data_dir = os.path.join(self.get_data_dir(), "data")
        self.waveforms_dir = os.path.join(self.get_data_dir(), "waveforms")
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.waveforms_dir):
            os.makedirs(self.waveforms_dir)
        
        self.db = BillingDB(self.data_dir)
        self.waves = YCYWaves(
            self.waveforms_dir,
            self.config.get("uploaded_wave_files", [])
        )
        
        if self.config.get("afdian", {}).get("user_id") and self.config.get("afdian", {}).get("token"):
            self.afdian = AfdianAPI(
                self.config.get("afdian", {}).get("base_url", "https://afdian.com/api/open"),
                self.config.get("afdian", {}).get("user_id", ""),
                self.config.get("afdian", {}).get("token", "")
            )

        print("役次元插件已加载")

    async def on_unload(self):
        if self.server:
            await self.server.stop()
        print("役次元插件已卸载")

    @register.command("ycy")
    async def ycy_command(self, event: MessageEvent, args: List[str]):
        if not args:
            await self.show_help(event)
            return

        cmd = args[0].lower()
        
        if cmd == "help":
            await self.show_help(event)
        elif cmd == "start":
            await self.start_ycy_mode(event)
        elif cmd == "stop":
            await self.stop_ycy_mode(event)
        elif cmd == "status":
            await self.show_status(event)
        elif cmd == "channel":
            await self.set_channel(event, args[1:])
        elif cmd == "part":
            await self.set_part(event, args[1:])
        elif cmd == "fire":
            await self.set_fire(event, args[1:])
        elif cmd == "wavelist":
            await self.show_wave_list(event)
        elif cmd == "waveinfo":
            await self.show_wave_info(event, args[1:])
        elif cmd == "quota":
            await self.show_quota(event)
        elif cmd == "redeem":
            await self.redeem(event, args[1:])
        elif cmd == "quota-list":
            await self.show_quota_list(event, args[1:])
        elif cmd == "redeem-list":
            await self.show_redeem_list(event, args[1:])
        elif cmd == "recharge":
            await self.recharge(event, args[1:])
        elif cmd == "refresh-free":
            await self.refresh_free(event, args[1:])
        else:
            await event.reply(MessageChain([Plain("未知命令，请使用 /ycy help 查看帮助")]))

    async def show_help(self, event: MessageEvent):
        help_text = """役次元玩具控制插件帮助

普通用户命令：
/ycy help - 查看帮助
/ycy start - 开启役次元模式
/ycy stop - 关闭役次元模式
/ycy status - 查看状态
/ycy channel A|B|AB - 设置可用通道
/ycy part A:部位 B:部位 - 设置部位描述
/ycy fire [强度] 或 /ycy fire A:强度 B:强度 - 设置一键开火增量
/ycy wavelist - 查看波形列表
/ycy waveinfo <波形名> - 查看波形信息
/ycy quota - 查看自己的额度
/ycy redeem <订单号> - 兑换爱发电订单

管理员命令：
/ycy quota-list [user_id=xxx] [limit=50] - 查看额度记录
/ycy redeem-list [user_id=xxx] [order_id=xxx] [limit=50] - 查看兑换记录
/ycy recharge user_id=123 amount=6.66 - 手动充值
/ycy refresh-free user_id=123 - 刷新免费额度
/ycy refresh-free all=true - 刷新所有用户免费额度"""
        await event.reply(MessageChain([Plain(help_text)]))

    async def start_ycy_mode(self, event: MessageEvent):
        session_id = event.get_sender().get_id()
        if session_id in self.sessions:
            await event.reply(MessageChain([Plain("你已经在役次元模式中了")]))
            return

        await self._ensure_server_started()

        self.sessions[session_id] = {
            "channel": "AB",
            "parts": {"A": "A通道", "B": "B通道"},
            "fire_increment": {"A": 10, "B": 10}
        }
        self.active_sessions.add(session_id)

        await self._create_or_update_shared_persona()

        qrcode_url = self.server.get_qrcode_url()
        await event.reply(MessageChain([
            Plain(f"役次元模式已开启！\n请扫描二维码或访问：{qrcode_url}\n绑定设备后即可使用")
        ]))

    async def stop_ycy_mode(self, event: MessageEvent):
        session_id = event.get_sender().get_id()
        if session_id not in self.sessions:
            await event.reply(MessageChain([Plain("你不在役次元模式中")]))
            return

        if self.tools:
            await self.tools.stop_output(session_id)

        del self.sessions[session_id]
        self.active_sessions.discard(session_id)

        await self._check_and_stop_server()
        await self._check_and_delete_shared_persona()

        await event.reply(MessageChain([Plain("役次元模式已关闭")]))

    async def show_status(self, event: MessageEvent):
        session_id = event.get_sender().get_id()
        if session_id not in self.sessions:
            await event.reply(MessageChain([Plain("你不在役次元模式中")]))
            return

        status = self.server.get_status(session_id) if self.server else {"connected": False}
        session_info = self.sessions[session_id]
        
        status_text = f"""役次元状态
已连接: {status.get('connected', False)}
已绑定: {status.get('bound', False)}
通道: {session_info['channel']}
A通道: {status.get('strength_a', 0)}/{status.get('limit_a', 0)} - {session_info['parts']['A']}
B通道: {status.get('strength_b', 0)}/{status.get('limit_b', 0)} - {session_info['parts']['B']}
一键开火增量: A={session_info['fire_increment']['A']}, B={session_info['fire_increment']['B']}"""
        await event.reply(MessageChain([Plain(status_text)]))

    async def set_channel(self, event: MessageEvent, args: List[str]):
        session_id = event.get_sender().get_id()
        if session_id not in self.sessions:
            await event.reply(MessageChain([Plain("请先开启役次元模式")]))
            return

        if not args:
            await event.reply(MessageChain([Plain("请指定通道：A、B 或 AB")]))
            return

        channel = args[0].upper()
        if channel not in ["A", "B", "AB"]:
            await event.reply(MessageChain([Plain("通道只能是 A、B 或 AB")]))
            return

        self.sessions[session_id]["channel"] = channel
        await event.reply(MessageChain([Plain(f"通道已设置为 {channel}")]))

    async def set_part(self, event: MessageEvent, args: List[str]):
        session_id = event.get_sender().get_id()
        if session_id not in self.sessions:
            await event.reply(MessageChain([Plain("请先开启役次元模式")]))
            return

        if not args:
            await event.reply(MessageChain([Plain("请指定部位，例如：A:左手 B:右手")]))
            return

        parts = self.sessions[session_id]["parts"]
        for arg in args:
            if ":" in arg:
                channel, part = arg.split(":", 1)
                channel = channel.upper()
                if channel in ["A", "B"]:
                    parts[channel] = part

        self.sessions[session_id]["parts"] = parts
        await event.reply(MessageChain([Plain(f"部位已设置：A={parts['A']}, B={parts['B']}")]))

    async def set_fire(self, event: MessageEvent, args: List[str]):
        session_id = event.get_sender().get_id()
        if session_id not in self.sessions:
            await event.reply(MessageChain([Plain("请先开启役次元模式")]))
            return

        if not args:
            await event.reply(MessageChain([Plain("请指定强度，例如：10 或 A:8 B:12")]))
            return

        increments = self.sessions[session_id]["fire_increment"]
        
        if len(args) == 1 and ":" not in args[0]:
            try:
                value = max(1, min(30, int(args[0])))
                increments["A"] = value
                increments["B"] = value
            except ValueError:
                await event.reply(MessageChain([Plain("强度必须是 1-30 的数字")]))
                return
        else:
            for arg in args:
                if ":" in arg:
                    channel, val = arg.split(":", 1)
                    channel = channel.upper()
                    if channel in ["A", "B"]:
                        try:
                            value = max(1, min(30, int(val)))
                            increments[channel] = value
                        except ValueError:
                            pass

        self.sessions[session_id]["fire_increment"] = increments
        await event.reply(MessageChain([Plain(f"一键开火增量已设置：A={increments['A']}, B={increments['B']}")]))

    async def show_wave_list(self, event: MessageEvent):
        wave_names = self.waves.get_wave_names()
        if not wave_names:
            await event.reply(MessageChain([Plain("没有可用的波形")]))
            return

        wave_list = "\n".join([f"- {name}: {self.waves.get_wave(name)['name']}" for name in wave_names])
        await event.reply(MessageChain([Plain(f"可用波形：\n{wave_list}")]))

    async def show_wave_info(self, event: MessageEvent, args: List[str]):
        if not args:
            await event.reply(MessageChain([Plain("请指定波形名称")]))
            return

        wave_name = args[0]
        info = self.waves.get_wave_info(wave_name)
        if not info:
            await event.reply(MessageChain([Plain(f"波形 {wave_name} 不存在")]))
            return

        info_text = f"""波形信息
名称: {info['name']}
时长: {info['duration']}ms
帧数: {info['frame_count']}
首帧: {info['first_frame']}
末帧: {info['last_frame']}"""
        await event.reply(MessageChain([Plain(info_text)]))

    async def show_quota(self, event: MessageEvent):
        user_id = event.get_sender().get_id()
        self._check_and_refresh_free_quota(user_id)
        
        quota = self.db.get_user_quota(user_id)
        total = quota["free_quota"] + quota["paid_quota"]
        last_refresh = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(quota["last_refresh_ts"])) if quota["last_refresh_ts"] else "从未刷新"
        next_refresh = self._get_next_refresh_time(quota["last_refresh_ts"])
        
        quota_text = f"""额度信息
免费额度: {quota['free_quota']}
付费额度: {quota['paid_quota']}
总额度: {total}
上次刷新: {last_refresh}
下次刷新: {next_refresh}"""
        await event.reply(MessageChain([Plain(quota_text)]))

    async def redeem(self, event: MessageEvent, args: List[str]):
        if not args:
            await event.reply(MessageChain([Plain("请提供爱发电订单号")]))
            return

        if not self.afdian:
            await event.reply(MessageChain([Plain("爱发电功能未配置，请联系管理员")]))
            return

        order_id = args[0]
        user_id = event.get_sender().get_id()

        if self.db.is_order_redeemed(order_id):
            await event.reply(MessageChain([Plain("该订单已经兑换过了")]))
            return

        order_data = self.afdian.get_order_by_id(order_id)
        if not order_data:
            await event.reply(MessageChain([Plain("订单不存在或查询失败")]))
            return

        show_amount = order_data.get("show_amount")
        total_amount = order_data.get("total_amount")
        amount = show_amount if show_amount is not None else total_amount

        if amount is None:
            await event.reply(MessageChain([Plain("订单金额无效")]))
            return

        token_per_yuan = self.config.get("billing", {}).get("token_per_yuan", 1000)
        token_amount = int(amount * token_per_yuan)

        quota = self.db.get_user_quota(user_id)
        self.db.update_user_quota(user_id, paid_quota=quota["paid_quota"] + token_amount)
        self.db.redeem_order(order_id, user_id, token_amount)

        await event.reply(MessageChain([Plain(f"兑换成功！获得 {token_amount} TOKEN")]))

    async def show_quota_list(self, event: MessageEvent, args: List[str]):
        if not await self._is_admin(event):
            await event.reply(MessageChain([Plain("此命令仅限管理员使用")]))
            return

        user_id = None
        limit = 50
        
        for arg in args:
            if arg.startswith("user_id="):
                user_id = arg.split("=", 1)[1]
            elif arg.startswith("limit="):
                try:
                    limit = int(arg.split("=", 1)[1])
                except ValueError:
                    pass

        records = self.db.get_all_quota_records(limit)
        if not records:
            await event.reply(MessageChain([Plain("没有额度记录")]))
            return

        if user_id:
            records = [r for r in records if r.get("user_id") == user_id]

        list_text = "额度记录：\n"
        for r in records:
            total = r.get("free_quota", 0) + r.get("paid_quota", 0)
            list_text += f"\n用户 {r['user_id']}: 免费={r.get('free_quota', 0)}, 付费={r.get('paid_quota', 0)}, 总计={total}"
        
        await event.reply(MessageChain([Plain(list_text)]))

    async def show_redeem_list(self, event: MessageEvent, args: List[str]):
        if not await self._is_admin(event):
            await event.reply(MessageChain([Plain("此命令仅限管理员使用")]))
            return

        user_id = None
        order_id = None
        limit = 50
        
        for arg in args:
            if arg.startswith("user_id="):
                user_id = arg.split("=", 1)[1]
            elif arg.startswith("order_id="):
                order_id = arg.split("=", 1)[1]
            elif arg.startswith("limit="):
                try:
                    limit = int(arg.split("=", 1)[1])
                except ValueError:
                    pass

        records = self.db.get_all_redeem_records(user_id, order_id, limit)
        if not records:
            await event.reply(MessageChain([Plain("没有兑换记录")]))
            return

        list_text = "兑换记录：\n"
        for r in records:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r.get("ts", 0)))
            list_text += f"\n订单 {r['order_id']}: 用户={r['user_id']}, 金额={r['amount']}, 时间={ts}"
        
        await event.reply(MessageChain([Plain(list_text)]))

    async def recharge(self, event: MessageEvent, args: List[str]):
        if not await self._is_admin(event):
            await event.reply(MessageChain([Plain("此命令仅限管理员使用")]))
            return

        user_id = None
        amount = None
        
        for arg in args:
            if arg.startswith("user_id="):
                user_id = arg.split("=", 1)[1]
            elif arg.startswith("amount="):
                try:
                    amount = float(arg.split("=", 1)[1])
                except ValueError:
                    pass

        if not user_id or amount is None:
            await event.reply(MessageChain([Plain("请提供 user_id 和 amount 参数")]))
            return

        token_per_yuan = self.config.get("billing", {}).get("token_per_yuan", 1000)
        token_amount = int(amount * token_per_yuan)

        quota = self.db.get_user_quota(user_id)
        self.db.update_user_quota(user_id, paid_quota=quota["paid_quota"] + token_amount)

        await event.reply(MessageChain([Plain(f"充值成功！用户 {user_id} 获得 {token_amount} TOKEN")]))

    async def refresh_free(self, event: MessageEvent, args: List[str]):
        if not await self._is_admin(event):
            await event.reply(MessageChain([Plain("此命令仅限管理员使用")]))
            return

        refresh_all = False
        user_id = None
        
        for arg in args:
            if arg == "all=true":
                refresh_all = True
            elif arg.startswith("user_id="):
                user_id = arg.split("=", 1)[1]

        free_quota_amount = self.config.get("billing", {}).get("free_quota_amount", 1000)
        now = int(time.time())

        if refresh_all:
            records = self.db.get_all_quota_records()
            count = 0
            for r in records:
                uid = r.get("user_id")
                self.db.update_user_quota(uid, free_quota=free_quota_amount, last_refresh_ts=now)
                count += 1
            await event.reply(MessageChain([Plain(f"已刷新 {count} 个用户的免费额度")]))
        elif user_id:
            self.db.update_user_quota(user_id, free_quota=free_quota_amount, last_refresh_ts=now)
            await event.reply(MessageChain([Plain(f"用户 {user_id} 的免费额度已刷新")]))
        else:
            await event.reply(MessageChain([Plain("请提供 user_id 或 all=true 参数")]))

    async def _ensure_server_started(self):
        if self.server_running:
            return

        async with self.server_start_lock:
            if self.server_running:
                return

            host = self.config.get("ws_host", "0.0.0.0")
            port = self.config.get("ws_port", 5555)
            external_host = self.config.get("ws_external_host")
            max_strength_a = self.config.get("max_strength_a", 200)
            max_strength_b = self.config.get("max_strength_b", 200)

            self.server = YCYServer(host, port, external_host, max_strength_a, max_strength_b)
            self.tools = YCYTools(self.server, self.waves)
            await self.server.start()
            self.server_running = True

    async def _check_and_stop_server(self):
        if self.active_sessions:
            return

        if self.server:
            await self.server.stop()
            self.server = None
            self.tools = None
            self.server_running = False

    async def _create_or_update_shared_persona(self):
        system_prompt = self.config.get("ycy_persona_system_prompt")
        if not system_prompt:
            return

        persona_id = self.config.get("ycy_persona_id", "ycy_persona")
        begin_dialogs = self.config.get("ycy_persona_begin_dialogs", [])

        try:
            from astrbot.api.persona import PersonaManager
            persona_mgr = PersonaManager()
            
            existing = persona_mgr.get_persona(persona_id)
            if existing:
                persona_mgr.delete_persona(persona_id)
            
            persona_mgr.create_persona(
                persona_id=persona_id,
                name="役次元控制助手",
                prompt=system_prompt,
                dialogs=begin_dialogs
            )
            self.shared_persona_id = persona_id
        except Exception as e:
            print(f"创建人格失败: {e}")

    async def _check_and_delete_shared_persona(self):
        if self.active_sessions or not self.shared_persona_id:
            return

        try:
            from astrbot.api.persona import PersonaManager
            persona_mgr = PersonaManager()
            persona_mgr.delete_persona(self.shared_persona_id)
            self.shared_persona_id = None
        except Exception as e:
            print(f"删除人格失败: {e}")

    def _check_and_refresh_free_quota(self, user_id: str):
        quota = self.db.get_user_quota(user_id)
        refresh_hours = self.config.get("billing", {}).get("free_refresh_hours", 24)
        free_quota_amount = self.config.get("billing", {}).get("free_quota_amount", 1000)
        now = int(time.time())

        if quota["last_refresh_ts"] == 0 or now - quota["last_refresh_ts"] >= refresh_hours * 3600:
            self.db.update_user_quota(user_id, free_quota=free_quota_amount, last_refresh_ts=now)

    def _get_next_refresh_time(self, last_ts: int) -> str:
        if not last_ts:
            return "下次使用时刷新"
        refresh_hours = self.config.get("billing", {}).get("free_refresh_hours", 24)
        next_ts = last_ts + refresh_hours * 3600
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(next_ts))

    async def _is_admin(self, event: MessageEvent) -> bool:
        try:
            return self.context.get_platform().is_admin(event.get_sender().get_id())
        except:
            return False
