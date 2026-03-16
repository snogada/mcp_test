import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# .env 파일에서 환경 변수 로드
load_dotenv()

async def call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Gemini API를 호출하여 응답을 받아오는 함수"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "오류: GEMINI_API_KEY가 설정되지 않았습니다."

    # Gemini API 엔드포인트 수정 (현재 권장 방식: models/gemini-2.0-flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f"{system_prompt}\n\n사용자 요청: {user_prompt}"}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            return f"Gemini API 호출 중 오류 발생: {str(e)}"

async def main():
    # Windows 콘솔에서 유니코드(이모지 등) 출력 오류 방지
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("🚀 테스트 에이전트 시작...")
    
    # MCP 서버 환경변수에 UTF-8 인코딩 강제
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # 1. 실행할 MCP 서버 설정 (python server.py)
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"], # 현재 디렉토리의 server.py 실행
        env=env
    )

    print("🔌 MCP 서버(server.py) 프로세스 시작 및 연결 중...")
    
    # 2. stdio_client를 사용하여 서버와 통신 채널 열기
    async with stdio_client(server_params) as (read_stream, write_stream):
        # 3. ClientSession을 통해 초기화 및 통신 시작
        async with ClientSession(read_stream, write_stream) as session:
            # 필수: 서버 초기화 프로토콜 핸드셰이크
            await session.initialize()
            print("✅ MCP 서버 연결 및 초기화 완료!\n")
            
            # --- [Tool 호출 테스트] ---
            equipment_name = "메인 냉각수 펌프"
            print(f"🛠️ [MCP 도구 호출] get_equipment_status('{equipment_name}')")
            
            # MCP 프로토콜을 이용해 도구(Tool) 호출
            result = await session.call_tool(
                name="get_equipment_status",
                arguments={"equipment_name": equipment_name}
            )
            
            # 결과 텍스트 추출 (결과는 리스트 형태로 옴)
            status_text = result.content[0].text
            print(f"📥 [서버 응답]: {status_text}\n")
            
            # --- [Gemini AI 통신] ---
            print("🧠 [Gemini AI] 서버에서 받은 상태를 기반으로 분석 요청 중...")
            
            system_prompt = (
                "당신은 공장 설비 관리 전문가 AI입니다. "
                "사용자가 설비의 센서 데이터(상태)를 주면, 해당 데이터가 의미하는 바와 "
                "간단한 조치사항(혹은 이상이 없다는 확인)을 2문장 이내로 짧게 답변해주세요."
            )
            user_prompt = f"다음 설비 상태를 확인해줘: {status_text}"
            
            ai_response = await call_gemini(system_prompt, user_prompt)
            print(f"💡 [AI 전문가의 조언]:\n{ai_response}\n")

if __name__ == "__main__":
    asyncio.run(main())
