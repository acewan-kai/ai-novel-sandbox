"""快速测试 - 仅5回合验证"""
import asyncio
import config
from sandbox_engine import SandboxEngine
from world_state import WorldState
from npc import NPCManager
from llm_client import DeepSeekClient
from event_logger import EventLogger

async def quick_test():
    print("[TEST] 快速验证 - 5回合测试\n")
    
    # 临时修改回合数
    original_turns = config.SIMULATION_CONFIG["total_turns"]
    config.SIMULATION_CONFIG["total_turns"] = 5
    
    # 初始化
    engine = SandboxEngine(None, None, None, None)
    engine = await engine._ainit() if hasattr(engine, '_ainit') else setup_engine()
    
    # 手动初始化
    world_state = WorldState()
    npc_manager = NPCManager()
    npcs = npc_manager.load_from_config(config.NPC_CONFIG_PATH)
    for npc in npcs:
        npc_manager.add_npc(npc)
    client = DeepSeekClient()
    logger = EventLogger(config.EVENT_LOG_FILE)
    engine = SandboxEngine(world_state, npc_manager, logger, client)
    
    # 运行5回合
    for turn in range(1, 6):
        await engine.run_turn(turn)
    
    # 输出结果
    events = logger.events
    success = len([e for e in events if e.get("status") == "success"])
    print(f"\n[RESULT] 5回合完成: {success}/5 成功")
    
    # 恢复原始配置
    config.SIMULATION_CONFIG["total_turns"] = original_turns

def setup_engine():
    from world_state import WorldState
    from npc import NPCManager
    from llm_client import DeepSeekClient
    from event_logger import EventLogger
    
    world_state = WorldState()
    npc_manager = NPCManager()
    npcs = npc_manager.load_from_config(config.NPC_CONFIG_PATH)
    for npc in npcs:
        npc_manager.add_npc(npc)
    client = DeepSeekClient()
    logger = EventLogger(config.EVENT_LOG_FILE)
    return SandboxEngine(world_state, npc_manager, logger, client)

if __name__ == "__main__":
    asyncio.run(quick_test())
