"""
DeepSeek API 客户端
"""

import json
import time
import random
import asyncio
from typing import Optional, Dict, List
from openai import AsyncOpenAI, RateLimitError, APIError
import config


# 模拟模式动作库
MOCK_ACTIONS = {
    "李沉渊": [
        "站在院子里远眺海面，思考着近日的异象",
        "在书房中翻阅旧籍，寻找关于海上异象的记载",
        "召集几位村民了解近日的所见所闻",
        "独自在村中巡视，检查各处是否一切正常",
    ],
    "张铁柱": [
        "修补渔网，嘴里哼着老歌",
        "与年轻渔民分享年轻时与风浪搏斗的经历",
        "在码头边整理渔具，眺望远方",
        "回忆起当年救下村长的往事",
    ],
    "沈墨白": [
        "在茶馆中品茶，观察周围人的言行举止",
        "与村民闲聊，旁敲侧击地打听村中的历史",
        "在村中漫步，似乎在寻找什么失踪之人的下落",
        "整理药箱，准备为有需要的村民诊病",
    ],
    "周文秀": [
        "在废弃祠堂中借着微弱光线读书",
        "偷偷观察村长宅院的动静",
        "在纸上写下村长的种种疑点",
        "叹息自己命运多舛，决心要找到证据揭发村长",
    ],
    "阿莲": [
        "在海边拾贝壳，哼唱着不知名的小调",
        "偷偷看向茶馆的方向，脸上带着红晕",
        "帮铁柱叔叔整理捕获的海产",
        "望着海面出神，幻想外面的世界",
    ],
    "周掌柜": [
        "在柜台后研磨药材",
        "与沈墨白讨论医术，相谈甚欢",
        "为村民配药，细心叮嘱用法用量",
        "回忆年轻时行走江湖的往事",
    ],
    "神秘商人": [
        "在村中四处游走，物色有价值的货物",
        "向村民兜售香料，言谈中透露见过大世面",
        "在茶馆中竖起耳朵，收集各种消息",
        "悄悄观察着村中的每一个人",
    ],
    "阿福": [
        "热情招待客人，端茶送水忙个不停",
        "向客人们讲述近日村中的趣闻轶事",
        "偷偷观察阿莲的到来，心里砰砰跳",
        "在角落里记下今日听到的重要消息",
    ],
    "红菱": [
        "在村中漫步，熟悉着周围的环境",
        "向村民打听去外岛的方法",
        "在海边望着远方，眼眶微红",
        "似乎在躲避某些人的注意",
    ],
    "哑巴老妪": [
        "在祠堂前静坐，目光深邃",
        "用树枝在地上画着奇怪的符号",
        "默默注视着周文秀的一举一动",
        "仿佛在等待某个时机",
    ],
}

# 模拟跨角色互动 - 用于增加故事的丰富度
MOCK_INTERACTIONS = [
    ("李沉渊", "张铁柱", "两人在院中叙旧，谈论近日海上异象"),
    ("沈墨白", "周掌柜", "两人在药铺品茶论医，相见恨晚"),
    ("阿莲", "阿福", "阿莲来茶馆听故事，两人眉来眼去"),
    ("神秘商人", "李沉渊", "商人想从村长口中打探村中隐秘"),
    ("周文秀", "哑巴老妪", "周文秀发现老妪似乎想对她透露什么秘密"),
    ("红菱", "阿莲", "红菱与阿莲攀谈，询问离岛之路"),
    ("沈墨白", "李沉渊", "沈墨白试探村长的来历和过去"),
    ("神秘商人", "红菱", "商人发现红菱行踪可疑，暗中跟踪"),
]


