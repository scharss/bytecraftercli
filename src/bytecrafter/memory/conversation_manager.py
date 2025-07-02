"""
Gestor de conversaciones para memoria persistente
"""

import uuid
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from .database import get_session, Conversation, Message

class ConversationManager:
    """Gestiona conversaciones persistentes y recuperación de memoria"""
    
    def __init__(self):
        self.current_session_id = str(uuid.uuid4())
        self.current_conversation_id = None
        
    def start_new_conversation(self, title: str = None, user_id: str = "default_user") -> Optional[int]:
        """Inicia una nueva conversación"""
        session = get_session()
        if session is None:
            return None
        
        try:
            conversation = Conversation(
                session_id=self.current_session_id,
                user_id=user_id,
                title=title or f"Conversación {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                status="active"
            )
            
            session.add(conversation)
            session.commit()
            
            self.current_conversation_id = conversation.id
            
            session.close()
            return conversation.id
            
        except Exception as e:
            print(f"❌ Error creando conversación: {e}")
            if session:
                session.rollback()
                session.close()
            return None
    
    def save_message(self, role: str, content: str, tool_name: str = None, 
                    tool_params: Dict = None, tool_result: str = None) -> bool:
        """Guarda un mensaje en la conversación actual"""
        if self.current_conversation_id is None:
            self.start_new_conversation()
        
        session = get_session()
        if session is None:
            return False
        
        try:
            # Obtener el orden del próximo mensaje
            last_message = session.query(Message).filter(
                Message.conversation_id == self.current_conversation_id
            ).order_by(Message.message_order.desc()).first()
            
            next_order = 1 if last_message is None else last_message.message_order + 1
            
            message = Message(
                conversation_id=self.current_conversation_id,
                role=role,
                content=content,
                tool_name=tool_name,
                tool_params=tool_params,
                tool_result=tool_result,
                message_order=next_order
            )
            
            session.add(message)
            session.commit()
            session.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error guardando mensaje: {e}")
            if session:
                session.rollback()
                session.close()
            return False
    
    def get_conversation_history(self, conversation_id: int = None, 
                               limit: int = 50) -> List[Dict[str, Any]]:
        """Recupera el historial de una conversación"""
        if conversation_id is None:
            conversation_id = self.current_conversation_id
        
        if conversation_id is None:
            return []
        
        session = get_session()
        if session is None:
            return []
        
        try:
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.message_order).limit(limit).all()
            
            history = []
            for msg in messages:
                # Limpiar mensajes de tool_result para que Gemini no se confunda
                cleaned_content = self._clean_tool_result_for_gemini(msg.content)
                
                # Solo incluir campos que Gemini acepta - NO metadatos de herramientas
                message_data = {
                    "role": msg.role,
                    "parts": [{"text": cleaned_content}]
                }
                
                # Los metadatos (tool_name, tool_params, tool_result) solo se usan para BD
                # NO se envían a Gemini
                
                history.append(message_data)
            
            session.close()
            return history
            
        except Exception as e:
            print(f"❌ Error recuperando historial: {e}")
            if session:
                session.close()
            return []
    
    def search_conversations(self, query: str, user_id: str = "default_user", 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Busca conversaciones por contenido"""
        session = get_session()
        if session is None:
            return []
        
        try:
            # Buscar en mensajes que contengan la query
            conversations = session.query(Conversation).join(Message).filter(
                Conversation.user_id == user_id,
                Message.content.ilike(f"%{query}%")
            ).distinct().order_by(Conversation.updated_at.desc()).limit(limit).all()
            
            results = []
            for conv in conversations:
                # Obtener snippet relevante
                relevant_message = session.query(Message).filter(
                    Message.conversation_id == conv.id,
                    Message.content.ilike(f"%{query}%")
                ).first()
                
                results.append({
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "snippet": relevant_message.content[:200] + "..." if relevant_message else "",
                    "status": conv.status
                })
            
            session.close()
            return results
            
        except Exception as e:
            print(f"❌ Error buscando conversaciones: {e}")
            if session:
                session.close()
            return []
    
    def get_recent_conversations(self, user_id: str = "default_user", 
                               limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene conversaciones recientes"""
        session = get_session()
        if session is None:
            return []
        
        try:
            conversations = session.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.status == "active"
            ).order_by(Conversation.updated_at.desc()).limit(limit).all()
            
            results = []
            for conv in conversations:
                # Contar mensajes
                message_count = session.query(Message).filter(
                    Message.conversation_id == conv.id
                ).count()
                
                results.append({
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": message_count,
                    "status": conv.status
                })
            
            session.close()
            return results
            
        except Exception as e:
            print(f"❌ Error obteniendo conversaciones recientes: {e}")
            if session:
                session.close()
            return []
    
    def complete_conversation(self, summary: str = None) -> bool:
        """Marca la conversación actual como completada"""
        if self.current_conversation_id is None:
            return False
        
        session = get_session()
        if session is None:
            return False
        
        try:
            conversation = session.query(Conversation).filter(
                Conversation.id == self.current_conversation_id
            ).first()
            
            if conversation:
                conversation.status = "completed"
                if summary:
                    conversation.summary = summary
                session.commit()
            
            session.close()
            return True
            
        except Exception as e:
            print(f"❌ Error completando conversación: {e}")
            if session:
                session.rollback()
                session.close()
            return False
    
    def get_context_for_query(self, query: str, user_id: str = "default_user") -> str:
        """Obtiene contexto relevante para una consulta"""
        # Buscar conversaciones relacionadas
        related_conversations = self.search_conversations(query, user_id, limit=3)
        
        if not related_conversations:
            return ""
        
        context_parts = []
        context_parts.append("📚 Información de conversaciones anteriores:")
        
        for conv in related_conversations:
            context_parts.append(f"\n🗂️ {conv['title']} ({conv['updated_at'][:10]}):")
            context_parts.append(f"   {conv['snippet']}")
        
        context_parts.append("\n---")
        return "\n".join(context_parts)
    
    def _clean_tool_result_for_gemini(self, content: str) -> str:
        """Limpia mensajes de tool_result para que Gemini no se confunda con el XML"""
        # Detectar si es un mensaje de tool_result
        if "<tool_result>" in content and "</tool_result>" in content:
            try:
                # Extraer tool_name y result del XML
                tool_name_match = re.search(r'<tool_name>(.*?)</tool_name>', content)
                result_match = re.search(r'<result>(.*?)</result>', content, re.DOTALL)
                error_match = re.search(r'<error>(.*?)</error>', content, re.DOTALL)
                
                if tool_name_match:
                    tool_name = tool_name_match.group(1)
                    
                    if result_match:
                        result = result_match.group(1)
                        return f"Tool: {tool_name}\nResult: {result}"
                    elif error_match:
                        error = error_match.group(1)
                        return f"Tool: {tool_name}\nError: {error}"
                
                # Si no se puede parsear, devolver el contenido original
                return content
            except:
                return content
        
        # Si no es tool_result, devolver tal como está
        return content

    def convert_to_gemini_format(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convierte historial de BD al formato esperado por Gemini"""
        gemini_history = []
        
        for msg in history:
            # Solo enviar campos que Gemini reconoce
            gemini_msg = {
                "role": msg["role"],
                "parts": msg["parts"]
            }
            # NO incluir tool_name, tool_params, tool_result - solo son para BD
            gemini_history.append(gemini_msg)
        
        return gemini_history 