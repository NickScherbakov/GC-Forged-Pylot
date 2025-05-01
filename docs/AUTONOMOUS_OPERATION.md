# Autonomous Operation Guide

## Overview

GC-Forged-Pylot is designed as a self-contained, autonomous system capable of operating with minimal user intervention. This document describes how to use the autonomous operation capabilities, which allow the system to execute tasks, self-improve, and notify users about results.

## The "Egg" Concept

The core philosophy of GC-Forged-Pylot revolves around the concept of an "egg" - a minimal initialization package that:

1. Launches in any environment (Windows, Linux, macOS)
2. Analyzes hardware capabilities automatically
3. Self-configures for optimal performance
4. Executes the assigned task autonomously
5. Improves itself when necessary to complete the task
6. Notifies the user when the task is completed

This approach ensures that users can simply provide a task description, and the system handles everything else - from optimization to execution and self-improvement.

## Using the Autonomous Runner

The autonomous operation is managed through the `run_autonomous.py` script, which serves as the main entry point for task execution:

```bash
python run_autonomous.py "Your task description here"
```

### Command Line Arguments

The script supports multiple command-line arguments to customize the autonomous operation:

| Argument | Description | Default |
|----------|-------------|---------|
| `task` | The task description (required) | - |
| `--cycles` | Maximum number of improvement cycles | 3 |
| `--threshold` | Confidence threshold for completion (0-1) | 0.85 |
| `--notify` | Notification method (log, email, telegram, all) | log |
| `--continuous` | Run in continuous self-improvement mode | False |

### Examples

```bash
# Basic task execution
python run_autonomous.py "Create a Python script that analyzes CSV data"

# Set higher quality requirements
python run_autonomous.py "Optimize database queries for better performance" --threshold 0.95

# Allow more improvement cycles
python run_autonomous.py "Design a responsive UI" --cycles 8

# Get email notifications
python run_autonomous.py "Monitor system security" --notify email

# Run continuously in the background
python run_autonomous.py "Process incoming customer requests" --continuous
```

## Workflow

When running in autonomous mode, the system follows this workflow:

1. **Initialization**
   - The system loads configuration
   - Hardware optimization parameters are determined
   - Components (LLM, memory, execution, etc.) are initialized

2. **Task Analysis**
   - The system analyzes the provided task
   - Required capabilities are identified

3. **Self-Improvement Cycle**
   - Missing functionality is detected
   - New code modules are generated if needed
   - Task execution plans are created
   - Task is executed
   - Results are evaluated for quality (confidence score)

4. **Iteration**
   - If confidence threshold is not met, another cycle begins
   - The system generates feedback to itself
   - Improvements are made before the next attempt
   - This continues until threshold is met or max cycles reached

5. **Completion**
   - User is notified of completion
   - Results are presented
   - System saves learning for future tasks

## Continuous Mode

In continuous mode (`--continuous` flag), the system:

1. Executes the initial task through improvement cycles
2. Periodically checks for user feedback
3. Updates its approach based on any feedback received
4. Continues executing with enhanced capabilities
5. Runs until reaching the maximum autonomous cycle count
6. Can be extended indefinitely with user feedback

## Notification System

The autonomous agent can notify users through various channels when tasks are completed:

- **Log**: Default method, writes to console and log file
- **Email**: Sends email notifications (requires email configuration)
- **Telegram**: Sends messages via Telegram bot (requires bot configuration)
- **All**: Uses all configured notification channels

To configure additional notification channels, add settings to `config/agent_config.json`:

```json
{
  "notification_channels": {
    "email": {
      "smtp_server": "smtp.example.com",
      "port": 587,
      "username": "your-email@example.com",
      "password": "your-password",
      "recipients": ["recipient@example.com"]
    },
    "telegram": {
      "bot_token": "your-telegram-bot-token",
      "chat_ids": ["your-chat-id"]
    }
  }
}
```

## Using Results as New Input

A powerful feature of the autonomous system is the ability to use results as new input, creating a cycle of continuous refinement:

```bash
# Execute task and feed result as new input
OUTPUT=$(python run_autonomous.py "Create data schema" --quiet)
python run_autonomous.py "$OUTPUT" --cycles 3
```

This pattern is particularly useful when:
- Breaking down complex tasks into stages
- Refining initial results with more specific requirements
- Implementing iterative development processes

## Advanced Configuration

You can fine-tune the autonomous operation by modifying the following files:

- **config/agent_config.json**: General agent configuration
- **config/self_improvement_config.json**: Self-improvement settings
- **config/hardware_profile.json**: Hardware-specific optimizations

## Implementation Architecture

The autonomous operation is implemented through these key components:

- **run_autonomous.py**: Main entry point and CLI
- **src/self_improvement.py**: Self-improvement cycle logic
- **src/core/hardware_optimizer.py**: Hardware profile detection
- **src/core/executor.py**: Task execution engine
- **src/bridge/feedback_handler.py**: User feedback processing

Each component is designed to be modular, allowing for future extensions and improvements.

## Best Practices

For optimal results with autonomous operation:

1. **Provide detailed task descriptions** - The more specific, the better the results
2. **Set appropriate thresholds** - Higher thresholds require better results but take longer
3. **Review generated modules** - Periodically inspect self-generated code for quality
4. **Use feedback effectively** - Provide specific, actionable feedback when needed
5. **Monitor resource usage** - Continuous operation may require resource management

## Troubleshooting

Common issues and solutions:

- **Low confidence scores**: Try increasing the maximum cycles or provide more detailed task descriptions
- **Notification failures**: Check notification configuration in agent_config.json
- **Hardware optimization issues**: Run optimize_llama.py separately to diagnose

## Advanced Use Cases

### Scheduled Tasks

You can schedule autonomous tasks using cron (Linux/macOS) or Task Scheduler (Windows):

```bash
# Linux/macOS crontab example (daily at 2 AM)
0 2 * * * cd /path/to/gc-forged-pylot && python run_autonomous.py "Daily system maintenance" --notify email
```

### Integration with Other Systems

The autonomous agent can be integrated with other systems via APIs or command-line interfaces:

```python
import subprocess

def run_agent_task(task_description):
    result = subprocess.check_output(
        ["python", "run_autonomous.py", task_description, "--quiet"]
    )
    return result.decode('utf-8')

# Usage in another application
analysis_result = run_agent_task("Analyze yesterday's logs for errors")
```