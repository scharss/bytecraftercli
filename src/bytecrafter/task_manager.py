"""
Sistema de gestión de tareas para Bytecrafter CLI.
Similar a la herramienta new_task de Cline para dividir tareas complejas.
"""

import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: float
    parent_task_id: Optional[str] = None
    subtasks: List[str] = None
    progress: float = 0.0
    estimated_duration: Optional[int] = None
    tags: List[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.subtasks is None:
            self.subtasks = []
        if self.tags is None:
            self.tags = []

class TaskManager:
    """Gestor de tareas para dividir trabajos complejos en subtareas manejables."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.current_task_id: Optional[str] = None
        self.task_counter = 0
        
    def _generate_task_id(self) -> str:
        """Genera un ID único para una tarea."""
        self.task_counter += 1
        return f"task_{int(time.time())}_{self.task_counter}"
    
    def create_task(self, description: str, priority: TaskPriority = TaskPriority.MEDIUM,
                   parent_task_id: Optional[str] = None, tags: List[str] = None) -> str:
        """Crea una nueva tarea."""
        try:
            task_id = self._generate_task_id()
            
            task = Task(
                id=task_id,
                description=description,
                status=TaskStatus.PENDING,
                priority=priority,
                created_at=time.time(),
                parent_task_id=parent_task_id,
                tags=tags or []
            )
            
            self.tasks[task_id] = task
            
            # Si es una subtarea, añadirla a la tarea padre
            if parent_task_id and parent_task_id in self.tasks:
                self.tasks[parent_task_id].subtasks.append(task_id)
            
            result = [
                f"✅ Tarea creada: {description}",
                f"🆔 ID: {task_id}",
                f"⭐ Prioridad: {priority.name}"
            ]
            
            if parent_task_id:
                result.append(f"👆 Tarea padre: {parent_task_id}")
            
            if tags:
                result.append(f"🏷️ Tags: {', '.join(tags)}")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Error creando tarea: {e}"
    
    def start_task(self, task_id: str) -> str:
        """Inicia una tarea específica."""
        try:
            if task_id not in self.tasks:
                return f"❌ Tarea '{task_id}' no encontrada"
            
            task = self.tasks[task_id]
            task.status = TaskStatus.IN_PROGRESS
            self.current_task_id = task_id
            
            return f"🚀 Tarea iniciada: {task.description} (ID: {task_id})"
            
        except Exception as e:
            return f"❌ Error iniciando tarea: {e}"
    
    def complete_task(self, task_id: str, notes: str = "") -> str:
        """Marca una tarea como completada."""
        try:
            if task_id not in self.tasks:
                return f"❌ Tarea '{task_id}' no encontrada"
            
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.progress = 100.0
            
            if notes:
                task.notes = notes
            
            result = [
                f"✅ Tarea completada: {task.description}",
                f"🆔 ID: {task_id}"
            ]
            
            if notes:
                result.append(f"📋 Notas: {notes}")
            
            # Si era la tarea actual, limpiar
            if self.current_task_id == task_id:
                self.current_task_id = None
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Error completando tarea: {e}"
    
    def break_down_task(self, task_id: str, subtask_descriptions: List[str]) -> str:
        """Divide una tarea en subtareas más pequeñas."""
        try:
            if task_id not in self.tasks:
                return f"❌ Tarea '{task_id}' no encontrada"
            
            parent_task = self.tasks[task_id]
            created_subtasks = []
            
            for desc in subtask_descriptions:
                result = self.create_task(
                    description=desc,
                    priority=parent_task.priority,
                    parent_task_id=task_id,
                    tags=parent_task.tags.copy()
                )
                # Extraer el ID de la respuesta
                lines = result.split('\n')
                for line in lines:
                    if "ID: " in line:
                        subtask_id = line.split("ID: ")[1]
                        created_subtasks.append(subtask_id)
                        break
            
            result = [
                f"🔨 Tarea dividida: {parent_task.description}",
                f"📊 Subtareas creadas: {len(created_subtasks)}",
                ""
            ]
            
            for i, subtask_id in enumerate(created_subtasks, 1):
                if subtask_id in self.tasks:
                    subtask = self.tasks[subtask_id]
                    result.append(f"  {i}. {subtask.description} (ID: {subtask_id})")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Error dividiendo tarea: {e}"
    
    def list_tasks(self, status_filter: Optional[TaskStatus] = None) -> str:
        """Lista todas las tareas con filtros opcionales."""
        try:
            filtered_tasks = []
            
            for task in self.tasks.values():
                if status_filter and task.status != status_filter:
                    continue
                filtered_tasks.append(task)
            
            if not filtered_tasks:
                return "📭 No se encontraron tareas"
            
            # Ordenar por prioridad y fecha
            filtered_tasks.sort(key=lambda t: (t.priority.value, t.created_at), reverse=True)
            
            result = [f"📋 Lista de tareas ({len(filtered_tasks)} encontradas):"]
            
            if status_filter:
                result.append(f"🔍 Filtro estado: {status_filter.value}")
            
            result.append("")
            
            for task in filtered_tasks:
                status_icon = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.IN_PROGRESS: "🔄",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.FAILED: "❌"
                }.get(task.status, "❓")
                
                priority_icon = {
                    TaskPriority.LOW: "🟢",
                    TaskPriority.MEDIUM: "🟡", 
                    TaskPriority.HIGH: "🟠",
                    TaskPriority.URGENT: "🔴"
                }.get(task.priority, "⚪")
                
                task_line = f"{status_icon} {priority_icon} {task.description} (ID: {task.id})"
                
                if task.progress > 0:
                    task_line += f" - {task.progress}%"
                
                if task.subtasks:
                    task_line += f" [{len(task.subtasks)} subtareas]"
                
                result.append(task_line)
            
            return "\n".join(result)
            
        except Exception as e:
            return f"❌ Error listando tareas: {e}"
    
    def get_current_task(self) -> str:
        """Obtiene información de la tarea actual."""
        try:
            if not self.current_task_id:
                return "📭 No hay tarea activa"
            
            task = self.tasks[self.current_task_id]
            return f"🔄 Tarea actual: {task.description} (ID: {task.id}) - {task.progress}%"
            
        except Exception as e:
            return f"❌ Error obteniendo tarea actual: {e}"

# Instancia global del gestor de tareas
task_manager = TaskManager()

def new_task(description: str, priority: str = "medium", parent_task_id: str = None, tags: str = None) -> str:
    """Crea una nueva tarea. Similar a la herramienta new_task de Cline."""
    try:
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        
        priority_enum = priority_map.get(priority.lower(), TaskPriority.MEDIUM)
        
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]
        
        return task_manager.create_task(
            description=description,
            priority=priority_enum,
            parent_task_id=parent_task_id,
            tags=tags_list
        )
        
    except Exception as e:
        return f"❌ Error creando nueva tarea: {e}"

def start_task_work(task_id: str) -> str:
    """Inicia trabajo en una tarea específica."""
    return task_manager.start_task(task_id)

def complete_current_task(notes: str = "") -> str:
    """Completa la tarea actual."""
    if not task_manager.current_task_id:
        return "❌ No hay tarea activa para completar"
    
    return task_manager.complete_task(task_manager.current_task_id, notes)

def break_down_current_task(subtask_descriptions: str) -> str:
    """Divide la tarea actual en subtareas."""
    if not task_manager.current_task_id:
        return "❌ No hay tarea activa para dividir"
    
    try:
        subtasks = [desc.strip() for desc in subtask_descriptions.split(",")]
        return task_manager.break_down_task(task_manager.current_task_id, subtasks)
        
    except Exception as e:
        return f"❌ Error dividiendo tarea: {e}"

def show_task_list(status: str = None) -> str:
    """Muestra lista de tareas con filtros opcionales."""
    try:
        status_enum = None
        if status:
            status_map = {
                "pending": TaskStatus.PENDING,
                "in_progress": TaskStatus.IN_PROGRESS,
                "completed": TaskStatus.COMPLETED,
                "failed": TaskStatus.FAILED
            }
            status_enum = status_map.get(status.lower())
        
        return task_manager.list_tasks(status_enum)
        
    except Exception as e:
        return f"❌ Error mostrando lista de tareas: {e}"

def show_current_task() -> str:
    """Muestra información de la tarea actual."""
    return task_manager.get_current_task()
