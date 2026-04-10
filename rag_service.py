"""RAG (Retrieval-Augmented Generation) service.

Uses OpenAI Responses API with File Search to query indexed documents,
returning answers with structured citations.
"""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from backend import AppConfig
from document_store import DocumentStore

RAG_SYSTEM_PROMPT = """\
당신은 문서 검색 비서입니다.

규칙:
1. 반드시 검색된 문서만 근거로 답변하세요.
2. 근거가 부족하면 "근거 부족"이라고 솔직하게 답하세요.
3. 답변에는 반드시 출처를 포함하세요:
   - 사양서: 문서명, 버전, 절/항목
   - 법규: 법명, 조문, 시행일
   - 메일: 제목, 발신자, 발송 시각
4. 상충되는 문서가 있으면 둘 다 보여주고 차이를 설명하세요.
5. 한국어로 답변하세요.
"""


class RAGService:
    """Handles document-based RAG queries using OpenAI File Search."""

    def __init__(self, config: AppConfig, document_store: DocumentStore | None = None):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key) if config.openai_api_key else None
        self.document_store = document_store or DocumentStore(config)
        self.model = config.openai_model or "gpt-4o-mini"

    def search(
        self,
        query: str,
        source_types: list[str] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search indexed documents and return answer with citations."""
        if not self.client:
            return {"error": "OpenAI API key not configured"}

        vs_ids = self.document_store.get_vector_store_ids(source_types)
        if not vs_ids:
            return {
                "answer": "색인된 문서가 없습니다. 먼저 문서를 업로드해주세요.",
                "citations": [],
                "warnings": ["검색 가능한 문서가 없습니다."],
            }

        try:
            tools = [
                {
                    "type": "file_search",
                    "vector_store_ids": vs_ids,
                    "max_num_results": min(limit, 20),
                }
            ]

            response = self.client.responses.create(
                model=self.model,
                instructions=RAG_SYSTEM_PROMPT,
                input=query,
                tools=tools,
                include=["file_search_call.results"],
                store=False,
            )

            answer = ""
            citations = []
            search_results = []

            for item in response.output:
                if hasattr(item, "type"):
                    if item.type == "message":
                        for content_block in item.content:
                            if hasattr(content_block, "text"):
                                answer = content_block.text
                                if hasattr(content_block, "annotations"):
                                    for ann in content_block.annotations:
                                        if hasattr(ann, "file_citation"):
                                            citations.append({
                                                "file_id": ann.file_citation.file_id if hasattr(ann.file_citation, "file_id") else "",
                                                "quote": ann.file_citation.quote if hasattr(ann.file_citation, "quote") else "",
                                            })
                    elif item.type == "file_search_call":
                        if hasattr(item, "results") and item.results:
                            for result in item.results:
                                search_results.append({
                                    "file_id": result.file_id if hasattr(result, "file_id") else "",
                                    "file_name": result.file_name if hasattr(result, "file_name") else "",
                                    "score": result.score if hasattr(result, "score") else 0,
                                    "text": (result.text[:500] if hasattr(result, "text") and result.text else ""),
                                    "attributes": result.attributes if hasattr(result, "attributes") else {},
                                })

            enriched_citations = self._enrich_citations(citations, search_results)

            warnings = []
            if not search_results:
                warnings.append("검색 결과가 없습니다.")
            if source_types:
                warnings.append(f"검색 범위: {', '.join(source_types)}")

            return {
                "answer": answer,
                "citations": enriched_citations,
                "search_results": search_results[:limit],
                "warnings": warnings,
            }

        except Exception as exc:
            error_str = str(exc)
            if "responses" in error_str.lower() or "not found" in error_str.lower():
                return self._fallback_chat_search(query, vs_ids, limit)
            return {"error": f"RAG 검색 실패: {error_str}"}

    def _fallback_chat_search(
        self, query: str, vs_ids: list[str], limit: int
    ) -> dict[str, Any]:
        """Fallback to Chat Completions if Responses API is not available."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.5,
                max_completion_tokens=2000,
            )

            answer = response.choices[0].message.content or ""
            return {
                "answer": answer,
                "citations": [],
                "search_results": [],
                "warnings": ["Responses API 미지원으로 일반 Chat API로 답변합니다. 문서 검색 결과가 포함되지 않을 수 있습니다."],
            }
        except Exception as exc:
            return {"error": f"Fallback 검색 실패: {str(exc)}"}

    def _enrich_citations(
        self,
        citations: list[dict[str, Any]],
        search_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enrich citation data with document metadata from search results."""
        file_id_to_result = {}
        for sr in search_results:
            fid = sr.get("file_id", "")
            if fid:
                file_id_to_result[fid] = sr

        enriched = []
        seen_file_ids = set()
        for c in citations:
            fid = c.get("file_id", "")
            if fid in seen_file_ids:
                continue
            seen_file_ids.add(fid)

            sr = file_id_to_result.get(fid, {})
            attrs = sr.get("attributes", {})

            enriched.append({
                "file_id": fid,
                "file_name": sr.get("file_name", ""),
                "quote": c.get("quote", ""),
                "score": sr.get("score", 0),
                "source_type": attrs.get("source_type", ""),
                "title": attrs.get("title", sr.get("file_name", "")),
                "version": attrs.get("version", ""),
                "effective_from": attrs.get("effective_from", ""),
                "department": attrs.get("department", ""),
            })

        if not enriched:
            for sr in search_results[:3]:
                attrs = sr.get("attributes", {})
                enriched.append({
                    "file_id": sr.get("file_id", ""),
                    "file_name": sr.get("file_name", ""),
                    "quote": sr.get("text", "")[:200],
                    "score": sr.get("score", 0),
                    "source_type": attrs.get("source_type", ""),
                    "title": attrs.get("title", sr.get("file_name", "")),
                    "version": attrs.get("version", ""),
                    "effective_from": attrs.get("effective_from", ""),
                    "department": attrs.get("department", ""),
                })

        return enriched

    def list_documents(
        self, source_type: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Proxy to DocumentStore.list_documents."""
        return self.document_store.list_documents(source_type=source_type, limit=limit)
