"""
Gestor de contexto de proyectos para memoria persistente
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy import String
from .database import get_session, ProjectContext

class ContextManager:
    """Gestiona el contexto y información de proyectos"""
    
    def __init__(self):
        self.current_project = self._detect_current_project()
    
    def _detect_current_project(self) -> str:
        """Detecta el proyecto actual basado en el directorio"""
        try:
            cwd = os.getcwd()
            project_name = os.path.basename(cwd)
            return project_name
        except:
            return "unknown_project"
    
    def save_project_info(self, project_name: str, info_type: str, 
                         data: Dict[str, Any], file_path: str = None) -> bool:
        """Guarda información sobre un proyecto"""
        session = get_session()
        if session is None:
            return False
        
        try:
            # Buscar si ya existe
            existing = session.query(ProjectContext).filter(
                ProjectContext.project_name == project_name,
                ProjectContext.file_path == file_path,
                ProjectContext.context_type == info_type
            ).first()
            
            if existing:
                existing.context_data = data
                existing.last_accessed = datetime.now(timezone.utc)
            else:
                context = ProjectContext(
                    project_name=project_name,
                    file_path=file_path,
                    context_type=info_type,
                    context_data=data
                )
                session.add(context)
            
            session.commit()
            session.close()
            return True
            
        except Exception as e:
            print(f"❌ Error guardando contexto de proyecto: {e}")
            if session:
                session.rollback()
                session.close()
            return False
    
    def get_project_info(self, project_name: str, info_type: str = None) -> List[Dict[str, Any]]:
        """Obtiene información de un proyecto"""
        session = get_session()
        if session is None:
            return []
        
        try:
            query = session.query(ProjectContext).filter(
                ProjectContext.project_name == project_name
            )
            
            if info_type:
                query = query.filter(ProjectContext.context_type == info_type)
            
            contexts = query.order_by(ProjectContext.last_accessed.desc()).all()
            
            results = []
            for ctx in contexts:
                results.append({
                    "type": ctx.context_type,
                    "file_path": ctx.file_path,
                    "data": ctx.context_data,
                    "last_accessed": ctx.last_accessed.isoformat(),
                    "created_at": ctx.created_at.isoformat()
                })
            
            session.close()
            return results
            
        except Exception as e:
            print(f"❌ Error obteniendo contexto de proyecto: {e}")
            if session:
                session.close()
            return []
    
    def save_file_structure(self, project_name: str, structure: Dict[str, Any]) -> bool:
        """Guarda la estructura de archivos de un proyecto"""
        return self.save_project_info(
            project_name=project_name,
            info_type="file_structure",
            data=structure
        )
    
    def get_file_structure(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene la estructura de archivos de un proyecto"""
        contexts = self.get_project_info(project_name, "file_structure")
        return contexts[0]["data"] if contexts else None
    
    def save_file_analysis(self, project_name: str, file_path: str, 
                          analysis: Dict[str, Any]) -> bool:
        """Guarda análisis de un archivo específico"""
        return self.save_project_info(
            project_name=project_name,
            info_type="file_analysis",
            data=analysis,
            file_path=file_path
        )
    
    def get_file_analysis(self, project_name: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Obtiene análisis de un archivo específico"""
        session = get_session()
        if session is None:
            return None
        
        try:
            context = session.query(ProjectContext).filter(
                ProjectContext.project_name == project_name,
                ProjectContext.file_path == file_path,
                ProjectContext.context_type == "file_analysis"
            ).first()
            
            session.close()
            return context.context_data if context else None
            
        except Exception as e:
            print(f"❌ Error obteniendo análisis de archivo: {e}")
            if session:
                session.close()
            return None
    
    def save_user_preferences(self, project_name: str, preferences: Dict[str, Any]) -> bool:
        """Guarda preferencias del usuario para un proyecto"""
        return self.save_project_info(
            project_name=project_name,
            info_type="user_preferences",
            data=preferences
        )
    
    def get_user_preferences(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene preferencias del usuario para un proyecto"""
        contexts = self.get_project_info(project_name, "user_preferences")
        return contexts[0]["data"] if contexts else None
    
    def search_project_context(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca en el contexto de proyectos"""
        session = get_session()
        if session is None:
            return []
        
        try:
            # Buscar en los datos JSON (compatible con SQLite y PostgreSQL)
            contexts = session.query(ProjectContext).filter(
                ProjectContext.context_data.cast(String).ilike(f"%{query}%")
            ).order_by(ProjectContext.last_accessed.desc()).limit(limit).all()
            
            results = []
            for ctx in contexts:
                results.append({
                    "project_name": ctx.project_name,
                    "type": ctx.context_type,
                    "file_path": ctx.file_path,
                    "data": ctx.context_data,
                    "relevance_snippet": self._extract_relevant_snippet(ctx.context_data, query),
                    "last_accessed": ctx.last_accessed.isoformat()
                })
            
            session.close()
            return results
            
        except Exception as e:
            print(f"❌ Error buscando contexto de proyecto: {e}")
            if session:
                session.close()
            return []
    
    def _extract_relevant_snippet(self, data: Dict[str, Any], query: str) -> str:
        """Extrae snippet relevante de los datos"""
        try:
            data_str = json.dumps(data, ensure_ascii=False)
            query_lower = query.lower()
            
            # Buscar la posición de la query
            pos = data_str.lower().find(query_lower)
            if pos == -1:
                return str(data)[:100] + "..."
            
            # Extraer contexto alrededor
            start = max(0, pos - 50)
            end = min(len(data_str), pos + len(query) + 50)
            
            snippet = data_str[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(data_str):
                snippet = snippet + "..."
                
            return snippet
            
        except:
            return str(data)[:100] + "..."
    
    def get_project_summary(self, project_name: str) -> Dict[str, Any]:
        """Obtiene un resumen del proyecto"""
        all_context = self.get_project_info(project_name)
        
        summary = {
            "project_name": project_name,
            "context_types": list(set([ctx["type"] for ctx in all_context])),
            "file_count": len([ctx for ctx in all_context if ctx["file_path"]]),
            "last_activity": max([ctx["last_accessed"] for ctx in all_context]) if all_context else None,
            "has_structure": any(ctx["type"] == "file_structure" for ctx in all_context),
            "has_preferences": any(ctx["type"] == "user_preferences" for ctx in all_context)
        }
        
        return summary
    
    def get_context_for_query(self, query: str, project_name: str = None) -> str:
        """Obtiene contexto relevante para una consulta sobre proyectos"""
        if project_name is None:
            project_name = self.current_project
        
        # Buscar información específica del proyecto
        project_info = self.get_project_info(project_name)
        
        # Buscar también en otros proyectos si la consulta lo amerita
        search_results = self.search_project_context(query, limit=5)
        
        if not project_info and not search_results:
            return ""
        
        context_parts = []
        context_parts.append(f"📁 Información del proyecto '{project_name}':")
        
        # Información del proyecto actual
        if project_info:
            for info in project_info:
                context_parts.append(f"   🔧 {info['type']}: {self._summarize_data(info['data'])}")
        
        # Resultados de búsqueda
        if search_results:
            context_parts.append("\n🔍 Información relacionada encontrada:")
            for result in search_results:
                context_parts.append(f"   📂 {result['project_name']} ({result['type']}): {result['relevance_snippet']}")
        
        context_parts.append("---")
        return "\n".join(context_parts)
    
    def _summarize_data(self, data: Dict[str, Any]) -> str:
        """Crea un resumen de los datos"""
        try:
            if isinstance(data, dict):
                if "name" in data:
                    return f"Nombre: {data['name']}"
                elif "files" in data:
                    return f"{len(data['files'])} archivos"
                else:
                    keys = list(data.keys())[:3]
                    return f"Campos: {', '.join(keys)}"
            else:
                return str(data)[:50] + "..." if len(str(data)) > 50 else str(data)
        except:
            return "Datos estructurados" 