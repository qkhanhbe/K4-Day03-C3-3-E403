import os
import sys
import json
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Thêm thư mục gốc dự án vào sys.path để import src/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.append(SRC_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

provider = get_llm_provider()

def execute_tool(action_str: str) -> dict:
    try:
        match = re.search(r"(\w+)\s*[\[\(](.*?)[\]\)]", action_str, re.DOTALL)
        if not match:
            return {"error": "Cú pháp Action không hợp lệ. Phải dạng tool_name[tham_số]"}
        
        tool_name = match.group(1).strip()
        raw_args = match.group(2).strip()
        
        if tool_name not in AVAILABLE_TOOLS:
            return {"error": f"Không tìm thấy công cụ '{tool_name}'"}
            
        tool_func = AVAILABLE_TOOLS[tool_name]
        
        if "," in raw_args and tool_name == "get_counseling_action_plan":
            parts = [p.strip().strip("'\"") for p in raw_args.split(",")]
            if len(parts) >= 2:
                res_str = tool_func(parts[0], parts[1])
            else:
                res_str = tool_func(parts[0], "Low")
        else:
            clean_arg = raw_args.strip("'\"")
            res_str = tool_func(clean_arg)
            
        try:
            return {"raw": res_str, "parsed": json.loads(res_str)}
        except Exception:
            return {"raw": res_str, "parsed": res_str}
    except Exception as e:
        return {"error": f"Lỗi thực thi công cụ: {str(e)}"}


def run_react_agent_steps(user_query: str):
    steps = []
    conversation_history = f"Câu hỏi của người dùng: {user_query}\n"
    step = 0
    completed = False
    final_answer = ""
    
    while step < MAX_ITERATIONS:
        step += 1
        prompt = f"{conversation_history}\nHãy thực hiện bước suy luận tiếp theo (Thought/Action hoặc Thought/Final Answer):"
        llm_response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT).strip()
        
        step_data = {
            "step_number": step,
            "max_steps": MAX_ITERATIONS,
            "llm_response": llm_response,
            "thought": "",
            "action": "",
            "observation": None,
            "final_answer": ""
        }
        
        # Bóc tách Thought
        if "Thought:" in llm_response:
            thought_part = llm_response.split("Thought:")[1]
            if "Action:" in thought_part:
                step_data["thought"] = thought_part.split("Action:")[0].strip()
            elif "Final Answer:" in thought_part:
                step_data["thought"] = thought_part.split("Final Answer:")[0].strip()
            else:
                step_data["thought"] = thought_part.strip()
                
        # Kiểm tra Final Answer
        if "Final Answer:" in llm_response:
            final_answer = llm_response.split("Final Answer:")[1].strip()
            step_data["final_answer"] = final_answer
            steps.append(step_data)
            completed = True
            break
            
        # Kiểm tra Action
        if "Action:" in llm_response:
            action_lines = [line for line in llm_response.split("\n") if "Action:" in line]
            if action_lines:
                action_str = action_lines[0].replace("Action:", "").strip()
                step_data["action"] = action_str
                obs_res = execute_tool(action_str)
                step_data["observation"] = obs_res
                conversation_history += f"\n{llm_response}\nObservation: {obs_res.get('raw', '')}\n"
                
        steps.append(step_data)
        
    return {
        "steps": steps,
        "completed": completed,
        "guardrail_triggered": not completed,
        "final_answer": final_answer
    }


class WebDemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        web_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=web_dir, **kwargs)
        
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/test-cases":
            config_path = os.path.join(BASE_DIR, "config", "test_cases.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.send_json(data)
            else:
                self.send_json([])
        else:
            super().do_GET()
            
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body) if body else {}
        
        query = data.get("query", "")
        
        if parsed.path == "/api/chat/baseline":
            resp = provider.generate(query, system_prompt=CHATBOT_BASELINE_PROMPT)
            self.send_json({"response": resp, "prompt": CHATBOT_BASELINE_PROMPT})
            
        elif parsed.path == "/api/chat/react":
            result = run_react_agent_steps(query)
            self.send_json(result)
            
        else:
            self.send_error(404, "Endpoint not found")
            
    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

def main():
    ports = [8080, 8081, 8001, 8888, 8000]
    httpd = None
    selected_port = 8080
    
    for p in ports:
        try:
            server_address = ('', p)
            httpd = HTTPServer(server_address, WebDemoHandler)
            selected_port = p
            break
        except OSError:
            continue
            
    if not httpd:
        print("❌ Không thể tìm thấy cổng rảnh để khởi chạy server.")
        return
        
    print(f"🚀 Server Web Demo ReAct Agent đang chạy tại http://localhost:{selected_port}")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
