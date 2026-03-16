# MCP 시스템 구조도 (Architecture Diagram)

구성 요소와 데이터 흐름을 시각화한 구조도입니다.

```mermaid
graph TD
    subgraph "Local Machine (내 컴퓨터)"
        direction TB
        
        Agent[("<b>Agent (MCP Client)</b><br/>agent.py")]
        
        Server[("<b>MCP Server</b><br/>server.py")]
        
        Config["Claude Desktop Config<br/>(Local JSON)"]
        Claude["Claude Desktop App"]
    end

    subgraph "Cloud (외부 API)"
        LLM[("<b>LLM</b><br/>Google Gemini API")]
    end

    %% 데이터 흐름 1: Agent 중심
    Agent -- "1. MCP Protocol (stdio)" --> Server
    Server -- "2. 설비 데이터 반환<br/>(온도: 10, 압력: 10)" --> Agent
    Agent -- "3. 데이터 기반 질문 (Prompt)" --> LLM
    LLM -- "4. 분석 결과/조언 반환" --> Agent

    %% 데이터 흐름 2: Claude Desktop 중심
    Config -. "설정 참조" .-> Server
    Claude -- "대화 시 도구 호출" --> Server
    Server -- "상태 전달" --> Claude
    
    %% 스타일링
    style Agent fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style Server fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style LLM fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style Claude fill:#f1f8e9,stroke:#33691e,stroke-width:1px
```

## 구성 요소 설명

1.  **MCP Server (`server.py`)**: 
    *   **역할**: 실제 설비 데이터(온도, 압력 등)를 제공하는 **데이터 공급자**입니다. 
    *   **특징**: `stdio`(표준 입출력)를 통해 외부와 통신하며, AI가 호출할 수 있는 '도구(Tool)'를 제공합니다.

2.  **Agent (`agent.py`)**: 
    *   **역할**: 전체 과정을 제어하는 **오케스트레이터(MCP Client)**입니다.
    *   **흐름**: MCP 서버에서 데이터를 가져온 후, 이를 LLM(Gemini)에게 전달하여 최종 분석 결과를 받아냅니다.

3.  **LLM (Gemini API)**: 
    *   **역할**: 전달받은 데이터를 해석하고 조언을 제공하는 **지능형 분석기**입니다.

4.  **Claude Desktop**: 
    *   **역할**: 사용자가 직접 대화하며 MCP 서버의 기능을 사용할 수 있는 **UI 클라이언트**입니다.
