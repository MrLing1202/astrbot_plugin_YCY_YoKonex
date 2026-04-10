# 役次元玩具控制插件

让大模型控制你的役次元设备！本插件将大模型与役次元主机的控制完美融合，开启前所未有的沉浸式体验！

## ✨ 核心亮点

- **沉浸式对话体验**：与大模型聊天时，每句话都能触发独特的脉冲回应，让对话充满惊喜与节奏感。
- **智能强度惊喜**：大模型自主掌控每一次强度调节，带来未知惊喜，只能从对话中揣测节奏，确保渐进舒适。
- **智能波形创作**：大模型根据对话自主编排和生成独特波形，从呼吸般的温柔到心跳般的激情，全凭创意打造独一无二的脉冲体验。
- **专属人格空间**：自动启用专用人格，不影响正常使用。

## 🎮 功能概览

### 役次元模式会话管理
- 支持 `/ycy start`、`/ycy stop`
- 状态查看、通道配置、部位配置
- 一键开火增量设置

### 动态 LLM 工具
役次元模式启用后，模型可调用：
- 波形发送
- 强度设置
- 停止输出
- 清空队列
- 自定义波形
- 定时切换波形
- 一键开火
- 随机波形

### 波形扩展
- 支持内置波形
- 支持上传波形文件扩展波形列表

### 额度计费系统
- 支持免费额度、付费额度（发电额度）
- 模型倍率、群聊免计费、仅役次元模式计费

### 爱发电兑换
- 用户可通过订单号把爱发电金额兑换成付费 TOKEN

### 管理员充值
- 管理员可直接为指定用户充值，并自动留下充值记录

## ⚠️ 重要说明

在执行以下操作前：
- 重载插件
- 停用插件

请先确保所有客户端都已经执行 `/ycy stop` 退出役次元模式。

否则可能出现：
- WS 服务未能及时释放端口占用，插件重载后无法重新绑定端口

如果已经发生端口占用，需要手动处理占用进程后再重载插件。

## 📋 环境要求

- AstrBot
- 役次元 APP

## 📦 安装

1. 打开 AstrBot 插件市场
2. 点击右下方加号(安装插件)
3. 选择从链接安装，输入 `https://github.com/MrLing1202/astrbot_plugin_YCY_YoKonex`
4. 点击安装

## ⚙️ 配置

插件主要配置位于 `_conf_schema.json`。

### 基础配置

- `ws_host`: WebSocket 监听地址，默认 `0.0.0.0`
- `ws_port`: WebSocket 监听端口，默认 `5555`
- `ws_external_host`: 生成二维码时使用的可访问地址
- `send_qr_raw_url`: 发送二维码时是否附带绑定链接
- `max_strength_a`: A 通道最大强度
- `max_strength_b`: B 通道最大强度
- `ycy_persona_id`: 役次元共享人格 ID
- `ycy_persona_system_prompt`: 役次元人格提示词
- `ycy_persona_begin_dialogs`: 役次元人格预设对话
- `ycy_persona_error_reply`: 人格切换失败提示
- `ycy_default_persona_id`: 退出役次元后默认恢复的人格
- `uploaded_wave_files`: 上传的波形文件列表

### 爱发电配置

- `afdian.base_url`: 爱发电开放平台 API 地址，默认 `https://afdian.com/api/open`
- `afdian.user_id`: 爱发电开放平台 user_id
- `afdian.token`: 爱发电开放平台 token

### 计费配置

- `billing.enabled`: 是否开启自动计费，默认 `false`
- `billing.free_quota_amount`: 免费额度
- `billing.free_refresh_hours`: 免费额度刷新周期，单位小时
- `billing.token_per_yuan`: 每 1 元可兑换多少 TOKEN
- `billing.charge_only_in_ycy_mode`: 是否仅在役次元模式下计费
- `billing.skip_group_chat_billing`: 是否群聊不计费
- `billing.insufficient_balance_reply`: 余额不足时的提示文案
- `billing.provider_multipliers`: Provider 倍率规则列表，按当前会话的大模型提供商 id 精确匹配

## 📝 命令

### 普通用户命令

- `/ycy help` - 查看役次元指令组帮助
- `/ycy start` - 开启役次元模式，返回二维码用于 APP 绑定
- `/ycy stop` - 关闭役次元模式，将 AB 通道强度归零，取消工具注册
- `/ycy status` - 查看当前役次元状态
- `/ycy channel A|B|AB` - 设置可用通道
- `/ycy part A:部位 B:部位` - 设置通道对应部位描述
- `/ycy fire [强度]` 或 `/ycy fire A:强度 B:强度` - 设置一键开火临时增量（范围 1-30），仅影响会话内一键开火工具
- `/ycy wavelist` - 查看当前可用波形（内置 + 用户上传）
- `/ycy waveinfo <波形名>` - 查看指定波形详细信息（帧数、总时长、首末帧）
- `/ycy quota` - 查看自己的免费额度、付费额度（发电额度）、总额度和刷新时间
- `/ycy redeem <订单号>` - 兑换爱发电订单为付费 TOKEN

### 管理员命令

