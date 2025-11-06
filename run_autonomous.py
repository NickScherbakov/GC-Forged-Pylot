#!/usr/bin/env python
"""
Script to launch GC-Forged-Pylot in autonomous mode with self-improvement.
Takes a task as a parameter and starts an autonomous self-learning cycle.
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pylot_agent.log')
    ]
)

logger = logging.getLogger("run_autonomous")

# Add project to import path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import load_config
from src.core.hardware_optimizer import HardwareOptimizer
from src.core.llm_interface import create_llm_interface
from src.core.memory import Memory
from src.core.executor import Executor
from src.core.reasoning import Reasoning
from src.core.planner import Planner
from src.bridge.feedback_handler import FeedbackHandler
from src.self_improvement import SelfImprovement


def initialize_system() -> tuple:
    """Initializes all necessary system components."""
    logger.info("Initializing GC-Forged-Pylot system...")
    
    # Load configuration
    config = load_config()
    
    # Optimize parameters for current hardware
    optimizer = HardwareOptimizer()
    optimizer._update_hardware_profile()
    
    # Initialize LLM
    llm = create_llm_interface()
    
    # Initialize base components
    memory = Memory()
    executor = Executor(llm)
    reasoning = Reasoning(llm)
    planner = Planner(llm, reasoning)
    
    # Initialize feedback handler
    feedback_handler = FeedbackHandler(config.get("notification_channels", {}))
    
    # Initialize self-improvement module
    self_improvement = SelfImprovement(
        llm=llm, 
        memory=memory, 
        executor=executor, 
        reasoning=reasoning, 
        planner=planner,
        feedback_handler=feedback_handler
    )
    
    return config, self_improvement, feedback_handler


def main():
    parser = argparse.ArgumentParser(
        description="Run GC-Forged-Pylot in autonomous mode"
    )
    parser.add_argument(
        "task", 
        type=str,
        help="Task for autonomous execution"
    )
    parser.add_argument(
        "--notify", 
        type=str, 
        choices=["log", "email", "telegram", "all"], 
        default="log",
        help="Notification method on completion"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous self-improvement mode"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="Maximum number of improvement cycles"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Confidence threshold for completion (0-1)"
    )
    
    args = parser.parse_args()
    
    # Initialize system
    config, self_improvement, feedback_handler = initialize_system()
    
    # Set user-defined confidence threshold
    self_improvement.confidence_threshold = args.threshold
    
    # Run system in selected mode
    if args.continuous:
        logger.info(f"Running in continuous self-improvement mode with task: {args.task[:100]}")
        self_improvement.continuous_improvement_daemon(
            initial_task=args.task,
            feedback_poll_interval=config.get("feedback_poll_interval", 3600),
            max_autonomous_cycles=10
        )
    else:
        logger.info(f"Running in single task mode with improvement cycles: {args.task[:100]}")
        result = self_improvement.execute_task_with_improvement(
            task_description=args.task,
            max_improvement_cycles=args.cycles,
            notify_on_completion=True
        )
        
        # Display results
        print("\n" + "="*50)
        print(f"Task completed with confidence: {result['confidence']:.2f}")
        print(f"Threshold value: {self_improvement.confidence_threshold} | " +
              f"{'✅ Exceeded' if result['threshold_met'] else '❌ Not reached'}")
        print(f"Improvement cycles: {result['cycles_completed']}")
        print("="*50)
        print("\nResult:")
        print(result['result'])
        print("="*50)
        
        # Send completion notification
        if args.notify != "log":
            channels = []
            if args.notify == "all":
                channels = list(config.get("notification_channels", {}).keys())
            else:
                channels = [args.notify]
                
            for channel in channels:
                self_improvement.send_notification(
                    message=f"Task completed with confidence {result['confidence']:.2f}.",
                    channel=channel,
                    metadata={"task": args.task, "result_summary": str(result['result'])[:200]}
                )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())