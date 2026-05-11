"""
NPC角色类
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import yaml
import random


@dataclass
class Relationship:
    """关系"""
    target: str  # 目标NPC ID
    type: str  # 关系类型：信任、敌意、暗恋等
    level: int  # 等级 1-5
    note: str  # 备注说明
    
    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "type": self.type,
            "level": self.level,
            "note": self.note
        }


@dataclass
class NPC:
    """NPC角色"""
    id: str
    name: str
    age: int
    gender: str
    identity: str
    personality: str
    background: str
    traits: Dict[str, int]  # 五维性格
    short_term_goal: str
    current_location: str
    relationships: List[Relationship]
    
    # 运行时状态
    memory: List[str] = field(default_factory=list)  # 记忆流
    last_action: Optional[str] = None  # 上一个动作
    status: str = "alive"  # 存活状态
    survival_turns: int = 0  # 存活回合数
    
    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        """从字典创建NPC"""
        relationships = [
            Relationship(**rel) for rel in data.get('relationships', [])
        ]
        return cls(
            id=data['id'],
            name=data['name'],
            age=data['age'],
            gender=data['gender'],
            identity=data['identity'],
            personality=data['personality'],
            background=data['background'],
            traits=data['traits'],
            short_term_goal=data['short_term_goal'],
            current_location=data['current_location'],
            relationships=relationships
        )
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> List["NPC"]:
        """从YAML加载所有NPC"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return [cls.from_dict(npc_data) for npc_data in data['npcs']]
    
    def add_memory(self, event: str):
        """添加记忆"""
        timestamped = f"[回合{len(self.memory)+1}] {event}"
        self.memory.append(timestamped)
        # 保留最近20条记忆
        if len(self.memory) > 20:
            self.memory = self.memory[-20:]
    
    def get_relationship(self, target_id: str) -> Optional[Relationship]:
        """获取与目标NPC的关系"""
        for rel in self.relationships:
            if rel.target == target_id:
                return rel
        return None
    
    def update_relationship(self, target_id: str, rel_type: str, delta: int):
        """更新关系"""
        rel = self.get_relationship(target_id)
        if rel:
            rel.level = max(1, min(5, rel.level + delta))
            rel.type = rel_type
        else:
            self.relationships.append(Relationship(
                target=target_id,
                type=rel_type,
                level=max(1, min(5, 3 + delta)),
                note=f"新建立的关系"
            ))
    
    def to_system_prompt(self, world_context: str) -> str:
        """生成用于LLM的system prompt"""
        rel_str = ""
        for rel in self.relationships:
            rel_str += f"- 与{rel.target}：{rel.type}({rel.level}/5) - {rel.note}\n"
        
        prompt = f"""【角色设定】
姓名：{self.name}
年龄：{self.age}岁
性别：{self.gender}
身份：{self.identity}

【性格特征】
{self.personality}

【背景故事】
{self.background}

【五维性格】
- 开放性：{self.traits.get('openness', 3)}/5
- 尽责性：{self.traits.get('conscientiousness', 3)}/5
- 外向性：{self.traits.get('extraversion', 3)}/5
- 宜人性：{self.traits.get('agreeableness', 3)}/5
- 神经质：{self.traits.get('neuroticism', 3)}/5

【当前目标】
{self.short_term_goal}

【当前关系】
{rel_str if rel_str else "暂无已知关系"}

【近期记忆】
"""
        if self.memory:
            for mem in self.memory[-5:]:
                prompt += f"- {mem}\n"
        else:
            prompt += "暂无记忆\n"
        
        prompt += f"""
{world_context}

【你的当前状态】
所在地点：{self.current_location}
"""
        if self.last_action:
            prompt += f"上一个动作：{self.last_action}\n"
        
        return prompt
    
    def to_context_summary(self) -> str:
        """简洁的角色上下文摘要"""
        return f"{self.name}({self.identity})"


class NPCManager:
    """NPC管理器"""
    
    def __init__(self, npcs: List[NPC]):
        self.npcs = {npc.id: npc for npc in npcs}
        self.npcs_by_name = {npc.name: npc for npc in npcs}
    
    def get(self, npc_id: str) -> Optional[NPC]:
        return self.npcs.get(npc_id)
    
    def get_by_name(self, name: str) -> Optional[NPC]:
        return self.npcs_by_name.get(name)
    
    def get_all(self) -> List[NPC]:
        return list(self.npcs.values())
    
    def get_alive(self) -> List[NPC]:
        return [npc for npc in self.npcs.values() if npc.status == "alive"]
    
    def get_by_location(self, location: str) -> List[NPC]:
        return [npc for npc in self.get_alive() if npc.current_location == location]
    
    def get_other_npcs_context(self, current_npc: NPC, world_state) -> str:
        """获取其他NPC的上下文信息"""
        # 获取同一地点的NPC
        same_location = self.get_by_location(current_npc.current_location)
        others = [n for n in same_location if n.id != current_npc.id]
        
        context = "【同处一地的角色】\n"
        if others:
            for other in others:
                rel = current_npc.get_relationship(other.id)
                rel_info = f"，关系：{rel.type}({rel.level}/5)" if rel else ""
                context += f"- {other.name}：{other.identity}{rel_info}，正在{other.last_action or '做自己的事'}\n"
        else:
            context += "只有你一人在此。\n"
        
        # 获取附近地点的NPC（随机选择一个增强互动可能性）
        nearby_npcs = []
        for npc in self.get_alive():
            if npc.id != current_npc.id and npc not in others:
                if random.random() < 0.1:  # 10%概率提及
                    nearby_npcs.append(npc)
        
        if nearby_npcs:
            context += "\n【远处传来消息】\n"
            for other in nearby_npcs[:3]:
                context += f"- 听闻{other.name}在{other.current_location}附近活动\n"
        
        return context
    
    def get_recent_events_context(self, current_npc: NPC) -> str:
        """获取相关记忆上下文"""
        context = "【你关注的事件】\n"
        
        # 获取与当前NPC关系相关的记忆
        relevant_memories = []
        for npc in self.get_alive():
            if npc.id == current_npc.id:
                continue
            rel = current_npc.get_relationship(npc.id)
            if rel and rel.level >= 3:
                relevant_memories.extend(
                    [m for m in npc.memory[-3:] if any(
                        name in m for name in [current_npc.name] + 
                        [r.target for r in current_npc.relationships]
                    )]
                )
        
        if relevant_memories:
            for mem in relevant_memories[:5]:
                context += f"- {mem}\n"
        else:
            context += "暂无值得关注的相关事件。\n"
        
        return context
