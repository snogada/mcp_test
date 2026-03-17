# 시스템 요약 & 구조도

## 📁 구성 파일

| 파일 | 역할 | 제공 도구 |
|---|---|---|
| `server.py` | 설비 상태 MCP 서버 | `get_equipment_status` |
| `user_server.py` | 사용자별 설비 목록 MCP 서버 | `get_user_equipment` |
| `registry_server.py` | MCP 서버 레지스트리 | `get_all_mcp_servers`, `get_mcp_server_info` |
| `langchain_agent.py` | LangChain/LangGraph 에이전트 | - |

---

## 🗺️ 아키텍처 구조도

```mermaid
graph TD
    User(["👤 사용자\n질의 입력"])

    subgraph Agent["LangChain Agent (langchain_agent.py)"]
        P1["Phase 1\n레지스트리 조회\n(registry_server)"]
        LLM["LLM\nGemini-2.5-Flash\n필요 서버 선택"]
        P2["Phase 2\n필요 서버에 동적 연결\n도구 추가 등록"]
        Exec["Agent 실행\n(registry 도구 + 선택 도구)"]
    end

    subgraph MCPServers["MCP Servers (stdio)"]
        RS["registry_server.py\n📋 get_all_mcp_servers\n🔍 get_mcp_server_info"]
        US["user_server.py\n👤 get_user_equipment"]
        ES["server.py\n🌡️ get_equipment_status"]
    end

    Config["claude_desktop_config.json\nMCP 서버 등록 정보"]

    User --> P1
    P1 -->|"1. 서버 목록 조회"| RS
    RS -->|"2. 서버 목록 반환"| P1
    Config -.->|서버 경로 참조| RS
    P1 -->|"3. 서버목록 + 질의"| LLM
    LLM -->|"4. 필요 서버 선택\n(JSON 배열)"| P2
    P2 -->|"5. 동적 연결 & 도구 등록"| US
    P2 -->|"5. 동적 연결 & 도구 등록"| ES
    P2 --> Exec
    Exec -->|"6. 도구 호출 (자동)"| US
    Exec -->|"6. 도구 호출 (자동)"| ES
    Exec -->|"7. 최종 답변"| User

    style Agent fill:#e8f4fd,stroke:#1565c0,stroke-width:2px
    style MCPServers fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    style RS fill:#fff3e0,stroke:#e65100
    style US fill:#fff3e0,stroke:#e65100
    style ES fill:#fff3e0,stroke:#e65100
    style LLM fill:#f3e5f5,stroke:#6a1b9a
    style Config fill:#f5f5f5,stroke:#757575
```

---

## 🔄 동작 흐름 요약

1. **질의 입력** → 에이전트 시작
2. **Phase 1** → `registry_server`에 연결, 등록된 MCP 서버 전체 목록 획득
3. **서버 선택** → LLM에 질의 + 서버 목록 전달, 필요한 서버를 JSON으로 응답 받음
4. **Phase 2** → 선택된 서버에 동적 연결, 도구 자동 등록 (stdio 기반)
5. **에이전트 실행** → 전체 도구(registry + 동적 추가)로 최종 질의 처리
6. **최종 응답** 출력
