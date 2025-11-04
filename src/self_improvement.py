import os
import time
import logging
import json
from typing import List, Dict, Optional, Tuple, Any, Union
from src.core.llm_interface import LLMInterface
from src.core.executor import Executor
from src.core.memory import Memory
from src.core.reasoning import Reasoning
from src.core.planner import Planner
from src.bridge.feedback_handler import FeedbackHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('self_improvement.log')
    ]
)
logger = logging.getLogger("self_improvement")


class SelfImprovement:
    """
    A module enabling GC-Forged-Pylot to improve itself by identifying gaps,
    generating new functionality, and seamlessly integrating it into the system.
    
    This module implements a complete self-improvement cycle:
    1. Task analysis - identifying required capabilities
    2. Code generation - creating missing functionalities
    3. Integration - adding new modules to the system
    4. Result evaluation - assessing the quality of task execution
    5. Feedback processing - learning from results and user feedback
    6. Continuous improvement - iterative refinement based on experience
    """

    def __init__(self, llm: LLMInterface, memory: Memory, executor: Executor, 
                 reasoning: Reasoning, planner: Planner, 
                 feedback_handler: Optional[FeedbackHandler] = None):
        self.llm = llm
        self.memory = memory
        self.executor = executor
        self.reasoning = reasoning
        self.planner = planner
        self.feedback_handler = feedback_handler
        self.improvement_cycle_count = 0
        self.improvement_history = []
        self.confidence_threshold = 0.85  # Confidence threshold for successful execution
        
        # Load self-improvement configuration if it exists
        self._load_config()

    def _load_config(self) -> None:
        """Loads self-improvement configuration."""
        config_path = os.path.join("config", "self_improvement_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self.confidence_threshold = config.get("confidence_threshold", 0.85)
                # Other configuration parameters can be added here
                logger.info(f"Loaded self-improvement configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading self-improvement configuration: {e}")
        else:
            # Create конфигурацию по умолчанию
            self._save_config()
    
    def _save_config(self) -> None:
        """Сохраняет конфигурацию self-improvement."""
        config_path = os.path.join("config", "self_improvement_config.json")
        config = {
            "confidence_threshold": self.confidence_threshold,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "improvement_cycle_count": self.improvement_cycle_count
        }
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved self-improvement configuration to {config_path}")
        except Exception as e:
            logger.error(f"Error saving self-improvement configuration: {e}")

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

    def evaluate_result(self, task_description: str, result: Any) -> Tuple[float, str]:
        """
        Оценивает результат execution задания с точки зрения качества и соответствия.
        
        Args:
            task_description: Исходное описание задания
            result: Результат execution задания
            
        Returns:
            Tuple[float, str]: Оценка уверенности (0-1) и текстовое обоснование
        """
        evaluation_prompt = (
            f"Evaluate how well the following result addresses the given task. "
            f"Task description: {task_description}\n\n"
            f"Result: {result}\n\n"
            f"Rate the confidence level from 0 to 1 (where 1 is perfect) and explain your reasoning."
        )
        
        response = self.llm.generate(evaluation_prompt, max_tokens=512)
        response_text = response.text.strip()
        
        # Извлекаем оценку уверенности
        try:
            # Ищем числовое значение от 0 до 1
            import re
            confidence_matches = re.findall(r'(?:confidence|score|rating|level)[:\s]+([01](?:\.\d+)?)', 
                                           response_text.lower())
            if confidence_matches:
                confidence = float(confidence_matches[0])
            else:
                # Если явное число не найдено, используем вызов LLM для извлечения
                extraction_prompt = (
                    f"Based on this evaluation, extract only the confidence score as a number between 0 and 1:\n\n"
                    f"{response_text}"
                )
                extraction_response = self.llm.generate(extraction_prompt, max_tokens=16)
                try:
                    confidence = float(extraction_response.text.strip())
                except ValueError:
                    confidence = 0.5  # Значение по умолчанию при невозможности извлечь
        except Exception as e:
            logger.error(f"Error extracting confidence score: {e}")
            confidence = 0.5
            
        # Ограничиваем оценку диапазоном [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence, response_text
    
    def process_user_feedback(self, task_description: str, result: Any, 
                              feedback: str) -> Dict[str, Any]:
        """
        Обрабатывает обратную связь от пользователя для улучшения системы.
        
        Args:
            task_description: Исходное описание задания
            result: Результат execution задания
            feedback: Обратная связь от пользователя
            
        Returns:
            Dict[str, Any]: Структура с извлеченными уроками и планом улучшений
        """
        if not feedback:
            return {
                "learning_points": [],
                "improvement_plan": [],
                "feedback_quality": 0.0
            }
            
        analysis_prompt = (
            f"Analyze the following user feedback regarding a task result:\n\n"
            f"Task: {task_description}\n\n"
            f"Result provided to user: {result}\n\n"
            f"User feedback: {feedback}\n\n"
            f"Extract: 1) Key learning points, 2) Specific improvements needed, "
            f"3) Rate the helpfulness of this feedback from 0 to 1."
        )
        
        response = self.llm.generate(analysis_prompt, max_tokens=768)
        response_text = response.text.strip()
        
        # Извлечение структурированной информации
        try:
            # Use reasoning для структурированного анализа
            structure_prompt = (
                f"Convert this feedback analysis into a structured JSON format with these keys:\n"
                f"- learning_points: array of strings\n"
                f"- improvement_plan: array of action items\n"
                f"- feedback_quality: number between 0 and 1\n\n"
                f"Analysis to convert: {response_text}"
            )
            structure_response = self.reasoning.analyze(structure_prompt, format_output="json")
            feedback_analysis = json.loads(structure_response)
        except Exception as e:
            logger.error(f"Error structuring feedback analysis: {e}")
            feedback_analysis = {
                "learning_points": ["Error processing feedback"],
                "improvement_plan": ["Review feedback manually"],
                "feedback_quality": 0.5
            }
        
        # Сохраняем извлеченные уроки в память системы
        for point in feedback_analysis["learning_points"]:
            self.memory.add(
                content=f"Learning point from user feedback: {point}",
                metadata={
                    "type": "feedback_learning",
                    "timestamp": time.time(),
                    "task": task_description[:100],  # Первые 100 символов задания
                    "feedback_quality": feedback_analysis["feedback_quality"]
                }
            )
        
        return feedback_analysis
    
    def send_notification(self, message: str, channel: str = "log", 
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Отправляет уведомление пользователю по выбранному каналу.
        
        Args:
            message: Текст уведомления
            channel: Канал уведомления ("log", "email", "telegram", и т.д.)
            metadata: Дополнительные данные для уведомления
            
        Returns:
            bool: Успешность отправки уведомления
        """
        if metadata is None:
            metadata = {}
            
        # Базовая реализация - только логирование
        logger.info(f"Notification ({channel}): {message}")
        
        # Если доступны дополнительные каналы через FeedbackHandler
        if self.feedback_handler and hasattr(self.feedback_handler, "send_notification"):
            try:
                return self.feedback_handler.send_notification(message, channel, metadata)
            except Exception as e:
                logger.error(f"Error sending notification via {channel}: {e}")
                return False
                
        return True

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
        
    def execute_task_with_improvement(self, task_description: str, 
                                     max_improvement_cycles: int = 3,
                                     notify_on_completion: bool = True) -> Dict[str, Any]:
        """
        Выполняет задание с циклом self-improvement до достижения 
        удовлетворительного результата или максимального числа итераций.
        
        Args:
            task_description: Описание задания
            max_improvement_cycles: Максимальное количество циклов улучшения
            notify_on_completion: Отправлять ли уведомление по окончании
            
        Returns:
            Dict[str, Any]: Результат execution задания и метаданные процесса
        """
        logger.info(f"Starting task execution with self-improvement: {task_description[:100]}...")
        
        # Run цикл execution и self-improvement
        current_cycle = 0
        best_result = None
        best_confidence = 0.0
        improvement_history = []
        
        while current_cycle < max_improvement_cycles:
            current_cycle += 1
            logger.info(f"Beginning improvement cycle {current_cycle} of {max_improvement_cycles}")
            
            # Шаг 1: Анализируем задание и улучшаем систему при необходимости
            self.self_improve(task_description)
            
            # Шаг 2: Планируем выполнение задания
            plan = self.planner.create_plan(task_description)
            logger.info(f"Created execution plan with {len(plan['steps'])} steps")
            
            # Шаг 3: Выполняем задание согласно плану
            try:
                result = self.executor.execute_plan(plan)
                execution_success = True
                execution_error = None
            except Exception as e:
                logger.error(f"Error executing task: {e}")
                result = f"Error: {str(e)}"
                execution_success = False
                execution_error = str(e)
            
            # Шаг 4: Оцениваем результат
            confidence, evaluation = self.evaluate_result(task_description, result)
            
            # Сохраняем информацию о текущем цикле
            cycle_info = {
                "cycle": current_cycle,
                "timestamp": time.time(),
                "result_summary": str(result)[:200] + "..." if isinstance(result, str) and len(str(result)) > 200 else str(result),
                "confidence": confidence,
                "evaluation_summary": evaluation[:200] + "..." if len(evaluation) > 200 else evaluation,
                "execution_success": execution_success,
                "execution_error": execution_error
            }
            improvement_history.append(cycle_info)
            
            # Если достигли необходимой уверенности, останавливаемся
            if confidence > best_confidence:
                best_confidence = confidence
                best_result = result
                
            if confidence >= self.confidence_threshold:
                logger.info(f"Achieved sufficient confidence ({confidence:.2f}) in cycle {current_cycle}")
                break
                
            # Если это не последний цикл и уверенность недостаточна
            if current_cycle < max_improvement_cycles:
                # Create самообратную связь на основе оценки
                self_feedback_prompt = (
                    f"Based on the evaluation of the previous result:\n\n{evaluation}\n\n"
                    f"Generate specific feedback to improve the system's approach to this task: {task_description}"
                )
                self_feedback = self.llm.generate(self_feedback_prompt, max_tokens=512).text
                
                # Применяем обратную связь как новый входной параметр для улучшения
                logger.info(f"Applying self-generated feedback for cycle {current_cycle + 1}")
                feedback_analysis = self.process_user_feedback(
                    task_description, result, self_feedback
                )
                
                # Add план улучшения в историю
                cycle_info["improvement_plan"] = feedback_analysis.get("improvement_plan", [])
        
        # Update счетчик циклов self-improvement
        self.improvement_cycle_count += current_cycle
        self.improvement_history.extend(improvement_history)
        self._save_config()
        
        # Отправляем уведомление о завершении
        if notify_on_completion:
            confidence_text = f"{best_confidence:.2f}" if best_confidence is not None else "unknown"
            notification = (
                f"Task completed after {current_cycle} improvement cycles.\n"
                f"Confidence: {confidence_text}\n"
                f"Task: {task_description[:100]}{'...' if len(task_description) > 100 else ''}"
            )
            self.send_notification(notification, "log")
            
        # Формируем итоговый результат
        final_result = {
            "result": best_result,
            "confidence": best_confidence,
            "cycles_completed": current_cycle,
            "threshold_met": best_confidence >= self.confidence_threshold,
            "improvement_history": improvement_history
        }
        
        return final_result
    
    def continuous_improvement_daemon(self, initial_task: str, 
                                     feedback_poll_interval: int = 3600,
                                     max_autonomous_cycles: int = 10) -> None:
        """
        Запускает непрерывный цикл self-improvement, который выполняет задания 
        и периодически проверяет обратную связь от пользователя.
        
        Args:
            initial_task: Начальное задание для execution
            feedback_poll_interval: Интервал проверки feedback (в секундах)
            max_autonomous_cycles: Максимальное число автономных циклов улучшения
        """
        logger.info(f"Starting continuous improvement daemon with initial task: {initial_task[:100]}")
        
        current_task = initial_task
        autonomous_cycles = 0
        last_feedback_check = time.time()
        
        while autonomous_cycles < max_autonomous_cycles:
            # Execute текущее задание с самосовершенствованием
            result = self.execute_task_with_improvement(
                current_task, 
                max_improvement_cycles=3,
                notify_on_completion=True
            )
            
            autonomous_cycles += 1
            logger.info(f"Completed autonomous cycle {autonomous_cycles} with confidence {result['confidence']:.2f}")
            
            # Check наличие feedback от пользователя
            if time.time() - last_feedback_check >= feedback_poll_interval:
                last_feedback_check = time.time()
                feedback = None
                
                # Если есть FeedbackHandler, пытаемся получить обратную связь
                if self.feedback_handler:
                    try:
                        feedback = self.feedback_handler.get_pending_feedback()
                    except Exception as e:
                        logger.error(f"Error fetching feedback: {e}")
                        
                if feedback:
                    # Обрабатываем обратную связь от пользователя
                    logger.info("Received user feedback, processing...")
                    feedback_analysis = self.process_user_feedback(
                        current_task, result["result"], feedback
                    )
                    
                    # Формируем новое задание на основе feedback
                    if feedback_analysis.get("improvement_plan"):
                        improvement_plan = "\n".join(feedback_analysis["improvement_plan"])
                        new_task_prompt = (
                            f"Based on the original task: {current_task}\n\n"
                            f"And the improvement plan: {improvement_plan}\n\n"
                            f"Formulate a new task description that incorporates these improvements."
                        )
                        new_task = self.llm.generate(new_task_prompt, max_tokens=512).text.strip()
                        current_task = new_task
                        autonomous_cycles = 0  # Сбрасываем счетчик после получения feedback
                        logger.info(f"Updated task based on feedback: {current_task[:100]}")
                    
            # Если достигли достаточной уверенности, сообщаем об этом
            if result["threshold_met"]:
                self.send_notification(
                    f"Achieved high confidence ({result['confidence']:.2f}) for task: {current_task[:100]}",
                    "log"
                )
            
            # Небольшая пауза перед проверкой необходимости следующего цикла
            time.sleep(10)
        
        logger.info(f"Continuous improvement daemon finished after {autonomous_cycles} autonomous cycles")