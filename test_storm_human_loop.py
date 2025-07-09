#!/usr/bin/env python3
"""
STORM Human-in-the-Loop 기능 테스트 스크립트
"""

import asyncio
import json
import requests
import websockets
from datetime import datetime
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000/api/v1"
WS_BASE_URL = "ws://localhost:8000/api/v1"

class StormHumanLoopTester:
    """STORM Human-in-the-Loop 테스터"""
    
    def __init__(self):
        self.session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.user_id = "test_user"
        self.websocket = None
        
    def print_banner(self, title: str):
        """테스트 배너 출력"""
        print("\n" + "="*60)
        print(f"🧪 {title}")
        print("="*60)
    
    def print_step(self, step: str):
        """테스트 단계 출력"""
        print(f"\n📋 {step}")
        print("-" * 40)
    
    def test_storm_capabilities(self):
        """STORM 시스템 능력 테스트"""
        self.print_banner("STORM 시스템 능력 테스트")
        
        try:
            response = requests.get(f"{API_BASE_URL}/chat/capabilities")
            if response.status_code == 200:
                data = response.json()
                print("✅ STORM 시스템 능력 조회 성공")
                
                # STORM 관련 정보 출력
                storm_caps = data.get("storm_capabilities", {})
                print(f"🌩️ STORM 사용 가능: {storm_caps.get('available', False)}")
                print(f"🔧 최대 워커 수: {storm_caps.get('max_workers', 0)}")
                print(f"📝 지원 기능: {', '.join(storm_caps.get('supported_features', []))}")
                print(f"🎯 인터랙티브 기능: {', '.join(storm_caps.get('interactive_features', []))}")
                
                return True
            else:
                print(f"❌ 능력 조회 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            return False
    
    def test_basic_storm_research(self):
        """기본 STORM 연구 테스트"""
        self.print_banner("기본 STORM 연구 테스트")
        
        try:
            request_data = {
                "topic": "AI 에이전트 시스템의 미래",
                "user_id": self.user_id,
                "session_id": self.session_id,
                "config": {
                    "enabled": True,
                    "editor_count": 3,
                    "enable_search": True
                },
                "enable_human_loop": False,
                "stream": False
            }
            
            self.print_step("기본 STORM 연구 요청 전송")
            response = requests.post(f"{API_BASE_URL}/chat/storm", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 기본 STORM 연구 성공")
                print(f"📄 결과 길이: {len(data['result'])} 글자")
                print(f"⏱️ 처리 시간: {data['processing_time']:.2f}초")
                print(f"📊 통계: {data.get('stats', {})}")
                
                # 결과 일부 출력
                result_preview = data['result'][:200] + "..." if len(data['result']) > 200 else data['result']
                print(f"📝 결과 미리보기:\n{result_preview}")
                
                return True
            else:
                print(f"❌ 기본 연구 실패: {response.status_code}")
                print(f"오류: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            return False
    
    async def test_interactive_storm_websocket(self):
        """인터랙티브 STORM 웹소켓 테스트"""
        self.print_banner("인터랙티브 STORM 웹소켓 테스트")
        
        try:
            self.print_step("웹소켓 연결 시도")
            
            async with websockets.connect(f"{WS_BASE_URL}/ws/storm/{self.session_id}") as websocket:
                self.websocket = websocket
                print("✅ 웹소켓 연결 성공")
                
                # 인터랙티브 연구 시작
                await self.start_interactive_research()
                
                # 웹소켓 메시지 수신 대기
                await self.handle_websocket_messages()
                
        except Exception as e:
            print(f"❌ 웹소켓 테스트 실패: {str(e)}")
            return False
    
    async def start_interactive_research(self):
        """인터랙티브 연구 시작"""
        self.print_step("인터랙티브 STORM 연구 시작")
        
        try:
            request_data = {
                "topic": "블록체인 기술의 현재와 미래",
                "user_id": self.user_id,
                "session_id": self.session_id,
                "config": {
                    "enabled": True,
                    "human_in_the_loop": True,
                    "editor_count": 4,
                    "enable_search": True,
                    "enable_interviews": True
                }
            }
            
            # 비동기 HTTP 요청 (실제 환경에서는 aiohttp 사용)
            import threading
            import time
            
            def make_request():
                try:
                    response = requests.post(f"{API_BASE_URL}/chat/storm/interactive", json=request_data)
                    print(f"📡 인터랙티브 연구 응답: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ 인터랙티브 연구 완료")
                        print(f"📄 결과 타입: {data.get('type')}")
                        print(f"📝 내용 길이: {len(data.get('content', ''))}")
                    else:
                        print(f"❌ 응답 오류: {response.text}")
                except Exception as e:
                    print(f"❌ 요청 오류: {str(e)}")
            
            # 백그라운드에서 연구 시작
            thread = threading.Thread(target=make_request)
            thread.daemon = True
            thread.start()
            
            print("🚀 인터랙티브 연구 시작됨 (백그라운드)")
            
        except Exception as e:
            print(f"❌ 연구 시작 실패: {str(e)}")
    
    async def handle_websocket_messages(self):
        """웹소켓 메시지 처리"""
        self.print_step("웹소켓 메시지 수신 대기")
        
        message_count = 0
        interaction_count = 0
        
        try:
            async for message in self.websocket:
                message_count += 1
                data = json.loads(message)
                message_type = data.get("type", "unknown")
                
                print(f"📨 메시지 #{message_count}: {message_type}")
                
                if message_type == "storm_start":
                    print(f"🚀 연구 시작: {data.get('topic', 'Unknown')}")
                    
                elif message_type == "storm_progress":
                    step = data.get("step", 0)
                    total_steps = data.get("total_steps", 6)
                    content = data.get("content", "")
                    print(f"📊 진행 상황: [{step}/{total_steps}] {content}")
                    
                elif message_type == "interaction_required":
                    interaction_count += 1
                    print(f"🤔 상호작용 요청 #{interaction_count}")
                    
                    interaction = data.get("interaction", {})
                    interaction_type = interaction.get("type", "unknown")
                    title = interaction.get("title", "")
                    content = interaction.get("content", "")
                    options = interaction.get("options", [])
                    
                    print(f"   타입: {interaction_type}")
                    print(f"   제목: {title}")
                    print(f"   내용: {content}")
                    print(f"   옵션: {options}")
                    
                    # 자동 응답 (실제 환경에서는 사용자 입력 처리)
                    await self.send_human_response(interaction.get("interaction_id", ""), "approve")
                    
                elif message_type == "storm_complete":
                    print(f"🎉 연구 완료!")
                    content = data.get("content", "")
                    if content:
                        preview = content[:200] + "..." if len(content) > 200 else content
                        print(f"📝 결과 미리보기:\n{preview}")
                    break
                    
                elif message_type == "storm_error":
                    print(f"❌ 연구 오류: {data.get('error', 'Unknown error')}")
                    break
                    
                elif message_type == "response_processed":
                    print(f"✅ 응답 처리됨: {data.get('action', 'unknown')}")
                    
                # 메시지 수 제한 (무한 대기 방지)
                if message_count > 50:
                    print("⏰ 메시지 수 제한 도달, 테스트 종료")
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 웹소켓 연결 종료")
        except Exception as e:
            print(f"❌ 메시지 처리 오류: {str(e)}")
        
        print(f"📊 테스트 결과: {message_count}개 메시지, {interaction_count}개 상호작용")
    
    async def send_human_response(self, interaction_id: str, action: str):
        """사용자 응답 전송"""
        try:
            response_data = {
                "type": "human_response",
                "interaction_id": interaction_id,
                "action": action,
                "feedback": f"자동 테스트 응답: {action}",
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(response_data))
            print(f"📤 사용자 응답 전송: {action}")
            
        except Exception as e:
            print(f"❌ 응답 전송 실패: {str(e)}")
    
    def test_session_status(self):
        """세션 상태 조회 테스트"""
        self.print_banner("세션 상태 조회 테스트")
        
        try:
            response = requests.get(f"{API_BASE_URL}/chat/storm/session/{self.session_id}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 세션 상태 조회 성공")
                print(f"📋 세션 ID: {data.get('session_id')}")
                print(f"👤 사용자 ID: {data.get('user_id')}")
                print(f"📊 현재 단계: {data.get('current_step', 0)}/{data.get('total_steps', 6)}")
                print(f"⏱️ 경과 시간: {data.get('elapsed_time', 0):.2f}초")
                print(f"🤔 상호작용 있음: {data.get('has_interaction', False)}")
                print(f"✅ 완료됨: {data.get('completed', False)}")
                
                return True
            else:
                print(f"❌ 세션 상태 조회 실패: {response.status_code}")
                if response.status_code == 404:
                    print("💡 세션이 아직 생성되지 않았을 수 있습니다.")
                return False
                
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 STORM Human-in-the-Loop 기능 테스트 시작")
        print(f"📋 세션 ID: {self.session_id}")
        print(f"👤 사용자 ID: {self.user_id}")
        
        test_results = []
        
        # 1. 시스템 능력 테스트
        result1 = self.test_storm_capabilities()
        test_results.append(("시스템 능력 테스트", result1))
        
        # 2. 기본 연구 테스트
        result2 = self.test_basic_storm_research()
        test_results.append(("기본 연구 테스트", result2))
        
        # 3. 인터랙티브 웹소켓 테스트
        try:
            await self.test_interactive_storm_websocket()
            test_results.append(("인터랙티브 웹소켓 테스트", True))
        except Exception as e:
            print(f"❌ 인터랙티브 테스트 실패: {str(e)}")
            test_results.append(("인터랙티브 웹소켓 테스트", False))
        
        # 4. 세션 상태 테스트
        result4 = self.test_session_status()
        test_results.append(("세션 상태 테스트", result4))
        
        # 결과 요약
        self.print_test_summary(test_results)
    
    def print_test_summary(self, results):
        """테스트 결과 요약"""
        self.print_banner("테스트 결과 요약")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"📊 총 테스트: {total}개")
        print(f"✅ 통과: {passed}개")
        print(f"❌ 실패: {total - passed}개")
        print(f"📈 성공률: {passed/total*100:.1f}%")
        
        print("\n상세 결과:")
        for test_name, result in results:
            status = "✅ 통과" if result else "❌ 실패"
            print(f"  {status} {test_name}")
        
        if passed == total:
            print("\n🎉 모든 테스트 통과! Human-in-the-Loop 기능이 정상적으로 작동합니다.")
        else:
            print("\n⚠️ 일부 테스트 실패. 로그를 확인하여 문제를 해결하세요.")

async def main():
    """메인 테스트 실행"""
    tester = StormHumanLoopTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 