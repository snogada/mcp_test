import os
import json
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# FastMCP를 사용하여 서버 인스턴스 생성
mcp = FastMCP("MCP_Registry_Server")

# Claude Desktop 설정 파일 경로
CLAUDE_CONFIG_PATH = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Roaming", "Claude", "claude_desktop_config.json"
)

@mcp.tool()
def get_all_mcp_servers() -> str:
    """
    Claude Desktop에 현재 등록된 모든 MCP 서버 목록과 실행 명령어 정보를 반환합니다.
    """
    if not os.path.exists(CLAUDE_CONFIG_PATH):
        return f"설정 파일을 찾을 수 없습니다: {CLAUDE_CONFIG_PATH}"
    
    try:
        with open(CLAUDE_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        mcp_servers = config.get("mcpServers", {})
        
        if not mcp_servers:
            return "현재 등록된 MCP 서버가 없습니다."
        
        result_lines = [f"📋 등록된 MCP 서버 목록 (총 {len(mcp_servers)}개):"]
        result_lines.append("=" * 50)
        
        for idx, (name, info) in enumerate(mcp_servers.items(), start=1):
            command = info.get("command", "N/A")
            args = " ".join(info.get("args", []))
            result_lines.append(f"{idx}. 서버명: {name}")
            result_lines.append(f"   실행 명령어: {command} {args}")
            result_lines.append("")
        
        return "\n".join(result_lines).strip()
    
    except json.JSONDecodeError as e:
        return f"설정 파일 JSON 파싱 오류: {str(e)}"
    except Exception as e:
        return f"오류 발생: {str(e)}"


@mcp.tool()
def get_mcp_server_info(server_name: str) -> str:
    """
    특정 MCP 서버 이름(server_name)의 상세 설정 정보를 반환합니다.
    """
    if not os.path.exists(CLAUDE_CONFIG_PATH):
        return f"설정 파일을 찾을 수 없습니다: {CLAUDE_CONFIG_PATH}"
    
    try:
        with open(CLAUDE_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        mcp_servers = config.get("mcpServers", {})
        
        if server_name not in mcp_servers:
            available = ", ".join(mcp_servers.keys())
            return f"'{server_name}' 서버를 찾을 수 없습니다.\n사용 가능한 서버: {available}"
        
        info = mcp_servers[server_name]
        command = info.get("command", "N/A")
        args = info.get("args", [])
        env = info.get("env", {})
        
        result_lines = [
            f"🔍 '{server_name}' 서버 상세 정보:",
            f"  실행 명령어: {command}",
            f"  인자(args): {' '.join(args) if args else '없음'}",
            f"  환경변수: {json.dumps(env, ensure_ascii=False) if env else '없음'}",
        ]
        
        return "\n".join(result_lines)
    
    except Exception as e:
        return f"오류 발생: {str(e)}"


if __name__ == "__main__":
    mcp.run()
