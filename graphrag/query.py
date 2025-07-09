import subprocess
import json
import os

class GraphRAGQuery:
    def __init__(self, config_path="./settings.yaml"):
        self.config_path = config_path
    
    def local_search(self, query: str) -> str:
        """Local Search 실행"""
        cmd = [
            "python", "-m", "graphrag", "query",
            "--config", self.config_path,
            "--method", "local",
            "--query", query
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # 출력에서 실제 응답 부분만 추출
            lines = result.stdout.split('\n')
            response_started = False
            response_lines = []
            
            for line in lines:
                if "SUCCESS: Local Search Response:" in line:
                    response_started = True
                    continue
                if response_started and line.strip():
                    response_lines.append(line)
            
            return '\n'.join(response_lines)
        else:
            return f"Error: {result.stderr}"
    
    def global_search(self, query: str) -> str:
        """Global Search 실행"""
        cmd = [
            "python", "-m", "graphrag", "query",
            "--config", self.config_path,
            "--method", "global",
            "--query", query
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # 출력에서 실제 응답 부분만 추출
            lines = result.stdout.split('\n')
            response_started = False
            response_lines = []
            
            for line in lines:
                if "SUCCESS: Global Search Response:" in line:
                    response_started = True
                    continue
                if response_started and line.strip():
                    response_lines.append(line)
            
            return '\n'.join(response_lines)
        else:
            return f"Error: {result.stderr}"

# 사용 예시
if __name__ == "__main__":
    rag = GraphRAGQuery()
    
    # Local Search
    print("Local Search 결과:")
    print("="*50 + "\n")
    result = rag.local_search("AutoGen에서 Team 기능은 무엇인가요?")
    print("믿음2.0 결과: ", result)
    print("\n" + "="*50 + "\n")
    
    # Global Search
    print("Global Search 결과:")
    print("="*50 + "\n")
    result = rag.global_search("AutoGen의 주요 특징들을 설명해주세요")
    print("믿음2.0 결과: ", result)
    print("\n" + "="*50 + "\n")