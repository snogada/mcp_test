import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# FastMCP를 사용하여 간단한 MCP 서버 인스턴스 생성
mcp = FastMCP("Equipment_and_AI_Server")

@mcp.tool()
def get_equipment_status(equipment_name: str) -> str:
    """
    주어진 설비명(equipment_name)의 현재 온도와 압력 상태를 반환합니다.
    """
    # 하드코딩된 테스트 값: 온도 10도, 압력 10atm
    temperature = 10.0
    pressure = 10.0
    
    return f"[{equipment_name} 상태] 온도: {temperature}°C, 압력: {pressure}atm"

if __name__ == "__main__":
    # 서버 실행 (표준 입출력을 통해 호스트와 통신)
    print("MCP Equipment & AI Server가 시작되었습니다. (이 메시지는 디버그용이며, MCP는 stdio를 사용합니다)", flush=True)
    mcp.run()
