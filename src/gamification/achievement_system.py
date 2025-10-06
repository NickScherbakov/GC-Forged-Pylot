#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Achievement System
====================================

Система достижений для геймификации вклада в проект.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class Achievement:
    """Класс, представляющий отдельное достижение"""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        xp: int,
        badge: str,
        category: str = "general"
    ):
        self.id = id
        self.title = title
        self.description = description
        self.xp = xp
        self.badge = badge
        self.category = category
        self.unlocked_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "xp": self.xp,
            "badge": self.badge,
            "category": self.category,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None
        }


class ContributorProfile:
    """Профиль участника с достижениями и уровнем"""
    
    LEVEL_THRESHOLDS = {
        "Новичок": 0,
        "Практикант": 1000,
        "Разработчик": 3000,
        "Эксперт": 7000,
        "Мастер": 15000,
        "Легенда": 30000
    }
    
    def __init__(self, username: str):
        self.username = username
        self.total_xp = 0
        self.achievements: Dict[str, Achievement] = {}
        self.contribution_stats = {
            "commits": 0,
            "prs": 0,
            "issues": 0,
            "code_reviews": 0,
            "bugs_fixed": 0,
            "features_added": 0
        }
    
    def add_xp(self, amount: int) -> Dict[str, Any]:
        """Добавить XP и проверить повышение уровня"""
        old_level = self.get_level()
        self.total_xp += amount
        new_level = self.get_level()
        
        result = {
            "xp_gained": amount,
            "total_xp": self.total_xp,
            "level_up": old_level != new_level,
            "old_level": old_level,
            "new_level": new_level
        }
        
        return result
    
    def unlock_achievement(self, achievement: Achievement) -> bool:
        """Разблокировать достижение"""
        if achievement.id in self.achievements:
            return False
        
        achievement.unlocked_at = datetime.now()
        self.achievements[achievement.id] = achievement
        self.add_xp(achievement.xp)
        return True
    
    def get_level(self) -> str:
        """Получить текущий уровень"""
        for level, threshold in sorted(
            self.LEVEL_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if self.total_xp >= threshold:
                return level
        return "Новичок"
    
    def get_progress_to_next_level(self) -> Dict[str, Any]:
        """Прогресс до следующего уровня"""
        current_level = self.get_level()
        current_threshold = self.LEVEL_THRESHOLDS[current_level]
        
        # Найти следующий уровень
        next_level = None
        next_threshold = None
        for level, threshold in sorted(
            self.LEVEL_THRESHOLDS.items(),
            key=lambda x: x[1]
        ):
            if threshold > self.total_xp:
                next_level = level
                next_threshold = threshold
                break
        
        if next_level is None:
            return {
                "current_level": current_level,
                "is_max_level": True,
                "progress_percent": 100
            }
        
        xp_for_next = next_threshold - self.total_xp
        xp_in_current_range = self.total_xp - current_threshold
        total_range = next_threshold - current_threshold
        progress = (xp_in_current_range / total_range) * 100
        
        return {
            "current_level": current_level,
            "next_level": next_level,
            "current_xp": self.total_xp,
            "xp_for_next_level": xp_for_next,
            "progress_percent": round(progress, 2)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "username": self.username,
            "total_xp": self.total_xp,
            "level": self.get_level(),
            "achievements": [ach.to_dict() for ach in self.achievements.values()],
            "contribution_stats": self.contribution_stats,
            "progress": self.get_progress_to_next_level()
        }


class AchievementSystem:
    """Главный класс системы достижений"""
    
    def __init__(self, data_dir: str = "data/gamification"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.achievements = self._load_achievements()
        self.profiles: Dict[str, ContributorProfile] = {}
    
    def _load_achievements(self) -> Dict[str, Achievement]:
        """Загрузить определения достижений"""
        achievements = {}
        
        # Базовые достижения
        achievement_definitions = [
            {
                "id": "first_commit",
                "title": "Первый шаг",
                "description": "Совершите ваш первый коммит",
                "xp": 100,
                "badge": "🌱",
                "category": "contribution"
            },
            {
                "id": "bug_hunter",
                "title": "Охотник за багами",
                "description": "Найдите и исправьте 5 багов",
                "xp": 500,
                "badge": "🐛",
                "category": "debugging"
            },
            {
                "id": "code_architect",
                "title": "Архитектор кода",
                "description": "Разработайте новый модуль с архитектурной документацией",
                "xp": 1000,
                "badge": "🏗️",
                "category": "architecture"
            },
            {
                "id": "ai_trainer",
                "title": "Тренер ИИ",
                "description": "Создайте 10 улучшений для self-improvement системы",
                "xp": 1500,
                "badge": "🧠",
                "category": "ai"
            },
            {
                "id": "community_builder",
                "title": "Строитель сообщества",
                "description": "Помогите 5 новичкам с их первыми PR",
                "xp": 800,
                "badge": "🤝",
                "category": "community"
            },
            {
                "id": "innovation_master",
                "title": "Мастер инноваций",
                "description": "Предложите и реализуйте уникальную фичу",
                "xp": 2000,
                "badge": "💡",
                "category": "innovation"
            },
            {
                "id": "test_champion",
                "title": "Чемпион тестирования",
                "description": "Добавьте 50+ тестов",
                "xp": 600,
                "badge": "✅",
                "category": "testing"
            },
            {
                "id": "documentation_hero",
                "title": "Герой документации",
                "description": "Создайте или улучшите 10 страниц документации",
                "xp": 700,
                "badge": "📚",
                "category": "documentation"
            },
            {
                "id": "performance_guru",
                "title": "Гуру производительности",
                "description": "Оптимизируйте код и улучшите производительность на 50%+",
                "xp": 1200,
                "badge": "⚡",
                "category": "performance"
            },
            {
                "id": "plugin_creator",
                "title": "Создатель плагинов",
                "description": "Разработайте и опубликуйте плагин",
                "xp": 900,
                "badge": "🔌",
                "category": "extension"
            },
            {
                "id": "early_adopter",
                "title": "Ранний последователь",
                "description": "Один из первых 50 участников проекта",
                "xp": 300,
                "badge": "🌟",
                "category": "special"
            },
            {
                "id": "marathon_runner",
                "title": "Марафонец",
                "description": "Внесите вклад в течение 30 дней подряд",
                "xp": 1500,
                "badge": "🏃",
                "category": "consistency"
            }
        ]
        
        for ach_def in achievement_definitions:
            ach = Achievement(**ach_def)
            achievements[ach.id] = ach
        
        return achievements
    
    def get_or_create_profile(self, username: str) -> ContributorProfile:
        """Получить или создать профиль участника"""
        if username not in self.profiles:
            profile_path = self.data_dir / f"{username}.json"
            if profile_path.exists():
                self.profiles[username] = self._load_profile(username)
            else:
                self.profiles[username] = ContributorProfile(username)
        
        return self.profiles[username]
    
    def _load_profile(self, username: str) -> ContributorProfile:
        """Загрузить профиль из файла"""
        profile_path = self.data_dir / f"{username}.json"
        with open(profile_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        profile = ContributorProfile(username)
        profile.total_xp = data.get("total_xp", 0)
        profile.contribution_stats = data.get("contribution_stats", profile.contribution_stats)
        
        # Загрузить достижения
        for ach_data in data.get("achievements", []):
            if ach_data["id"] in self.achievements:
                ach = self.achievements[ach_data["id"]]
                if ach_data.get("unlocked_at"):
                    ach.unlocked_at = datetime.fromisoformat(ach_data["unlocked_at"])
                profile.achievements[ach.id] = ach
        
        return profile
    
    def save_profile(self, username: str):
        """Сохранить профиль в файл"""
        if username not in self.profiles:
            return
        
        profile = self.profiles[username]
        profile_path = self.data_dir / f"{username}.json"
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
    
    def check_and_unlock_achievement(
        self,
        username: str,
        achievement_id: str
    ) -> Optional[Dict[str, Any]]:
        """Проверить и разблокировать достижение"""
        if achievement_id not in self.achievements:
            return None
        
        profile = self.get_or_create_profile(username)
        achievement = self.achievements[achievement_id]
        
        if profile.unlock_achievement(achievement):
            self.save_profile(username)
            return {
                "achievement": achievement.to_dict(),
                "profile": profile.to_dict()
            }
        
        return None
    
    def record_contribution(
        self,
        username: str,
        contribution_type: str,
        details: Dict[str, Any] = None
    ):
        """Записать вклад и проверить достижения"""
        profile = self.get_or_create_profile(username)
        
        # Обновить статистику
        if contribution_type in profile.contribution_stats:
            profile.contribution_stats[contribution_type] += 1
        
        # Проверить достижения
        unlocked = []
        
        # Первый коммит
        if contribution_type == "commits" and profile.contribution_stats["commits"] == 1:
            result = self.check_and_unlock_achievement(username, "first_commit")
            if result:
                unlocked.append(result)
        
        # Охотник за багами
        if profile.contribution_stats["bugs_fixed"] >= 5:
            result = self.check_and_unlock_achievement(username, "bug_hunter")
            if result:
                unlocked.append(result)
        
        self.save_profile(username)
        
        return {
            "profile": profile.to_dict(),
            "unlocked_achievements": unlocked
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить таблицу лидеров"""
        all_profiles = []
        
        # Загрузить все профили
        for profile_file in self.data_dir.glob("*.json"):
            username = profile_file.stem
            profile = self.get_or_create_profile(username)
            all_profiles.append(profile)
        
        # Сортировать по XP
        all_profiles.sort(key=lambda p: p.total_xp, reverse=True)
        
        # Вернуть топ N
        return [p.to_dict() for p in all_profiles[:limit]]
    
    def get_achievement_statistics(self) -> Dict[str, Any]:
        """Получить статистику по достижениям"""
        stats = {
            "total_achievements": len(self.achievements),
            "total_contributors": len(list(self.data_dir.glob("*.json"))),
            "achievement_unlock_rates": {}
        }
        
        # Подсчитать частоту разблокировки каждого достижения
        for ach_id, achievement in self.achievements.items():
            unlock_count = 0
            for profile_file in self.data_dir.glob("*.json"):
                profile = self.get_or_create_profile(profile_file.stem)
                if ach_id in profile.achievements:
                    unlock_count += 1
            
            stats["achievement_unlock_rates"][ach_id] = {
                "title": achievement.title,
                "badge": achievement.badge,
                "unlock_count": unlock_count,
                "unlock_rate": round(
                    unlock_count / max(stats["total_contributors"], 1) * 100,
                    2
                )
            }
        
        return stats


def main():
    """Демонстрация работы системы достижений"""
    system = AchievementSystem()
    
    # Симуляция вклада
    print("=== Демонстрация системы достижений ===\n")
    
    username = "demo_user"
    
    # Первый коммит
    print(f"Пользователь {username} делает первый коммит...")
    result = system.record_contribution(username, "commits")
    if result["unlocked_achievements"]:
        for unlock in result["unlocked_achievements"]:
            ach = unlock["achievement"]
            print(f"🎉 Разблокировано: {ach['badge']} {ach['title']}")
            print(f"   {ach['description']}")
            print(f"   +{ach['xp']} XP\n")
    
    # Исправление багов
    print(f"Пользователь {username} исправляет 5 багов...")
    for i in range(5):
        system.record_contribution(username, "bugs_fixed")
    
    result = system.record_contribution(username, "bugs_fixed")
    if result["unlocked_achievements"]:
        for unlock in result["unlocked_achievements"]:
            ach = unlock["achievement"]
            print(f"🎉 Разблокировано: {ach['badge']} {ach['title']}")
            print(f"   {ach['description']}")
            print(f"   +{ach['xp']} XP\n")
    
    # Показать профиль
    profile = system.get_or_create_profile(username)
    print(f"\n=== Профиль {username} ===")
    print(f"Уровень: {profile.get_level()}")
    print(f"Общий XP: {profile.total_xp}")
    print(f"Достижения разблокировано: {len(profile.achievements)}")
    
    progress = profile.get_progress_to_next_level()
    if not progress.get("is_max_level"):
        print(f"Прогресс до следующего уровня ({progress['next_level']}): {progress['progress_percent']}%")
    
    print("\n=== Разблокированные достижения ===")
    for ach in profile.achievements.values():
        print(f"{ach.badge} {ach.title} - {ach.description}")
    
    # Таблица лидеров
    print("\n=== Таблица лидеров ===")
    leaderboard = system.get_leaderboard(5)
    for i, profile_data in enumerate(leaderboard, 1):
        print(f"{i}. {profile_data['username']} - {profile_data['level']} ({profile_data['total_xp']} XP)")


if __name__ == "__main__":
    main()