class MockDeepSeekClient:
    """模拟模式的DeepSeek客户端"""
    
    def __init__(self):
        self.turn_counter = 0
        
    async def generate_action(
        self, 
        system_prompt: str, 
        user_prompt: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """模拟生成动作"""
        # 模拟网络延迟
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # 从system_prompt中提取角色名
        npc_name = "阿福"  # 默认
        for name in MOCK_ACTIONS.keys():
            if name in system_prompt:
                npc_name = name
                break
        
        self.turn_counter += 1
        
        # 10%概率生成跨角色互动
        if random.random() < 0.15 and self.turn_counter > 5:
            interaction = random.choice(MOCK_INTERACTIONS)
            if interaction[0] == npc_name:
                return f"{npc_name}: {interaction[2]} → 影响 {interaction[1]}"
        
        # 正常生成动作
        actions = MOCK_ACTIONS.get(npc_name, MOCK_ACTIONS["阿福"])
        action = random.choice(actions)
        
        # 20%概率涉及目标角色
        if random.random() < 0.2:
            target = random.choice(list(MOCK_ACTIONS.keys()))
            if target != npc_name:
                return f"{npc_name}: {action} → 影响 {target}"
        
        return action


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.base_url = config.DEEPSEEK_API_URL
        self.model = config.DEEPSEEK_MODEL
        self.llm_config = config.LLM_CONFIG.copy()
        self.mock_mode = config.MOCK_MODE
        
        if self.mock_mode:
            print("[INFO] 模拟模式已启用 (无API密钥)")
            self.mock_client = MockDeepSeekClient()
        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
    
    async def generate_action(
        self, 
        system_prompt: str, 
        user_prompt: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """生成NPC动作"""
        
        if self.mock_mode:
            return await self.mock_client.generate_action(
                system_prompt, user_prompt, max_retries
            )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.llm_config["temperature"],
                    max_tokens=self.llm_config["max_tokens"],
                    top_p=self.llm_config["top_p"],
                )
                
                content = response.choices[0].message.content.strip()
                return content
                
            except RateLimitError:
                print(f"API速率限制，等待后重试... (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(config.SIMULATION_CONFIG["retry_delay"])
                
            except APIError as e:
                print(f"API错误: {e} (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(config.SIMULATION_CONFIG["retry_delay"])
                    
            except Exception as e:
                print(f"未知错误: {e}")
                break
        
        return None
    
    def parse_action_response(self, response: str, npc_name: str) -> Dict:
        """
        解析动作响应
        
        Returns:
            包含动作描述、目标、类型的字典
        """
        result = {
            "actor": npc_name,
            "action": response,
            "target": None,
            "action_type": "other",
            "original_response": response
        }
        
        # 尝试解析格式：角色名: 动作描述 → 影响 xxx
        if "→" in response or "->" in response:
            parts = response.replace("→", "->").split("->")
            result["action"] = parts[0].strip()
            if len(parts) > 1:
                target = parts[1].strip()
                result["target"] = target
                # 判断动作类型
                if any(kw in target for kw in ["说话", "告诉", "问", "答", "喊", "谈", "论"]):
                    result["action_type"] = "communicate"
                elif any(kw in target for kw in ["打", "攻击", "伤害"]):
                    result["action_type"] = "attack"
                elif any(kw in target for kw in ["帮助", "照顾", "给", "关心"]):
                    result["action_type"] = "help"
                else:
                    result["action_type"] = "interact"
        
        return result


def generate_action_prompt(npc: 'NPC', world_state: 'WorldState', npc_manager: 'NPCManager') -> str:
    """
    生成动作请求的用户提示词
    """
    world_context = world_state.to_context()
    other_npcs = npc_manager.get_other_npcs_context(npc, world_state)
    recent_events = npc_manager.get_recent_events_context(npc)
    
    prompt = f"""{world_context}

{other_npcs}

{recent_events}

---

你扮演的{npc.name}（{npc.identity}）现在在{npc.current_location}。

{npc.short_term_goal}

请以{npc.name}的视角，用一句话描述他/她在这个情境下会做什么。
动作应该符合角色性格，且可能与其他角色产生互动。
输出格式：{npc.name}: [动作描述] → 影响 [目标角色/环境]

请用中文输出动作："""
    
    return prompt


async def simulate_npc_action(
    client: DeepSeekClient,
    npc: 'NPC',
    world_state: 'WorldState',
    npc_manager: 'NPCManager',
    turn_num: int
) -> Dict:
    """
    模拟单个NPC的动作
    
    Returns:
        事件字典
    """
    system_prompt = npc.to_system_prompt(world_state.to_context())
    user_prompt = generate_action_prompt(npc, world_state, npc_manager)
    
    start_time = time.time()
    response = await client.generate_action(system_prompt, user_prompt)
    elapsed = time.time() - start_time
    
    if response:
        parsed = client.parse_action_response(response, npc.name)
        parsed["turn"] = turn_num
        parsed["location"] = npc.current_location
        parsed["elapsed_time"] = elapsed
        parsed["status"] = "success"
        
        # 更新NPC状态
        npc.last_action = parsed["action"]
        npc.survival_turns += 1
        
        # 解析目标并建立联系
        if parsed["target"]:
            # 尝试匹配目标角色名
            target_npc = None
            for name in ["李沉渊", "张铁柱", "沈墨白", "周文秀", "阿莲", 
                        "周掌柜", "神秘商人", "阿福", "红菱", "哑巴老妪"]:
                if name in parsed["target"]:
                    target_npc = npc_manager.get_by_name(name)
                    break
            
            if target_npc:
                parsed["target_id"] = target_npc.id
                # 相互添加记忆
                npc.add_memory(f"向{target_npc.name}：{parsed['action']}")
                target_npc.add_memory(f"见{npc.name}：{parsed['action']}")
            else:
                npc.add_memory(f"影响了环境/事物：{parsed['action']}")
        else:
            npc.add_memory(parsed["action"])
        
        return parsed
    else:
        return {
            "actor": npc.name,
            "action": "保持沉默，观望周围动静",
            "turn": turn_num,
            "location": npc.current_location,
            "elapsed_time": elapsed,
            "status": "fallback",
            "original_response": None
        }
