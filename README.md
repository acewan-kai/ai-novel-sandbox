# PoC 技术验证 - 沉浸式AI小说创作平台

## 项目概述

这是一个基于 DeepSeek API 的回合制沙盒引擎 PoC（概念验证），用于验证"世界自主运转 → 涌现叙事"的核心假设。

## 封闭世界设定

**雾隐村** - 四面环海的孤岛村庄，常年被薄雾笼罩。村庄虽小，却藏龙卧虎——有隐居的前朝官员、有来历不明的商人、有神秘的旅人……

### 10个NPC角色

| ID | 姓名 | 身份 | 特点 |
|----|------|------|------|
| npc_001 | 李沉渊 | 村长 | 前朝大员，城府极深 |
| npc_002 | 张铁柱 | 老渔夫 | 豪爽直率，爱讲往事 |
| npc_003 | 沈墨白 | 游方郎中 | 温文尔雅，来历不明 |
| npc_004 | 周文秀 | 落魄书生 | 清高自傲，愤世嫉俗 |
| npc_005 | 阿莲 | 渔家少女 | 天真烂漫，对外界好奇 |
| npc_006 | 周掌柜 | 药铺老板 | 慈眉善目，曾是游医 |
| npc_007 | 神秘商人 | 行商 | 什么都卖，来历不明 |
| npc_008 | 阿福 | 茶馆小二 | 机灵勤快，消息灵通 |
| npc_009 | 红菱 | 神秘女子 | 美艳动人，身世成谜 |
| npc_010 | 哑巴老妪 | 守庙人 | 三十年不语，心怀仇恨 |

## 验收标准

| 条件 | 要求 | 状态 |
|------|------|------|
| 10个NPC全部存活运行100回合 | 必须 | ⏳ |
| 产生至少3个非预设跨角色互动 | 必须 | ⏳ |
| 至少1个互动具有故事感 | 必须 | ⏳ |
| 单回合延迟 < 15秒 | 期望 | ⏳ |

## 快速开始

### 1. 安装依赖

```bash
cd poc-sandbox
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
# Linux/Mac
export DEEPSEEK_API_KEY='your-api-key'

# Windows PowerShell
$env:DEEPSEEK_API_KEY='your-api-key'
```

### 3. 运行模拟

```bash
python sandbox_engine.py
```

## 项目结构

```
poc-sandbox/
├── config.py           # 配置文件
├── sandbox_engine.py   # 沙盒引擎核心
├── world_state.py      # 世界状态管理
├── npc.py              # NPC角色类
├── llm_client.py       # DeepSeek API客户端
├── event_logger.py     # 事件日志系统
├── world/
│   ├── world.yaml      # 世界定义
│   └── npcs.yaml       # NPC定义
└── logs/
    ├── events.jsonl    # 事件日志
    └── poc_report.md   # 验证报告
```

## 技术栈

- **Python 3.8+**
- **asyncio** - 异步并发执行
- **OpenAI SDK** - 兼容 DeepSeek API
- **PyYAML** - 配置文件解析

## 参考文档

- [PRD 文档](../../prd-ai-novel-platform-2026-05-11.md)
- [开发启动指令](../../dev-kickoff-p0-mvp.md)
