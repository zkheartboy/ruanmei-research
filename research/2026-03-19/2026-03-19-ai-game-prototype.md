# AI游戏原型设计报告

**报告时间**: 2026-03-19
**报告性质**: AI游戏产品原型深化设计
**参考基准**: 2026-03-05 AI游戏竞品调研报告

---

## 一、背景回顾

2026-03-05 的竞品调研已完成以下工作：
- 分析了 AI Dungeon、Character.AI、Replika、Verses 等主流产品
- 识别出三大潜在机会方向：政府/政务主题游戏、金融模拟游戏、AI+传统游戏

本报告在上述调研基础上，进一步选定核心玩法、完成技术方案设计，并规划 MVP。

---

## 二、核心玩法选定

### 2.1 五大可行概念回顾

| 序号 | 概念 | 核心机制 | 市场潜力 | 技术难度 | 差异化 |
|------|------|----------|----------|----------|--------|
| 1 | AI NPC 开放世界 | AI 驱动 NPC 自主决策与对话 | ★★★★★ | ★★★★ | 叙事自由度高 |
| 2 | AI 剧情生成 RPG | LLM 实时生成任务与剧情分支 | ★★★★ | ★★★ | 内容无限 |
| 3 | 金融模拟交易游戏 | 虚拟组合 + AI 对手盘 | ★★★ | ★★★ | 教育+娱乐 |
| 4 | 政务决策模拟游戏 | 政策选择 → 城市指标变化 | ★★★★ | ★★★ | 垂直领域蓝海 |
| 5 | AI + 棋牌竞技 | 传统棋牌 + AI 自适应难度 | ★★★★ | ★★★ | 存量市场升级 |

### 2.2 选定方案：**AI 剧情生成 RPG（概念2升级版）**

**正式命名**: **「叙事深渊」(Narrative Abyss)**

**选择理由**:

1. **市场验证充分**: AI Dungeon 已验证 AI 生成剧情的商业可行性（订阅制，稳定付费用户）
2. **技术复利强**: LLM 能力持续提升 → 产品体验自动提升（无需手动更新内容）
3. **差异化定位**: 现有 AI Dungeon 偏向奇幻/冒险，我们聚焦**都市悬疑/商战博弈**，填补市场空白
4. **变现路径清晰**: 章节付费 + 订阅会员 + 皮肤叙事包
5. **AI 能力依赖**: 充分发挥 GPT-4/Claude 的长上下文和推理能力，而非依赖游戏图形引擎

### 2.3 核心玩法机制

#### 2.3.1 游戏类型
- **类型**: 都市悬疑叙事 RPG（文字/视觉小说形式）
- **平台**: PC Web + 移动端 H5
- **用户画像**: 18-35岁，喜欢悬疑叙事、内容探索、策略抉择的用户

#### 2.3.2 核心循环
```
玩家行动 → AI解析意图 → 生成剧情片段 → 展示选项 → 玩家决策 → 循环
```

#### 2.3.3 三大核心系统

**① 叙事引擎系统 (Narrative Engine)**
- 基于 LLM API 构建，负责实时生成剧情文本
- 输入：玩家当前状态（背包、人际关系、金钱、情报值）、历史决策树、当前位置
- 输出：符合世界观的剧情片段（200-800字）+ 3-5个玩家可选行动
- 上下文窗口：保留最近 20 轮对话历史 + 关键决策摘要

**② 角色关系系统 (Relationship System)**
- NPC 不再是静态脚本，而是由 LLM 驱动的"AI 角色"
- 每个 NPC 有：身份背景、性格参数（通过 few-shot prompt 设定）、当前目标、对玩家态度
- NPC 自主行为：玩家不在场时，NPC 会根据自身目标自主行动（通过定时调用 LLM 模拟）
- 派系系统：城市中存在多个派系（警方/黑帮/企业/媒体），玩家选择影响派系关系

**③ 叙事状态追踪系统 (State Tracker)**
- 结构化记录：玩家位置、物品、人际关系、金钱、情报值、解锁成就、时间线进度
- 决策影响评估：每次重大决策后，系统计算对后续剧情的潜在影响（影响因子权重）
- 多结局引擎：基于状态向量，支持 5 种以上不同结局路线（真相揭露/派系胜利/玩家牺牲/反派胜利/隐藏结局）

#### 2.3.4 关键游戏机制

**【情报博弈机制】**（差异化核心）
- 玩家拥有"情报值"属性，可用于"调查"行动
- 调查行动触发 AI 生成探索场景：跟踪、潜入、审讯、黑入
- 情报值消耗方式：每次调查消耗 1-3 点，可通过休息恢复
- 情报是推动主线和获取线索的核心资源

**【时间流逝机制】**
- 游戏内时间随行动推进（每次重大行动推进 1-4 小时）
- 部分事件仅在特定时间段发生（紧迫感设计）
- NPC 行为受时间影响（夜间派系行动、白天商业活动）

