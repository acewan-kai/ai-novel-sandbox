"""
事件日志系统
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import config


@dataclass
class Event:
    """事件"""
    timestamp: str
    turn: int
    day: int
    time_of_day: str
    actor: str
    actor_id: Optional[str]
    action: str
    target: Optional[str]
    target_id: Optional[str]
    location: str
    action_type: str
    world_mood: str
    status: str
    elapsed_time: float
    original_response: Optional[str]
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(**data)


class EventLogger:
    """事件日志记录器"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.events: List[Event] = []
        self.unscripted_interactions: List[Event] = []  # 非预设互动
        self.storylike_moments: List[Event] = []  # 有故事感的互动
        self.npc_survival: Dict[str, int] = {}  # NPC存活记录
        
        # 确保文件存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_event(self, event: Dict, npc_id: str, world_state):
        """记录事件"""
        timestamp = datetime.now().isoformat()
        
        e = Event(
            timestamp=timestamp,
            turn=event.get("turn", 0),
            day=world_state.current_day,
            time_of_day=world_state.time_of_day,
            actor=event.get("actor", ""),
            actor_id=npc_id,
            action=event.get("action", ""),
            target=event.get("target"),
            target_id=event.get("target_id"),
            location=event.get("location", ""),
            action_type=event.get("action_type", "other"),
            world_mood=world_state.environment.get("mood", "平静"),
            status=event.get("status", "unknown"),
            elapsed_time=event.get("elapsed_time", 0.0),
            original_response=event.get("original_response")
        )
        
        self.events.append(e)
        
        # 写入JSONL文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(e.to_json() + '\n')
        
        # 更新存活记录
        if npc_id:
            self.npc_survival[npc_id] = event.get("turn", 0)
        
        # 检测非预设互动（有目标且涉及两个角色）
        if e.target and e.target_id and e.actor != e.target:
            self.unscripted_interactions.append(e)
        
        # 检测故事感（通过关键词）
        story_keywords = [
            "秘密", "发现", "真相", "回忆", "承诺", "背叛", 
            "隐藏", "秘密", "发现", "阴谋", "情感", "痛苦",
            "希望", "恐惧", "犹豫", "决定", "选择"
        ]
        if any(kw in e.action for kw in story_keywords):
            self.storylike_moments.append(e)
        
        return e
    
    def get_metrics(self) -> Dict:
        """获取验证指标"""
        total_events = len(self.events)
        successful_events = len([e for e in self.events if e.status == "success"])
        fallbacks = len([e for e in self.events if e.status == "fallback"])
        
        # 计算平均延迟
        timed_events = [e for e in self.events if e.elapsed_time > 0]
        avg_delay = sum(e.elapsed_time for e in timed_events) / len(timed_events) if timed_events else 0
        max_delay = max((e.elapsed_time for e in timed_events), default=0)
        
        # 计算非预设互动数量（去重后的跨角色互动）
        unique_cross_interactions = set()
        for e in self.unscripted_interactions:
            pair = tuple(sorted([e.actor, e.target or ""]))
            unique_cross_interactions.add(pair)
        
        return {
            "total_turns": len(self.events),
            "successful_events": successful_events,
            "fallbacks": fallbacks,
            "success_rate": f"{successful_events/total_events*100:.1f}%" if total_events > 0 else "0%",
            "unique_cross_interactions": len(unique_cross_interactions),
            "storylike_moments": len(self.storylike_moments),
            "avg_turn_delay": f"{avg_delay:.2f}s",
            "max_turn_delay": f"{max_delay:.2f}s",
            "npc_survival": self.npc_survival,
            "all_npcs_survived": len(self.npc_survival) == 10,
            "validation": {
                "all_npcs_survived_100_turns": len(self.npc_survival) == 10 and min(self.npc_survival.values()) >= 100,
                "at_least_3_unscripted_interactions": len(unique_cross_interactions) >= 3,
                "at_least_1_storylike_moment": len(self.storylike_moments) >= 1,
                "single_turn_delay_under_15s": max_delay < 15.0
            }
        }
    
    def generate_report(self, output_file: Path):
        """生成验证报告"""
        metrics = self.get_metrics()
        max_delay = metrics['max_turn_delay']
        all_npcs = "全部存活" if metrics['all_npcs_survived'] else "部分存活"
        
        report = f"""# PoC 技术验证报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 验收标准检查

| 条件 | 要求 | 实际 | 结果 |
|------|------|------|------|
| 10个NPC全部存活运行100回合 | 必须 | {all_npcs} ({len(metrics['npc_survival'])}/10) | {'[PASS]' if metrics['validation']['all_npcs_survived_100_turns'] else '[FAIL]'} |
| 产生至少3个非预设跨角色互动 | 必须 | {metrics['unique_cross_interactions']}个 | {'[PASS]' if metrics['validation']['at_least_3_unscripted_interactions'] else '[FAIL]'} |
| 至少1个互动具有故事感 | 必须 | {metrics['storylike_moments']}个 | {'[PASS]' if metrics['validation']['at_least_1_storylike_moment'] else '[FAIL]'} |
| 单回合延迟 < 15秒 | 期望 | 最大{max_delay}秒 | {'[PASS]' if metrics['validation']['single_turn_delay_under_15s'] else '[FAIL]'} |

## 运行统计

- 总回合数: {metrics['total_turns']}
- 成功事件: {metrics['successful_events']}
- 回退事件: {metrics['fallbacks']}
- 成功率: {metrics['success_rate']}
- 平均回合延迟: {metrics['avg_turn_delay']}
- 最大回合延迟: {metrics['max_turn_delay']}

## NPC存活情况

"""
        for npc_id, turns in sorted(metrics['npc_survival'].items()):
            status = "[PASS]" if turns >= 100 else "[FAIL]"
            report += f"- {npc_id}: {turns}回合 {status}\n"
        
        report += f"""
## 非预设跨角色互动 ({metrics['unique_cross_interactions']}个)

"""
        for i, e in enumerate(self.storylike_moments[:10], 1):
            report += f"{i}. [{e.time_of_day}] {e.actor} → {e.target or '环境'}: {e.action}\n"
        
        report += f"""
## 有故事感的时刻 ({len(self.storylike_moments)}个)

"""
        for i, e in enumerate(self.storylike_moments[:10], 1):
            report += f"{i}. [第{e.turn}回合] {e.actor}: {e.action}\n"
        
        report += f"""
## 最终结论

**Go/No-Go**: {'[GO] PoC验证通过，可以进入第2步' if all([
    metrics['validation']['all_npcs_survived_100_turns'],
    metrics['validation']['at_least_3_unscripted_interactions'],
    metrics['validation']['at_least_1_storylike_moment']
]) else '[NO-GO] 需要调整后重试'}

"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report
