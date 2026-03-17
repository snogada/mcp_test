import os
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# FastMCP를 사용하여 간단한 MCP 서버 인스턴스 생성
mcp = FastMCP("User_Equipment_Server")

# 가상의 사용자별 설비 데이터베이스
USER_EQUIPMENT_DB = {
    "alice": ["Pump A", "Motor B", "Conveyor C"],
    "bob": ["Valve D", "Sensor E"],
    "charlie": ["Generator F", "Compressor G", "Cooler H", "Heater I"]
}

@mcp.tool()
def get_user_equipment(user_name: str) -> str:
    """
    주어진 사용자 이름(user_name)에 할당된 설비 리스트를 반환합니다.
    """
    user_name_lower = user_name.lower()
    
    if user_name_lower in USER_EQUIPMENT_DB:
        equipment_list = ", ".join(USER_EQUIPMENT_DB[user_name_lower])
        return f"[{user_name}의 설비 리스트]: {equipment_list}"
    else:
        return f"[{user_name}] 사용자를 찾을 수 없거나 등록된 설비가 없습니다."

if __name__ == "__main__":
    # 서버 실행 (표준 입출력을 통해 호스트와 통신)
    mcp.run()
