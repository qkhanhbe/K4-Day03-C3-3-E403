"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS, analyze_alter_ego, assess_psychological_risk, get_counseling_action_plan
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


import re

def execute_tool(action_str: str) -> str:
    """
    Phân tích tên tool và tham số từ chuỗi Action (ví dụ: analyze_alter_ego['vui vẻ'] hoặc get_counseling_action_plan['hidden_volcano', 'High'])
    """
    try:
        match = re.search(r"(\w+)\s*[\[\(](.*?)[\]\)]", action_str, re.DOTALL)
        if not match:
            return "Lỗi: Cú pháp Action không hợp lệ. Phải có dạng: tool_name[tham_số]"
        
        tool_name = match.group(1).strip()
        raw_args = match.group(2).strip()
        
        if tool_name not in AVAILABLE_TOOLS:
            return f"Lỗi: Không tìm thấy công cụ '{tool_name}' trong danh sách công cụ khả dụng."
            
        tool_func = AVAILABLE_TOOLS[tool_name]
        
        if "," in raw_args and tool_name == "get_counseling_action_plan":
            parts = [p.strip().strip("'\"") for p in raw_args.split(",")]
            if len(parts) >= 2:
                return tool_func(parts[0], parts[1])
            else:
                return tool_func(parts[0], "Low")
        else:
            clean_arg = raw_args.strip("'\"")
            return tool_func(clean_arg)
    except Exception as e:
        return f"Lỗi khi thực thi công cụ: {str(e)}"


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails hoàn chỉnh.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    conversation_history = f"Câu hỏi của người dùng: {user_query}\n"
    step = 0
    completed = False
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        prompt = f"{conversation_history}\nHãy thực hiện bước suy luận tiếp theo (Thought/Action hoặc Thought/Final Answer):"
        llm_response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT).strip()
        print(f"{llm_response}")
        
        if "Final Answer:" in llm_response:
            completed = True
            break
            
        if "Action:" in llm_response:
            action_lines = [line for line in llm_response.split("\n") if "Action:" in line]
            if action_lines:
                action_content = action_lines[0].replace("Action:", "").strip()
                obs = execute_tool(action_content)
                print(f"👁️ Observation: {obs}")
                conversation_history += f"\n{llm_response}\nObservation: {obs}\n"
            else:
                conversation_history += f"\n{llm_response}\n"
        else:
            conversation_history += f"\n{llm_response}\nObservation: Vui lòng sử dụng đúng cú pháp Action: tên_công_cụ[tham_số] hoặc Final Answer: ...\n"
            
    if not completed and step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước suy luận. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu test số 7 (Tâm lý mâu thuẫn phức tạp - Cần 2 tools)
    sample_query = tests[6]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
