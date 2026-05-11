"""
沙盒引擎核心
"""

import asyncio
import time
from typing import List, Optional
from datetime import datetime
from pathlib import Path

import config
from world_state import WorldState
from npc import NPC, NPCManager
from llm_client import DeepSeekClient, simulate_npc_action
from event_logger import EventLogger


class SandboxEngine:
    """沙盒引擎"""
    
    def __init__(
        self,
        world_state: WorldState,
        npc_manager: NPCManager,
        logger: EventLogger,
        client: DeepSeekClient
    ):
        self.world_state = world_state
        self.npc_manager = npc_manager
        self.logger = logger
        self.client = client
        self.is_running = False
        self.total_turns = config.SIMULATION_CONFIG["total_turns"]
        
    async def run_turn(self, turn_num: int) -> float:
        """运行单个回合"""
        print(f"\n{'='*60}")
        print(f"回合 {turn_num} | 第{self.world_state.current_day}天 {self.world_state.time_of_day}")
        print(f"{'='*60}")
        
        turn_start = time.time()
        alive_npcs = self.npc_manager.get_alive()
        
        # 更新世界状态
        self.world_state.advance_turn()
        
        # 并发执行所有NPC动作
        tasks = [
            simulate_npc_action(
                self.client,
                npc,
                self.world_state,
                self.npc_manager,
                turn_num
            )
            for npc in alive_npcs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 记录事件
        for npc, result in zip(alive_npcs, results):
            if isinstance(result, Exception):
                print(f"  [WARN] {npc.name} 出错: {result}")
                result = {"actor": npc.name, "turn": turn_num, "status": "error"}
                self.logger.log_event(result, npc.id, self.world_state)
            else:
                self.logger.log_event(result, npc.id, self.world_state)
                status_icon = "[OK]" if result.get("status") == "success" else "[WARN]"
                print(f"  {status_icon} {npc.name}: {result.get('action', '...')[:50]}...")
        
        turn_elapsed = time.time() - turn_start
        print(f"\n回合耗时: {turn_elapsed:.2f}秒")
        
        return turn_elapsed
    
    async def run_simulation(self, progress_callback=None):
        """运行完整模拟"""
        print("="*60)
        print("[雾隐村] 沙盒模拟启动")
        print("="*60)
        print(f"世界: {self.world_state.name}")
        print(f"时代: {self.world_state.era}")
        print(f"角色数: {len(self.npc_manager.get_all())}")
        print(f"目标回合: {self.total_turns}")
        print("="*60)
        
        self.is_running = True
        turn_delays = []
        
        try:
            for turn in range(1, self.total_turns + 1):
                elapsed = await self.run_turn(turn)
                turn_delays.append(elapsed)
                
                # 进度回调
                if progress_callback:
                    progress_callback(turn, self.total_turns, elapsed)
                
                # 每10回合打印一次统计
                if turn % 10 == 0:
                    metrics = self.logger.get_metrics()
                    print(f"\n[STAT] 第{turn}回合统计:")
                    print(f"   成功事件: {metrics['successful_events']}/{metrics['total_turns']}")
                    print(f"   跨角色互动: {metrics['unique_cross_interactions']}个")
                    print(f"   故事感时刻: {metrics['storylike_moments']}个")
                    print(f"   平均延迟: {metrics['avg_turn_delay']}")
                
                # 短暂休息避免API过载
                if turn < self.total_turns:
                    await asyncio.sleep(0.5)
                    
        except KeyboardInterrupt:
            print("\n\n[中断] 模拟被用户中断")
        finally:
            self.is_running = False
        
        # 最终报告
        metrics = self.logger.get_metrics()
        print("\n" + "="*60)
        print("[REPORT] 模拟完成 - 最终统计")
        print("="*60)
        print(f"总回合: {metrics['total_turns']}")
        print(f"成功事件: {metrics['successful_events']} ({metrics['success_rate']})")
        print(f"非预设互动: {metrics['unique_cross_interactions']}个")
        print(f"故事感时刻: {metrics['storylike_moments']}个")
        print(f"平均延迟: {metrics['avg_turn_delay']}")
        print(f"最大延迟: {metrics['max_turn_delay']}")
        
        return metrics


def create_engine() -> SandboxEngine:
    """创建沙盒引擎"""
    # 确保目录存在
    config.ensure_dirs()
    
    # 加载世界状态
    world_state = WorldState.from_yaml(config.WORLD_CONFIG_PATH)
    
    # 加载NPC
    npcs = NPC.from_yaml(config.NPC_CONFIG_PATH)
    npc_manager = NPCManager(npcs)
    
    # 初始化NPC位置
    for npc in npcs:
        loc = world_state.get_location_by_name(npc.current_location)
        if loc and npc.id not in loc.NPCs:
            loc.NPCs.append(npc.id)
    
    # 创建客户端和日志器
    client = DeepSeekClient()
    logger = EventLogger(config.EVENT_LOG_FILE)
    
    # 创建引擎
    engine = SandboxEngine(world_state, npc_manager, logger, client)
    
    return engine


async def main():
    """主函数"""
    print("PoC Sandbox Engine - 沉浸式AI小说创作平台")
    print()
    
    # 检查API密钥
    if not config.DEEPSEEK_API_KEY:
        print("[ERROR] 请先在 .env 文件中设置 DEEPSEEK_API_KEY")
        print("   示例: DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx")
        print()
        print("   如果想使用模拟模式测试，请在 config.py 中设置 MOCK_MODE=True")
        return
    else:
        print(f"[INFO] API密钥已设置 (长度: {len(config.DEEPSEEK_API_KEY)})")
        print(f"[INFO] API URL: {config.DEEPSEEK_API_URL}")
        print(f"[INFO] 模型: {config.DEEPSEEK_MODEL}")
    
    # 创建引擎
    engine = create_engine()
    
    # 进度回调
    def progress(turn, total, elapsed):
        pct = turn / total * 100
        bar_len = 30
        filled = int(bar_len * turn / total)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"\r  进度: [{bar}] {pct:.1f}% | 回合 {turn}/{total} | 延迟 {elapsed:.1f}s", end="", flush=True)
    
    # 运行模拟
    metrics = await engine.run_simulation(progress_callback=progress)
    
    # 生成报告
    report_file = config.LOG_DIR / "poc_report.md"
    engine.logger.generate_report(report_file)
    print(f"\n\n[INFO] 报告已生成: {report_file}")
    
    # 检查验收标准
    print("\n" + "="*60)
    print("验收标准检查")
    print("="*60)
    
    criteria = metrics['validation']
    all_pass = all([
        criteria['all_npcs_survived_100_turns'],
        criteria['at_least_3_unscripted_interactions'],
        criteria['at_least_1_storylike_moment']
    ])
    
    check1 = "[PASS]" if criteria['all_npcs_survived_100_turns'] else "[FAIL]"
    check2 = "[PASS]" if criteria['at_least_3_unscripted_interactions'] else "[FAIL]"
    check3 = "[PASS]" if criteria['at_least_1_storylike_moment'] else "[FAIL]"
    check4 = "[PASS]" if criteria['single_turn_delay_under_15s'] else "[WARN]"
    
    print(f"  {check1} 10个NPC全部存活运行100回合")
    print(f"  {check2} 产生至少3个非预设跨角色互动")
    print(f"  {check3} 至少1个互动具有故事感")
    print(f"  {check4} 单回合延迟 < 15秒")
    
    print("\n" + "="*60)
    if all_pass:
        print("GO - PoC验证通过! 可以进入第2步: P0 MVP 构建")
    else:
        print("NO-GO - 需要调整后重试")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
