import os
import asyncio
import sys
import json
from typing import Any
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LangChain 및 LangGraph 임포트
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

# 1. 환경 변수 로드
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")

# 2. Gemini 모델 초기화
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    api_key=api_key
)

# ─────────────────────────────────────────────────────────────────────
# Helper: MCP 세션 하나에 있는 모든 도구를 LangChain StructuredTool로 변환
# ─────────────────────────────────────────────────────────────────────
def _make_tool(session: ClientSession, tool_info: Any) -> StructuredTool:
    """MCP tool 메타데이터를 LangChain StructuredTool로 래핑합니다."""
    tool_name = tool_info.name
    tool_desc = tool_info.description or f"{tool_name} 도구"

    # 입력 스키마를 파악하여 pydantic 없이 generic kwargs로 처리
    async def _call(**kwargs) -> str:
        print(f"\n  [Agent → MCP:{tool_name}] 인자={kwargs}")
        result = await session.call_tool(name=tool_name, arguments=kwargs)
        return result.content[0].text if result.content else ""

    # StructuredTool은 args_schema가 없으면 **kwargs 기반으로 동작
    wrapped = StructuredTool.from_function(
        name=tool_name,
        description=tool_desc,
        func=_call,
        coroutine=_call,
    )
    return wrapped


# ─────────────────────────────────────────────────────────────────────
# Phase 1: registry_server에 연결, 서버 목록 + 선택 도구만 확보
# ─────────────────────────────────────────────────────────────────────
async def phase1_get_registry(env: dict) -> tuple[list[StructuredTool], str, dict]:
    """
    registry_server 에 연결하여
    - get_all_mcp_servers / get_mcp_server_info 도구를 래핑
    - get_all_mcp_servers 를 직접 호출해 현재 서버 목록 텍스트 획득
    - claude_desktop_config.json 내용을 반환 (Phase 2 연결용)
    """
    server_params = StdioServerParameters(
        command="python",
        args=["registry_server.py"],
        env=env
    )

    print("🔌 [Phase 1] registry_server 에 연결 중...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ [Phase 1] registry_server 연결 완료\n")

            # 도구 목록 조회
            tools_response = await session.list_tools()
            registry_tools = [_make_tool(session, t) for t in tools_response.tools]

            # 서버 목록 텍스트 획득
            all_servers_raw = await session.call_tool(
                name="get_all_mcp_servers", arguments={}
            )
            server_list_text = all_servers_raw.content[0].text if all_servers_raw.content else ""

            # 설정 파일에서 서버 맵 읽기
            config_path = os.path.join(
                os.path.expanduser("~"),
                "AppData", "Roaming", "Claude", "claude_desktop_config.json"
            )
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            server_map = config.get("mcpServers", {})

    print(f"\n📋 [Phase 1] 현재 등록된 MCP 서버 목록:\n{server_list_text}\n")
    return registry_tools, server_list_text, server_map


# ─────────────────────────────────────────────────────────────────────
# Phase 2: LLM 에게 필요한 서버를 골라 달라고 한 뒤 해당 서버에 연결
# ─────────────────────────────────────────────────────────────────────
async def phase2_select_and_connect(
    user_query: str,
    server_list_text: str,
    server_map: dict,
    env: dict
) -> list[StructuredTool]:
    """
    LLM 이 user_query 를 보고 필요한 서버 이름을 JSON 배열로 응답하면,
    그 서버들에 연결하여 도구를 수집해 반환합니다. (단, registry 서버 자체는 제외)
    """
    # LLM 에게 필요한 서버 선택을 요청
    selection_prompt = f"""아래는 현재 시스템에 등록된 MCP 서버 목록입니다.

{server_list_text}

사용자 질의: "{user_query}"

위 질의를 처리하는 데 필요한 MCP 서버 이름을 JSON 배열로만 답하세요.
예) ["user_equipment_server"]
registry 서버(mcp_registry_server)는 이미 조회에 사용했으므로 선택하지 마세요."""

    resp = await llm.ainvoke(selection_prompt)
    raw = resp.content.strip()
    # 마크다운 코드블록 제거
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    try:
        selected_servers = json.loads(raw)
    except json.JSONDecodeError:
        print(f"⚠️  서버 선택 응답 파싱 실패: {raw!r} → 빈 목록 사용")
        selected_servers = []

    print(f"🤖 [Phase 2] LLM 선택 서버: {selected_servers}")

    collected_tools: list[StructuredTool] = []
    for server_name in selected_servers:
        if server_name not in server_map:
            print(f"  ⚠️  '{server_name}' 를 server_map에서 찾지 못했습니다.")
            continue

        info = server_map[server_name]
        cmd = info.get("command", "python")
        args = info.get("args", [])

        print(f"  🔌 [{server_name}] 에 연결 중...")
        params = StdioServerParameters(command=cmd, args=args, env=env)

        # 컨텍스트 매니저를 스택에 쌓아 생명주기 유지 (세션 참조 반환)
        read_ctx = stdio_client(params)
        read_write = await read_ctx.__aenter__()
        read_stream, write_stream = read_write
        session_ctx = ClientSession(read_stream, write_stream)
        sess = await session_ctx.__aenter__()
        await sess.initialize()
        print(f"  ✅ [{server_name}] 연결 완료")

        tools_resp = await sess.list_tools()
        for t in tools_resp.tools:
            tool = _make_tool(sess, t)
            collected_tools.append(tool)
            print(f"    · 등록된 도구: {t.name}")

    return collected_tools


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────
async def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print("🚀 LangChain 동적 에이전트 시작...\n")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # ── Phase 1: registry 서버로부터 전체 서버 목록 파악 ──
    registry_tools, server_list_text, server_map = await phase1_get_registry(env)

    # ── 사용자 질의 목록 ──
    queries = [
        "Alice가 관리하는 설비 리스트를 알려주세요.",
        "Bob은 어떤 설비들을 가지고 있나요?",
    ]

    for query in queries:
        print(f"\n{'='*50}")
        print(f"👤 사용자: {query}")
        print(f"{'='*50}")

        # ── Phase 2: LLM이 필요한 서버 선택 → 추가 도구 확보 ──
        extra_tools = await phase2_select_and_connect(
            user_query=query,
            server_list_text=server_list_text,
            server_map=server_map,
            env=env
        )

        # registry 도구 + 동적으로 추가된 도구를 합쳐 에이전트 구성
        all_tools = registry_tools + extra_tools
        print(f"\n🛠️  최종 등록된 도구: {[t.name for t in all_tools]}")

        agent = create_react_agent(llm, all_tools)
        response = await agent.ainvoke({"messages": [("user", query)]})
        final_answer = response["messages"][-1].content
        print(f"\n🤖 LLM 최종 응답: {final_answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
