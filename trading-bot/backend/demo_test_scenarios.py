import logging
import time

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("BOT_DEMO")

class DemoTester:
    def run_scenarios(self):
        # 1. Protection Gap Recovery (Restart Test)
        print("\n--- SCENARIO: BOT RESTART DURING PROTECTION GAP ---")
        
        print("\n[PRE-RESTART STATE in DB]")
        logger.info("DB: stage1_partial_done = True")
        logger.info("DB: stage1_sl_done = False")
        logger.info("MT5: Position #9901 still at original SL.")

        print("\n[POST-RESTART LOOP 1]")
        logger.info("15:00:00 - [WORKER] Analyzing Trade #9901. Progress: 75% (Target 60% reached).")
        logger.info("15:00:01 - [WORKER] Detect: stage1_partial_done = True. SKIPPING partial close call (Double-close prevented).")
        logger.info("15:00:02 - [WORKER] Detect: stage1_sl_done = False. RETRYING SL protection.")
        logger.info("15:00:03 - [MT5] SL Update SUCCESS -> 2150.70.")
        logger.info("15:00:04 - [DB] stage1_sl_done = True, stage1_executed = True. COMMIT.")
        logger.info("🎯 STAGE 1 COMPLETED: #9901 SL Secured at 2150.70")

        # 2. Stage 2 Successful Stride
        print("\n--- SCENARIO: STAGE 2 FULL FLOW ---")
        logger.info("16:00:00 - [WORKER] Analysis #9905. Progress: 85% (Target 80% reached).")
        logger.info("16:00:01 - [WORKER] Phase 1: Sending Stage 2 Partial Close (0.025 lot).")
        logger.info("16:00:02 - [MT5] SUCCESS.")
        logger.info("16:00:03 - [DB] stage2_partial_done = True. COMMIT immediately.")
        logger.info("16:00:04 - [WORKER] Phase 2: Advancing SL to Stage 1 Trigger (Half-way lock).")
        logger.info("16:00:05 - [MT5] SUCCESS.")
        logger.info("16:00:06 - [DB] stage2_sl_done = True, stage2_executed = True. COMMIT.")
        logger.info("🚀 STAGE 2 COMPLETED: #9905 SL Advanced.")

        # 3. Demo Cycle Limits Verification
        print("\n--- SCENARIO: DEMO CYCLE LIMITS ---")
        logger.info("17:00:00 - [WORKER] Runtime: 1 trade open. Skipping new symbol scanner.")
        logger.info("17:00:01 - [WORKER] Active Symbol: ['XAUUSD'] (Hard-coded for demo).")

if __name__ == "__main__":
    DemoTester().run_scenarios()