**【信任与伪装机制】**
- 玩家可以选择"真实身份"或"伪装身份"与不同派系互动
- 伪装身份有暴露风险（通过 LLM 评估玩家行为与伪装的一致性）
- 信任度双向：NPC 对玩家有信任值，玩家对 NPC 也有（影响信息获取）

---

## 三、技术方案

### 3.1 技术栈选择

| 层级 | 技术选型 | 理由 |
|------|----------|------|
| **游戏引擎** | Godot 4.x (前端) | 开源免费、轻量级、2D 表现优秀、GDScript 上手快 |
| **LLM 接入** | OpenAI API (GPT-4o / GPT-4.5) + Claude API 作为备选 | 上下文窗口大、推理能力强、成本可控 |
| **RL 框架** | Stable-Baselines3 (PPO) — 用于 NPC 自适应难度 | 成熟稳定、文档完善 |
| **后端服务** | FastAPI (Python) | 异步支持好、与 SB3/RL 集成方便 |
| **数据库** | SQLite (MVP) → PostgreSQL (生产) | 轻量起步、水平扩展 |
| **缓存/状态** | Redis | 高频状态读写 |
| **部署** | Docker + 云服务器 | 跨平台、可复制 |

### 3.2 系统架构设计

```
┌─────────────────────────────────────────────────────┐
│                   玩家客户端 (Godot)                  │
│   [UI层] 剧情展示 / 选项选择 / 状态面板 / 地图        │
└─────────────────────┬───────────────────────────────┘
                      │ HTTPS / WebSocket
                      ▼
┌─────────────────────────────────────────────────────┐
│                  API Gateway (Nginx)                │
│            负载均衡 / SSL / 速率限制                  │
└─────────────────────┬───────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Game API │ │ LLM API  │ │ NPC API  │
    │ (FastAPI)│ │ (路由层) │ │ (RL引擎) │
    └────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │
         ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │PostgreSQL│ │OpenAI API│ │ Stable-  │
    │+ Redis   │ │Claude API│ │ Baselines│
    └──────────┘ └──────────┘ └──────────┘
```

### 3.3 核心模块设计

#### 3.3.1 叙事引擎模块 (Narrative Engine)
```python
# 核心伪代码
class NarrativeEngine:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.world_state = WorldState()
        self.prompt_template = self._load_prompt("narrative_v1.md")

    def generate_scene(self, player_action: str) -> SceneResult:
        # 1. 构建上下文摘要
        context = self._build_context()

        # 2. 构建 Prompt（含few-shot示例）
        prompt = self._build_prompt(player_action, context)

        # 3. 调用 LLM
        response = self.llm.complete(prompt)

        # 4. 解析输出：剧情文本 + 候选选项
        scene = self._parse_response(response)

        # 5. 更新世界状态
        self.world_state.apply_action(player_action)

        return scene

    def _build_context(self):
        return {
            "location": self.world_state.current_location,
            "time": self.world_state.game_time,
            "inventory": self.world_state.inventory,
            "relationships": self.world_state.npc_relations,
            "key_decisions": self.world_state.major_decisions[-5:],
            "active_plotlines": self.world_state.active_threads
        }
```

#### 3.3.2 NPC AI 模块
```python
# NPC 决策由 PPO 模型 + LLM 对话双重驱动
class NPCAgent:
    def __init__(self, npc_id, personality, goals):
        self.npc_id = npc_id
        self.personality = personality  # prompt中的few-shot设定
        self.goals = goals
        self.relation_model = SB3_PPO(model_path=f"npc_{npc_id}_relation")

    def decide_action(self, world_state) -> NPCAction:
        # PPO模型决定行动类型：交流/移动/等待/攻击
        action_type = self.relation_model.predict(world_state.get_npc_view(self.npc_id))

        # LLM 决定具体执行内容（对话内容/行动描述）
        if action_type == "communicate":
            target = world_state.get_nearest_player_or_npc()
            dialogue = self.llm.generate_dialogue(self.personality, target, world_state)
            return NPCAction("communicate", target, dialogue)

        return NPCAction(action_type)
```

#### 3.3.3 状态管理模块
```python
# 世界状态结构
@dataclass
class WorldState:
    game_time: datetime          # 游戏内时间
    player_location: str         # 当前位置
    inventory: List[Item]        # 背包
    money: int                    # 金钱
    intel: int                    # 情报值
    npc_relations: Dict[str, float]  # NPC关系 (-100~100)
    faction_relations: Dict[str, float]  # 派系关系
    major_decisions: List[Decision]  # 重大决策记录
    active_threads: List[str]    # 进行中的剧情线
    unlocked_clues: List[str]    # 已解锁线索
    world_facts: Dict[str, bool] # 已确认的世界事实
```

### 3.4 Prompt 设计要点

