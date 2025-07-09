#!/usr/bin/env python3
"""
STORM 스트리밍 API 테스트 스크립트
1명의 연구자로 테스트하여 시스템이 올바르게 작동하는지 확인
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

from backend.agent.storm_research import ParallelStormResearchSystem

async def test_storm_single_researcher():
    """1명의 연구자로 STORM 시스템 테스트"""
    
    print("="*80)
    print("🌩️ STORM 스트리밍 API 테스트 (1명 연구자)")
    print("="*80)
    
    # STORM 시스템 초기화
    storm_system = ParallelStormResearchSystem(max_workers=1)
    
    # 테스트 주제
    test_topic = "AI 에이전트의 미래"
    
    print(f"📝 테스트 주제: {test_topic}")
    print(f"👥 연구자 수: 1명")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*80)
    
    start_time = time.time()
    results = []
    
    try:
        # STORM 연구 실행 및 스트리밍 이벤트 수집
        async for event in storm_system.run_parallel_storm_research(
            topic=test_topic,
            enable_human_loop=False,
            editor_count=1
        ):
            results.append(event)
            
            # 실시간 로그 출력
            if event.get("type") == "log":
                level = event.get("level", "info").upper()
                message = event.get("message", "")
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # 로그 레벨별 색상 및 아이콘
                icons = {
                    "INFO": "📋",
                    "SUCCESS": "✅", 
                    "ERROR": "❌",
                    "WARNING": "⚠️"
                }
                
                icon = icons.get(level, "📋")
                print(f"[{timestamp}] {icon} {message}")
                
            elif event.get("type") == "storm_progress":
                step = event.get("step", 0)
                total_steps = event.get("total_steps", 6)
                message = event.get("message", "")
                progress = (step / total_steps) * 100
                
                print(f"📊 진행률: [{step}/{total_steps}] {progress:.1f}% - {message}")
                
            elif event.get("type") == "storm_complete":
                content = event.get("content", "")
                processing_time = event.get("processing_time", 0)
                
                print("-"*80)
                print(f"🎉 STORM 연구 완료!")
                print(f"⏱️ 총 소요시간: {processing_time:.2f}초")
                print(f"📄 결과 길이: {len(content):,} 글자")
                print(f"📊 단어 수: {len(content.split()):,} 단어")
                print("-"*80)
                
                # 결과를 파일로 저장
                output_file = f"storm_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# STORM 연구 결과: {test_topic}\n\n")
                    f.write(f"- **연구자 수**: 1명\n")
                    f.write(f"- **처리 시간**: {processing_time:.2f}초\n")
                    f.write(f"- **생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    f.write(content)
                
                print(f"💾 결과가 '{output_file}' 파일로 저장되었습니다.")
                break
    
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 리소스 정리
        try:
            await storm_system.model_client.close()
            await storm_system.long_context_model.close()
        except:
            pass
    
    total_time = time.time() - start_time
    print(f"🏁 테스트 완료 (전체 소요시간: {total_time:.2f}초)")
    
    # 이벤트 통계
    event_types = {}
    for result in results:
        event_type = result.get("type", "unknown")
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print("\n📊 이벤트 통계:")
    for event_type, count in event_types.items():
        print(f"  - {event_type}: {count}개")
    
    return True

async def test_api_compatibility():
    """API 호환성 테스트"""
    print("\n" + "="*80)
    print("🔧 API 호환성 테스트")
    print("="*80)
    
    try:
        # AgentService와의 호환성 테스트
        from app.services.agent_service import AgentService
        
        agent_service = AgentService()
        await agent_service.initialize()
        
        print("✅ AgentService 초기화 성공")
        
        # STORM 서비스 확인
        if agent_service.storm_service:
            print("✅ STORM 서비스 사용 가능")
            
            # 스트리밍 메서드 확인
            if hasattr(agent_service, 'process_message_stream'):
                print("✅ 스트리밍 메서드 사용 가능")
            else:
                print("❌ 스트리밍 메서드 없음")
        else:
            print("❌ STORM 서비스 사용 불가")
        
        await agent_service.cleanup()
        
    except Exception as e:
        print(f"❌ API 호환성 테스트 실패: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    async def main():
        print("🧪 STORM 시스템 테스트 시작\n")
        
        # 1. 기본 STORM 테스트
        success1 = await test_storm_single_researcher()
        
        # 2. API 호환성 테스트  
        success2 = await test_api_compatibility()
        
        print("\n" + "="*80)
        print("📋 테스트 결과 요약")
        print("="*80)
        print(f"🌩️ STORM 기본 테스트: {'✅ 성공' if success1 else '❌ 실패'}")
        print(f"🔧 API 호환성 테스트: {'✅ 성공' if success2 else '❌ 실패'}")
        
        if success1 and success2:
            print("\n🎉 모든 테스트가 성공했습니다!")
            print("💡 이제 프론트엔드에서 STORM 연구를 시작할 수 있습니다.")
        else:
            print("\n⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")
    
    asyncio.run(main()) 