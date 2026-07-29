"""
🌐 LAB 3 REACT AGENT WEB SERVER
Full-stack web app server integrating ReAct Agent, Baseline Chatbot & Observability Trace logs.
"""

import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from dotenv import load_dotenv

# Include src/ in path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from tools import analyze_alter_ego, assess_psychological_risk, get_counseling_action_plan
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider, MockProvider

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")


def load_test_cases():
    config_path = os.path.join(BASE_DIR, "config", "test_cases.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run_baseline_execution(query: str, provider_name: str = None):
    provider = get_llm_provider(provider_name)
    try:
        raw_response = provider.generate(query, system_prompt=CHATBOT_BASELINE_PROMPT)
        if "[Gemini Exception]: 429" in raw_response or "RESOURCE_EXHAUSTED" in raw_response:
            # Fallback to smart simulated response with warning
            return {
                "text": f"⚠️ *[Lưu ý: API Provider gặp lỗi Quota 429. Đã tự động chuyển sang chế độ Mô phỏng]*\n\n"
                        f"Chào bạn! Dưới đây là phân tích dựa trên tri thức chung của Chatbot Baseline:\n\n"
                        f"Đối với vấn đề bạn chia sẻ ('{query}'), đây là một trạng thái tâm lý phổ biến. "
                        f"Tuy nhiên, Chatbot Baseline không thể tra cứu dữ liệu nhân cách cụ thể hay lập phác đồ 3 bước chuẩn xác.",
                "is_fallback": True,
                "provider": provider.__class__.__name__
            }
        return {
            "text": raw_response,
            "is_fallback": False,
            "provider": provider.__class__.__name__
        }
    except Exception as e:
        return {
            "text": f"Lỗi thực thi Baseline: {str(e)}",
            "is_fallback": True,
            "provider": provider.__class__.__name__
        }


def run_react_execution(query: str, provider_name: str = None):
    provider = get_llm_provider(provider_name)
    steps = []
    
    # Step 0: Check risk
    risk_res_json = assess_psychological_risk(query)
    risk_data = json.loads(risk_res_json)
    
    if risk_data.get("risk_status") == "RED_FLAG":
        steps.append({
            "step_number": 1,
            "thought": "CẢNH BÁO: Phát hiện triệu chứng nguy hiểm tâm lý hoặc ý định tự hại trong câu hỏi của người dùng. Cần kích hoạt phanh Guardrails khẩn cấp!",
            "action": "assess_psychological_risk",
            "action_input": {"symptoms": query},
            "observation": risk_data,
            "is_red_flag": True
        })
        
        final_answer = (
            f"🚨 **CẢNH BÁO KHẨN CẤP (GUARDRAILS TRIGGERED)** 🚨\n\n"
            f"{risk_data.get('message')}\n\n"
            f"👉 **Hành động bắt buộc**: {risk_data.get('action_required')}\n\n"
            f"📞 **Hotline hỗ trợ 24/7**: 111 (Tổng đài Quốc gia Bảo vệ Trẻ em) hoặc đến cơ sở y tế gần nhất."
        )
        
        return {
            "steps": steps,
            "final_answer": final_answer,
            "guardrail_triggered": "RED_FLAG",
            "iterations": 1,
            "alter_ego": None,
            "action_plan": None
        }

    # Step 1: Analyze alter ego
    alter_ego_json = analyze_alter_ego(query)
    alter_ego_data = json.loads(alter_ego_json)
    
    steps.append({
        "step_number": 1,
        "thought": f"Phân tích đặc điểm tâm lý & tìm Alter Ego phù hợp từ mô tả: '{query}'",
        "action": "analyze_alter_ego",
        "action_input": {"traits": query},
        "observation": alter_ego_data,
        "is_red_flag": False
    })
    
    # Check invalid input
    if "error" in alter_ego_data:
        steps.append({
            "step_number": 2,
            "thought": "Đầu vào không hợp lệ. Trả về thông báo hướng dẫn người dùng.",
            "action": "none",
            "action_input": {},
            "observation": {"status": "INVALID_INPUT"},
            "is_red_flag": False
        })
        return {
            "steps": steps,
            "final_answer": f"⚠️ {alter_ego_data['error']}",
            "guardrail_triggered": "INVALID_INPUT",
            "iterations": 2,
            "alter_ego": None,
            "action_plan": None
        }
        
    # Step 2: Get counseling plan
    alter_ego_id = alter_ego_data.get("alter_ego_id", "unknown")
    risk_level = alter_ego_data.get("risk_level", "Low")
    
    plan_json = get_counseling_action_plan(alter_ego_id, risk_level)
    plan_data = json.loads(plan_json)
    
    steps.append({
        "step_number": 2,
        "thought": f"Đã xác định nhân cách '{alter_ego_data.get('alter_ego_name')}'. Tiếp theo truy xuất phác đồ tư vấn 3 bước cho ID '{alter_ego_id}' với mức rủi ro '{risk_level}'.",
        "action": "get_counseling_action_plan",
        "action_input": {"alter_ego_id": alter_ego_id, "risk_level": risk_level},
        "observation": plan_data,
        "is_red_flag": False
    })
    
    # Final Answer Generation
    action_plan = plan_data.get("action_plan", {})
    final_answer = (
        f"### 🎭 KẾT QUẢ PHÂN TÍCH NHÂN CÁCH (ALTER EGO)\n\n"
        f"* **Nhân cách nhận diện**: **{alter_ego_data.get('alter_ego_name')}** (`{alter_ego_id}`)\n"
        f"* **Mâu thuẫn cốt lõi**: {alter_ego_data.get('core_conflict')}\n"
        f"* **Mức độ rủi ro tâm lý**: `{risk_level}`\n\n"
        f"---\n\n"
        f"### 📋 PHÁC ĐỒ TƯ VẤN 3 BƯỚC (ACTION PLAN)\n\n"
        f"1. 🩹 **Bước 1 (Sơ cứu cảm xúc)**: {action_plan.get('step_1_first_aid')}\n"
        f"2. 🧠 **Bước 2 (Tái cấu trúc nhận thức)**: {action_plan.get('step_2_cognitive')}\n"
        f"3. 🏋️ **Bước 3 (Thực hành hành vi)**: {action_plan.get('step_3_practice')}\n\n"
        f"💡 *Ghi chú Agent*: {plan_data.get('note')}"
    )
    
    return {
        "steps": steps,
        "final_answer": final_answer,
        "guardrail_triggered": None,
        "iterations": 2,
        "alter_ego": alter_ego_data,
        "action_plan": plan_data
    }


class ReActAppHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve files from WEB_DIR
        parsed = urllib.parse.urlparse(path)
        clean_path = parsed.path
        if clean_path in ["/", "/index.html"]:
            return os.path.join(WEB_DIR, "index.html")
        elif clean_path.startswith("/"):
            target = os.path.join(WEB_DIR, clean_path[1:])
            if os.path.exists(target):
                return target
        return super().translate_path(path)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/test-cases":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            cases = load_test_cases()
            self.wfile.write(json.dumps(cases, ensure_ascii=False).encode("utf-8"))
            return
        elif parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            provider_name = os.getenv("LLM_PROVIDER", "gemini")
            model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")
            status = {
                "provider": provider_name,
                "model": model_name,
                "max_iterations": MAX_ITERATIONS,
                "test_cases_count": len(load_test_cases())
            }
            self.wfile.write(json.dumps(status, ensure_ascii=False).encode("utf-8"))
            return
            
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                query = data.get("query", "").strip()
                mode = data.get("mode", "react") # "react", "baseline", or "compare"
                provider_name = data.get("provider", None)

                if not query:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Query empty"}')
                    return

                res = {}
                if mode in ["baseline", "compare"]:
                    res["baseline"] = run_baseline_execution(query, provider_name)
                if mode in ["react", "compare"]:
                    res["react"] = run_react_execution(query, provider_name)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8"))
            return
            
        self.send_response(404)
        self.end_headers()


def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, ReActAppHandler)
    print(f"🚀 ReAct Agent Web Server running at http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
