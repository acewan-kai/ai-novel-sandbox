"""
快速测试脚本 - 运行少量回合测试
"""
import asyncio
import config
from sandbox_engine import create_engine

async def quick_test():
    """快速测试 - 运行5回合"""
    print("="*60)
    print("快速测试模式 - 5回合")
    print("="*60)
    
    # 临时修改配置
    original_turns = config.SIMULATION_CONFIG["total_turns"]
    config.SIMULATION_CONFIG["total_turns"] = 5
    
    try:
        engine = create_engine()
        metrics = await engine.run_simulation()
        
        print("\n" + "="*60)
        print("测试完成")
        print("="*60)
        return metrics
    finally:
        config.SIMULATION_CONFIG["total_turns"] = original_turns

if __name__ == "__main__":
    asyncio.run(quick_test())