**叙事生成 Prompt 核心要素**:
1. **系统设定**: 定义城市背景、派系、主角身份
2. **当前状态**: 格式化的结构化数据注入（位置/关系/时间）
3. **Few-shot 示例**: 提供 2-3 个"行动 → 剧情"示例，保持输出格式一致
4. **输出格式约束**: 明确要求 JSON 格式（剧情文本 + 选项列表 + 状态变更）
5. **安全约束**: 禁止生成暴力/色情/政治敏感内容

---

## 四、MVP 规划

### 4.1 MVP 范围定义

**目标**: 在 8-12 周内推出可运行的最小可行产品

#### 必须包含 (MVP)

| 功能模块 | 具体内容 | 优先级 |
|----------|----------|--------|
| 叙事引擎 | LLM 生成剧情文本 + 选项 | P0 |
| 基础 UI | 文字展示区、选项区、状态栏（位置/时间/金钱） | P0 |
| 存档系统 | SQLite 存储游戏进度 | P0 |
| 一个完整章节 | 3-5 小时游戏内容，1 条主线，2 个可发现结局 | P0 |
| 用户认证 | 简单邮箱注册/登录 | P0 |
| 基础数据分析 | DAU/留存/选项分布 | P1 |

#### 暂不包含 (Post-MVP)

- NPC 派系自主行动（第一版 NPC 为事件触发）
- PPO 驱动的 NPC 自适应难度
- 物品系统（简化版：仅金钱和关键道具）
- 多章节内容
- 订阅付费（先免费跑数据）

### 4.2 技术 MVP 里程碑

```
Week 1-2:  环境搭建
  - Godot 项目初始化，UI 界面搭建
  - FastAPI 后端骨架，数据库表设计
  - LLM API 接入测试，Prompt 初版

Week 3-4:  叙事引擎核心
  - Narrative Engine 完成
  - 状态追踪系统完成
  - 单场景测试（固定起点/固定选项测试）

Week 5-6:  第一章内容
  - 章节剧情编写（人类编剧 + AI 扩写）
  - 5+ 结局分支落地
  - 内部测试

Week 7-8:  完整流程打通
  - 注册登录 → 剧情 → 存档 → 结束 完整链路
  - 基础数据分析埋点
  - 修复 bug

Week 9-10: 外部测试
  - 邀请 20-50 名用户内测
  - 收集反馈，优化 Prompt
  - 性能优化（LLM 调用延迟）

Week 11-12: 上线准备
  - 部署到云服务器
  - 运营数据看板
  - 正式发布
```

### 4.3 MVP 成本估算

| 成本项 | 单价 | 估算 |
|--------|------|------|
| 云服务器 (2台) | ¥300/月 | ¥3,600（初期年付） |
| OpenAI API | $0.01/K tokens | 约 $50-200/月（视用户量） |
| 域名/SSL | ¥200/年 | ¥200 |
| 开发人力 | 自研 | 0（团队现有资源） |
| **合计（年）** | | **约 ¥8,000-15,000** |

---

## 五、商业化路径

### 5.1 短期（0-6个月）
- **阶段1**: 免费公测，积累用户和数据
- **阶段2**: 推出付费章节包（¥6-12/章节），单章节 3-5 小时
- **目标**: 6个月达到 5,000 月活，500 付费用户

### 5.2 中期（6-18个月）
- 会员订阅制（¥25-30/月）：解锁所有章节 + 优先体验新内容
- 叙事包（皮肤系统）：不同叙事风格包（赛博朋克/民国谍战/都市传说）
- **目标**: 18个月达到 20,000 月活，2,000 付费订阅

### 5.3 长期（18个月+）
- IP 化：热门章节改编为有声剧/短剧
- 平台化：开放编辑器，让创作者使用 AI 叙事引擎创作
- B端：授权叙事引擎给教育/培训场景

---

## 六、风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|----------|
| LLM 生成内容质量不稳定 | 高 | 高 | 严格 Prompt 约束 + 人工审核内容 + 多模型投票 |
| API 成本随用户增长超预期 | 中 | 中 | 引入 Claude 作为低价备选 + 缓存机制 |
| 用户留存低于预期 | 中 | 高 | 快速迭代内容 + 社区驱动创作 |
| 政策监管 LLM 生成内容 | 低 | 高 | 建立内容审核层，上线前完成备案 |
| 技术选型风险（Godot） | 低 | 低 | Godot 成熟度高，切换 Unity 成本可控 |

---

## 七、总结

**「叙事深渊」** 以 AI 实时生成叙事为核心差异化竞争力，结合都市悬疑/商战博弈的题材定位，填补市场空白。技术方案以 Godot + FastAPI + OpenAI API 为核心栈，Stable-Baselines3 支撑 NPC 自适应难度，整体技术风险可控。

MVP 聚焦叙事引擎 + 单章节内容，8-12 周可交付可运行版本，为后续规模化奠定数据和体验基础。

---

*报告撰写: 阮·梅 AI游戏研究模块*
*报告时间: 2026-03-19*