- `/ycy quota-list [user_id=xxx] [limit=50]` - 查看额度记录
- `/ycy redeem-list [user_id=xxx] [order_id=xxx] [limit=50]` - 查看充值记录
- `/ycy recharge user_id=123 amount=6.66` - 手动为指定用户充值
- `/ycy refresh-free user_id=123` - 立即刷新指定用户的免费额度
- `/ycy refresh-free all=true` - 立即刷新当前所有已有额度记录用户的免费额度

## 📊 计费规则

计费用户以消息发送者 ID 为准，不按会话 ID 计费。

免费额度为惰性刷新：新用户首次命中时发放首份免费额度；到达刷新周期后，首次命中时重置为配置值。

管理员可通过 `/ycy refresh-free user_id=xxx` 或 `/ycy refresh-free all=true` 立即刷新免费额度，这会把免费额度重置为当前配置值并更新时间。

自动计费时，优先扣免费额度。如果免费额度不足，本次只会把免费额度扣到 0，不会立即扣付费额度（发电额度）；下一次请求才会开始扣付费额度（发电额度）。

付费额度（发电额度）最低只扣到 0，不会出现负数。

群聊是否计费、是否只在役次元模式计费，都由 billing 配置控制。

## 💡 爱发电兑换与充值

`/ycy redeem <订单号>` 只接受支付成功的订单。

金额优先使用 show_amount，缺失时回退到 total_amount。

兑换结果按 `floor(金额 * billing.token_per_yuan)` 计算。

同一订单只允许兑换一次。

管理员手动充值会写入充值记录，source 为 manual_admin。

管理员手动充值记录的 order_id 格式为 `manual:{admin_id}:{user_id}:{ts}`。

## 🌊 上传波形说明

支持在配置项 `uploaded_wave_files` 中上传多个波形文件。

文件会从 AstrBot 默认目录读取：`plugin_data/ycy_plugin/files/uploaded_wave_files/`。

波形在插件初始化阶段加载（配置变更触发插件重载后生效）。

加载成功后会与内置波形一起出现在 `/ycy wavelist` 和 wave 相关工具可用列表中。

## 🎨 内置波形

本插件在 `ycy_waves.py` 中提供若干内置波形（直接可通过工具或大模型调用）：

- `breathe`（呼吸）：模拟缓慢吸呼的起伏。
- `tide`（潮汐）：长周期涨落，类似潮汐上升/下降。
- `combo`（连击）：短促的连击脉冲。
- `fast_pinch`（快速按捏）：快速重复按捏感。
- `pinch_crescendo`（按捏渐强）：按捏力度逐步增强的过渡。
- `heartbeat`（心跳节奏）：模拟心跳的节奏脉冲。
- `compress`（压缩）：由强到弱或由弱到强的压缩式变化。
- `rhythm_step`（节奏步伐）：节奏化的步伐/鼓点型波形。

## 🛠️ 开发说明

- WebSocket 中继与控制器实现：`ycy_server.py`
- 工具实现：`ycy_tools.py`
- 波形预设与上传波形加载：`ycy_waves.py`
- 插件入口与指令：`main.py`
- 计费数据库：`billing_db.py`
- 爱发电 API：`afdian_api.py`

## 📡 WS 服务器机制

WS 服务采用"按需启动 + 空闲关闭"：

- 第一个会话执行 `/ycy start` 时启动 WS
- 后续会话复用同一个 WS 实例
- 最后一个会话执行 `/ycy stop` 后，WS 自动关闭

实现中包含启动锁，避免并发重复启动导致端口冲突。

## 🎭 役次元人格生成与删除机制

役次元人格采用"共享人格"模式：

有效配置 `ycy_persona_system_prompt` 时：
- 首次启用役次元模式会创建或更新共享人格
- 后续会话复用该人格

所有会话退出役次元模式后：
- 删除共享役次元人格，避免污染人格库

每个会话仍会记录进入役次元前的人格，并在 `/ycy stop` 时恢复。

## 🔧 动态 Tools 机制

本插件使用动态注册与动态删除 Tools：

- 役次元模式激活时注册 Tools
- 无活跃会话时卸载 Tools

## 📌 版本

当前版本：v1.0.0

## ⚠️ 安全提示（免责声明与使用承诺）

安装、启用或使用本插件，即视为你已阅读并理解役次元软件及设备提供的风险提示，并已知悉可能存在的风险与禁忌事项。

同时承诺：已对本插件相关风险作出与上述一致的知情确认，基于自愿原则使用，并对由此产生的风险、损害或其他后果自行承担责任。

并进一步确认：如因使用过程产生任何问题、纠纷或损失，由使用者自行承担责任，本项目及维护者不承担由此产生的责任。

如你不同意上述条款，请勿安装、启用或使用本插件；你一旦安装、启用或使用，即视为已同意并接受上述条款。

## 💡 使用建议

请从低强度开始并循序渐进；如存在心脏起搏器、癫痫、妊娠等情况，请先咨询专业医生；若出现不适、疼痛、头晕、心悸或皮肤明显刺激，请立即停止（执行 `/ycy stop`）并及时就医。
