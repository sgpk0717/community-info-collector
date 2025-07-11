import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/progress"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket 연결 성공!")
            
            # 테스트 세션 ID
            session_id = "test_session_" + str(int(asyncio.get_event_loop().time()))
            
            # 연결 메시지 전송
            await websocket.send(json.dumps({
                "type": "connect",
                "session_id": session_id
            }))
            
            print(f"세션 ID {session_id}로 연결됨")
            
            # 메시지 수신 대기
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    print(f"받은 메시지: {message}")
            except asyncio.TimeoutError:
                print("10초 동안 메시지가 없어 종료합니다.")
            
    except Exception as e:
        print(f"WebSocket 연결 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())