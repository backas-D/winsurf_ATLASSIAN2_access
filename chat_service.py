from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from backend import AppConfig, find_confluence_pages, find_jira_issues


class ChatService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model or "gpt-4o-mini"
        self.conversation_history: list[dict[str, str]] = []
    
    def process_message(self, user_message: str) -> dict[str, Any]:
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        system_prompt = self._build_system_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=2000
            )
            
            assistant_message = response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            intent = self._analyze_intent(user_message)
            result = self._execute_action(intent, user_message)
            
            return {
                "success": True,
                "message": assistant_message,
                "intent": intent,
                "action_result": result,
                "conversation_id": len(self.conversation_history)
            }
            
        except Exception as e:
            error_msg = str(e)
            
            if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                intent = self._analyze_intent(user_message)
                result = self._execute_action(intent, user_message)
                
                if result and result.get("type") in ["jira_issues", "confluence_pages"]:
                    mock_message = f"요청하신 작업을 수행했습니다. 아래 결과를 확인하세요."
                else:
                    mock_message = f"'{user_message}' 요청을 받았습니다. 프로젝트 Key나 스페이스 이름을 포함해서 다시 요청해주세요."
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": mock_message
                })
                
                return {
                    "success": True,
                    "message": mock_message + "\n\n⚠️ (OpenAI API 할당량 초과로 간단한 응답을 제공합니다)",
                    "intent": intent,
                    "action_result": result,
                    "conversation_id": len(self.conversation_history)
                }
            
            return {
                "success": False,
                "message": f"오류가 발생했습니다: {error_msg}\n\n💡 OpenAI API 키와 할당량을 확인해주세요.",
                "intent": "error",
                "action_result": None
            }
    
    def _build_system_prompt(self) -> str:
        return """당신은 Atlassian 제품(Jira, Confluence)을 도와주는 AI 어시스턴트입니다.

주요 역할:
1. Jira 이슈 검색, 조회, 요약
2. Confluence 페이지 검색, 조회, 요약
3. 사용자 요청을 분석하여 적절한 작업 수행

사용 가능한 작업:
- Jira 이슈 검색: 프로젝트 Key로 이슈 목록 조회
- Jira 이슈 요약: 특정 이슈의 내용 요약
- Confluence 페이지 검색: 프로젝트/스페이스 이름으로 페이지 검색
- Confluence 페이지 요약: 특정 페이지의 내용 요약

응답 형식:
- 간결하고 명확하게 답변
- 필요시 구조화된 정보 제공
- 링크나 상세 정보 포함

제약사항:
- 쓰기 작업(생성, 수정)은 미리보기만 제공
- 실제 반영은 사용자 확인 후에만 수행
"""
    
    def _analyze_intent(self, message: str) -> str:
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["jira", "이슈", "issue", "티켓"]):
            if any(word in message_lower for word in ["찾", "검색", "조회", "보여", "list"]):
                return "jira_search"
            elif any(word in message_lower for word in ["요약", "설명", "내용", "summary"]):
                return "jira_summary"
            else:
                return "jira_general"
        
        elif any(word in message_lower for word in ["confluence", "컨플", "페이지", "문서", "page"]):
            if any(word in message_lower for word in ["찾", "검색", "조회", "보여", "list"]):
                return "confluence_search"
            elif any(word in message_lower for word in ["요약", "설명", "내용", "summary"]):
                return "confluence_summary"
            else:
                return "confluence_general"
        
        else:
            return "general"
    
    def _execute_action(self, intent: str, message: str) -> dict[str, Any] | None:
        try:
            if intent == "jira_search":
                project_key = self._extract_project_key(message)
                if project_key:
                    issues = find_jira_issues(project_key, self.config)
                    return {
                        "type": "jira_issues",
                        "data": issues[:10],
                        "count": len(issues)
                    }
            
            elif intent == "confluence_search":
                project_name = self._extract_project_name(message)
                if project_name:
                    pages = find_confluence_pages(project_name, self.config)
                    return {
                        "type": "confluence_pages",
                        "data": pages[:10],
                        "count": len(pages)
                    }
            
            return None
            
        except Exception as e:
            return {
                "type": "error",
                "message": str(e)
            }
    
    def _extract_project_key(self, message: str) -> str | None:
        import re
        match = re.search(r'\b([A-Z]{2,10})\b', message)
        if match:
            return match.group(1)
        
        words = message.split()
        for word in words:
            if word.isupper() and 2 <= len(word) <= 10:
                return word
        
        return None
    
    def _extract_project_name(self, message: str) -> str | None:
        import re
        
        patterns = [
            r'프로젝트["\s]+([가-힣A-Za-z0-9_-]+)',
            r'스페이스["\s]+([가-힣A-Za-z0-9_-]+)',
            r'([A-Z]{2,10})\s+프로젝트',
            r'([A-Z]{2,10})\s+스페이스',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        
        project_key = self._extract_project_key(message)
        if project_key:
            return project_key
        
        return None
    
    def clear_history(self):
        self.conversation_history = []
    
    def get_history(self) -> list[dict[str, str]]:
        return self.conversation_history
