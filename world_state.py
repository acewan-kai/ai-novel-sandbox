"""
世界状态管理
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import yaml


@dataclass
class Location:
    """地点"""
    name: str
    description: str
    NPCs: List[str] = field(default_factory=list)  # 在此地点的NPC ID列表


@dataclass
class WorldState:
    """世界状态"""
    name: str
    description: str
    location: str
    era: str
    atmosphere: str
    rules: List[str]
    environment: Dict
    locations: List[Location]
    current_turn: int = 0
    current_day: int = 1
    time_of_day: str = "清晨"
    global_events: List[str] = field(default_factory=list)  # 全球事件
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "WorldState":
        """从YAML加载世界配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        world_data = data['world']
        locations = [
            Location(**loc) for loc in world_data.get('locations', [])
        ]
        
        env = world_data.get('environment', {})
        
        return cls(
            name=world_data['name'],
            description=world_data['description'],
            location=world_data['location'],
            era=world_data['era'],
            atmosphere=world_data['atmosphere'],
            rules=world_data.get('rules', []),
            environment={
                'time': env.get('time', '清晨'),
                'weather': env.get('weather', '晴'),
                'mood': env.get('mood', '平静'),
                'rumor': env.get('rumor', ''),
            },
            locations=locations
        )
    
    def advance_turn(self, turns_per_day: int = 12):
        """推进回合"""
        self.current_turn += 1
        
        # 计算时间和天数
        position = self.current_turn % turns_per_day
        if position == 0:
            self.current_day += 1
            position = turns_per_day
        
        # 更新时辰
        times = ["清晨", "上午", "正午", "下午", "傍晚", "入夜", 
                 "深夜", "子时", "丑时", "寅时", "卯时", "辰时"]
        self.time_of_day = times[position - 1]
        
        # 随机更新环境
        weathers = ["晴", "阴", "薄雾", "小雨", "大雾"]
        if self.current_turn % 3 == 0:
            self.environment['weather'] = weathers[self.current_turn // 3 % len(weathers)]
        
        # 更新氛围（基于事件）
        if len(self.global_events) > 3:
            self.environment['mood'] = "暗流涌动"
        elif len(self.global_events) > 0:
            self.environment['mood'] = "有所波澜"
        else:
            self.environment['mood'] = "平静"
    
    def add_global_event(self, event: str):
        """添加全球事件"""
        self.global_events.append(event)
        # 保留最近20个事件
        if len(self.global_events) > 20:
            self.global_events = self.global_events[-20:]
    
    def get_location_by_name(self, name: str) -> Optional[Location]:
        """根据名称获取地点"""
        for loc in self.locations:
            if loc.name == name:
                return loc
        return None
    
    def to_context(self) -> str:
        """生成用于LLM的上下文描述"""
        context = f"""【当前世界状态】
世界名称：{self.name}
时代背景：{self.era}
地点：{self.location}
整体氛围：{self.atmosphere}
当前时间：第{self.current_day}天 {self.time_of_day}
天气：{self.environment['weather']}
村中氛围：{self.environment['mood']}

【地点】
"""
        for loc in self.locations:
            npcs_here = [n for n in loc.NPCs] if loc.NPCs else []
            npcs_str = "、".join(npcs_here) if npcs_here else "无"
            context += f"- {loc.name}：{loc.description}（当前有：{npcs_str}）\n"
        
        context += f"\n【近期动态】\n"
        if self.global_events:
            for event in self.global_events[-5:]:
                context += f"- {event}\n"
        else:
            context += "暂无重大事件发生。\n"
        
        context += f"\n【世界规则】\n"
        for rule in self.rules:
            context += f"- {rule}\n"
        
        context += f"\n【当前传闻】{self.environment.get('rumor', '无')}\n"
        
        return context
