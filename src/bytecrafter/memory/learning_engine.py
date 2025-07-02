"""
Motor de aprendizaje para memoria persistente
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

from .database import get_session, LearningMemory

class LearningEngine:
    """Motor de aprendizaje que recuerda patrones y soluciones"""
    
    def __init__(self):
        pass
    
    def learn_pattern(self, category: str, pattern: str, data: Dict[str, Any], 
                     confidence: float = 1.0) -> bool:
        """Aprende un patrón nuevo o refuerza uno existente"""
        session = get_session()
        if session is None:
            return False
        
        try:
            # Buscar si ya existe
            existing = session.query(LearningMemory).filter(
                LearningMemory.category == category,
                LearningMemory.key_pattern == pattern
            ).first()
            
            if existing:
                # Reforzar aprendizaje existente
                existing.usage_count += 1
                existing.confidence_score = min(1.0, existing.confidence_score + 0.1)
                existing.last_used = datetime.now(timezone.utc)
                
                # Combinar datos si es útil
                if "examples" in existing.learned_data:
                    if "examples" in data:
                        existing.learned_data["examples"].extend(data["examples"])
                        # Mantener solo los últimos 10 ejemplos
                        existing.learned_data["examples"] = existing.learned_data["examples"][-10:]
                else:
                    existing.learned_data.update(data)
            else:
                # Crear nuevo aprendizaje
                learning = LearningMemory(
                    category=category,
                    key_pattern=pattern,
                    learned_data=data,
                    confidence_score=confidence
                )
                session.add(learning)
            
            session.commit()
            session.close()
            return True
            
        except Exception as e:
            print(f"❌ Error aprendiendo patrón: {e}")
            if session:
                session.rollback()
                session.close()
            return False
    
    def get_learned_pattern(self, category: str, pattern: str) -> Optional[Dict[str, Any]]:
        """Obtiene un patrón aprendido específico"""
        session = get_session()
        if session is None:
            return None
        
        try:
            learning = session.query(LearningMemory).filter(
                LearningMemory.category == category,
                LearningMemory.key_pattern == pattern
            ).first()
            
            if learning:
                # Actualizar último uso
                learning.last_used = datetime.now(timezone.utc)
                session.commit()
                
                result = {
                    "pattern": learning.key_pattern,
                    "data": learning.learned_data,
                    "confidence": learning.confidence_score,
                    "usage_count": learning.usage_count,
                    "last_used": learning.last_used.isoformat()
                }
                
                session.close()
                return result
            
            session.close()
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo patrón: {e}")
            if session:
                session.close()
            return None
    
    def search_similar_patterns(self, category: str, query: str, 
                               limit: int = 5) -> List[Dict[str, Any]]:
        """Busca patrones similares en una categoría"""
        session = get_session()
        if session is None:
            return []
        
        try:
            # Buscar patrones que contengan la query
            learnings = session.query(LearningMemory).filter(
                LearningMemory.category == category,
                LearningMemory.key_pattern.ilike(f"%{query}%")
            ).order_by(
                LearningMemory.confidence_score.desc(),
                LearningMemory.usage_count.desc()
            ).limit(limit).all()
            
            results = []
            for learning in learnings:
                results.append({
                    "pattern": learning.key_pattern,
                    "data": learning.learned_data,
                    "confidence": learning.confidence_score,
                    "usage_count": learning.usage_count,
                    "last_used": learning.last_used.isoformat()
                })
            
            session.close()
            return results
            
        except Exception as e:
            print(f"❌ Error buscando patrones: {e}")
            if session:
                session.close()
            return []
    
    def learn_file_encoding_solution(self, filename: str, encoding: str, 
                                   solution: str, success: bool = True) -> bool:
        """Aprende soluciones de encoding de archivos"""
        pattern = self._extract_file_pattern(filename)
        
        data = {
            "encoding": encoding,
            "solution": solution,
            "success": success,
            "examples": [{"filename": filename, "encoding": encoding}]
        }
        
        confidence = 0.9 if success else 0.3
        return self.learn_pattern("file_encoding", pattern, data, confidence)
    
    def get_file_encoding_suggestion(self, filename: str) -> Optional[Dict[str, Any]]:
        """Obtiene sugerencia de encoding para un archivo"""
        pattern = self._extract_file_pattern(filename)
        return self.get_learned_pattern("file_encoding", pattern)
    
    def learn_error_solution(self, error_type: str, error_message: str, 
                           solution: str, context: Dict[str, Any] = None) -> bool:
        """Aprende solución a un error específico"""
        pattern = f"{error_type}:{error_message[:100]}"
        
        data = {
            "error_type": error_type,
            "error_message": error_message,
            "solution": solution,
            "context": context or {},
            "examples": [{"error": error_message, "solution": solution}]
        }
        
        return self.learn_pattern("error_solution", pattern, data)
    
    def get_error_solution(self, error_type: str, error_message: str) -> Optional[Dict[str, Any]]:
        """Obtiene solución para un error"""
        # Buscar patrón exacto primero
        pattern = f"{error_type}:{error_message[:100]}"
        exact_match = self.get_learned_pattern("error_solution", pattern)
        
        if exact_match:
            return exact_match
        
        # Buscar patrones similares
        similar = self.search_similar_patterns("error_solution", error_type, limit=3)
        return similar[0] if similar else None
    
    def learn_user_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]) -> bool:
        """Aprende patrones de comportamiento del usuario"""
        pattern_key = f"{pattern_type}:{pattern_data.get('key', 'general')}"
        
        return self.learn_pattern("user_pattern", pattern_key, pattern_data)
    
    def get_user_patterns(self, pattern_type: str = None) -> List[Dict[str, Any]]:
        """Obtiene patrones de comportamiento del usuario"""
        if pattern_type:
            query = f"{pattern_type}:"
            return self.search_similar_patterns("user_pattern", query, limit=10)
        else:
            session = get_session()
            if session is None:
                return []
            
            try:
                learnings = session.query(LearningMemory).filter(
                    LearningMemory.category == "user_pattern"
                ).order_by(LearningMemory.usage_count.desc()).limit(20).all()
                
                results = []
                for learning in learnings:
                    results.append({
                        "pattern": learning.key_pattern,
                        "data": learning.learned_data,
                        "confidence": learning.confidence_score,
                        "usage_count": learning.usage_count
                    })
                
                session.close()
                return results
                
            except Exception as e:
                print(f"❌ Error obteniendo patrones de usuario: {e}")
                if session:
                    session.close()
                return []
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de todo lo aprendido"""
        session = get_session()
        if session is None:
            return {}
        
        try:
            # Estadísticas por categoría
            categories = session.query(
                LearningMemory.category,
                session.query(LearningMemory.id).filter(
                    LearningMemory.category == LearningMemory.category
                ).count().label('count')
            ).group_by(LearningMemory.category).all()
            
            # Top patrones más usados
            top_patterns = session.query(LearningMemory).order_by(
                LearningMemory.usage_count.desc()
            ).limit(10).all()
            
            summary = {
                "total_patterns": session.query(LearningMemory).count(),
                "categories": {cat.category: cat.count for cat in categories},
                "top_patterns": [
                    {
                        "category": p.category,
                        "pattern": p.key_pattern,
                        "usage_count": p.usage_count,
                        "confidence": p.confidence_score
                    }
                    for p in top_patterns
                ]
            }
            
            session.close()
            return summary
            
        except Exception as e:
            print(f"❌ Error obteniendo resumen de aprendizaje: {e}")
            if session:
                session.close()
            return {}
    
    def get_context_for_query(self, query: str, category: str = None) -> str:
        """Obtiene contexto de aprendizajes relevantes para una consulta"""
        if category:
            patterns = self.search_similar_patterns(category, query, limit=3)
        else:
            # Buscar en todas las categorías
            all_patterns = []
            for cat in ["file_encoding", "error_solution", "user_pattern"]:
                cat_patterns = self.search_similar_patterns(cat, query, limit=2)
                all_patterns.extend(cat_patterns)
            
            # Ordenar por confianza y uso
            patterns = sorted(all_patterns, 
                            key=lambda x: (x["confidence"], x["usage_count"]), 
                            reverse=True)[:5]
        
        if not patterns:
            return ""
        
        context_parts = []
        context_parts.append("🧠 Aprendizajes relevantes:")
        
        for pattern in patterns:
            usage_info = f"({pattern['usage_count']} usos, {pattern['confidence']:.1f} confianza)"
            context_parts.append(f"   🔹 {pattern['pattern']} {usage_info}")
            
            # Agregar información útil del aprendizaje
            if "solution" in pattern["data"]:
                context_parts.append(f"      Solución: {pattern['data']['solution'][:100]}...")
            elif "encoding" in pattern["data"]:
                context_parts.append(f"      Encoding: {pattern['data']['encoding']}")
        
        context_parts.append("---")
        return "\n".join(context_parts)
    
    def _extract_file_pattern(self, filename: str) -> str:
        """Extrae patrón de un nombre de archivo"""
        import os
        
        # Obtener extensión
        _, ext = os.path.splitext(filename.lower())
        
        # Patrones comunes
        if ext in ['.txt', '.md', '.log']:
            return f"text_file{ext}"
        elif ext in ['.py', '.js', '.html', '.css']:
            return f"code_file{ext}"
        elif ext in ['.pdf', '.doc', '.docx']:
            return f"document{ext}"
        elif ext in ['.jpg', '.png', '.gif']:
            return f"image{ext}"
        else:
            return f"unknown{ext}" if ext else "no_extension" 