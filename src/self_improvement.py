import os
import time
from typing import List, Dict, Optional
from src.core.llm_interface import LLMInterface
from src.core.executor import Executor
from src.core.memory import Memory
from src.core.reasoning import Reasoning
from src.core.planner import Planner


class SelfImprovement:
    """
    A module enabling GC-Forged-Pylot to improve itself by identifying gaps,
    generating new functionality, and seamlessly integrating it into the system.
    """

    def __init__(self, llm: LLMInterface, memory: Memory, executor: Executor, reasoning: Reasoning, planner: Planner):
        self.llm = llm
        self.memory = memory
        self.executor = executor
        self.reasoning = reasoning
        self.planner = planner

    def analyze_task(self, task_description: str) -> List[str]:
        """
        Analyzes the task description to identify missing functionalities.
        Args:
            task_description (str): A brief description of the user's task.

        Returns:
            List[str]: A list of missing functionalities needed to complete the task.
        """
        analysis_prompt = (
            f"Analyze the following task and identify any missing functionalities "
            f"that the system would need to accomplish it:\n\n{task_description}"
        )
        response = self.llm.generate(analysis_prompt, max_tokens=256)
        return response.text.strip().split("\n")

    def generate_code(self, functionality: str) -> str:
        """
        Generates Python code for the specified functionality using LLM.
        Args:
            functionality (str): The functionality description.

        Returns:
            str: Generated Python code.
        """
        code_prompt = (
            f"Generate a Python module that implements the following functionality:\n\n{functionality}\n\n"
            f"Make sure the code is modular, well-documented, and compatible with the existing system."
        )
        response = self.llm.generate(code_prompt, max_tokens=1024)
        return response.text.strip()

    def integrate_module(self, module_name: str, module_code: str) -> None:
        """
        Integrates the generated module into the system.
        Args:
            module_name (str): The name of the module.
            module_code (str): The Python code of the new module.
        """
        module_path = os.path.join("src", f"{module_name}.py")
        with open(module_path, "w") as file:
            file.write(module_code)

        # Log the integration in memory
        self.memory.add(
            content=f"Integrated new module: {module_name}",
            metadata={"timestamp": time.time(), "module_path": module_path},
        )

    def self_improve(self, task_description: str) -> Optional[str]:
        """
        The main method to analyze a task, generate missing functionalities,
        and integrate them into the system.
        Args:
            task_description (str): A brief description of the user's task.

        Returns:
            Optional[str]: Status message about the self-improvement process.
        """
        print(f"Starting self-improvement for task: {task_description}")
        missing_functionalities = self.analyze_task(task_description)
        if not missing_functionalities:
            print("No missing functionalities identified. Task seems feasible with the current system.")
            return None

        for functionality in missing_functionalities:
            print(f"Generating code for functionality: {functionality}")
            module_code = self.generate_code(functionality)
            module_name = functionality.replace(" ", "_").lower()
            self.integrate_module(module_name, module_code)
            print(f"Successfully integrated module: {module_name}")

        return "Self-improvement process completed successfully."