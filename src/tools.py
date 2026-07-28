import json

"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

def analyze_alter_ego(traits: str) -> str:
    """
    Phân tích 'nhân cách thứ 2' (Alter Ego) dựa trên mô tả tính cách/hành vi.
    
    Args:
        traits (str): Các đặc điểm tính cách, hành vi hoặc cảm xúc mà người dùng mô tả.
        
    Returns:
        str: Kết quả phân tích dưới dạng JSON chứa alter_ego_id, alter_ego_name, core_conflict, và risk_level.
    """
    traits_lower = traits.lower()
    
    if "123456" in traits_lower or "!@#" in traits_lower:
        return json.dumps({"error": "Dữ liệu đầu vào không hợp lệ. Vui lòng mô tả tính cách bằng văn bản tự nhiên."}, ensure_ascii=False)
        
    if "một mình" in traits_lower or "né tránh" in traits_lower or "cô đơn" in traits_lower and "khát khao" in traits_lower:
        result = {
            "alter_ego_id": "hedgehog_dilemma",
            "alter_ego_name": "Kẻ Ôm Cây Xương Rồng (Hội chứng Con Nhím)",
            "core_conflict": "Khao khát yêu thương và gắn kết nhưng lại sợ hãi sự tổn thương, dẫn đến việc tự đẩy người khác ra xa.",
            "risk_level": "Medium"
        }
    elif "nổi cáu" in traits_lower or "nhẫn nhịn" in traits_lower or "nổi loạn" in traits_lower:
        result = {
            "alter_ego_id": "hidden_volcano",
            "alter_ego_name": "Ngọn Núi Lửa Ngầm",
            "core_conflict": "Bên ngoài cố gắng tuân thủ và dồn nén cảm xúc, nhưng bên trong chán ghét thực tại và có xu hướng muốn phá vỡ lề thói.",
            "risk_level": "High"
        }
    elif "hoàn hảo" in traits_lower or "áp lực" in traits_lower or "vô dụng" in traits_lower:
        result = {
            "alter_ego_id": "anxious_achiever",
            "alter_ego_name": "Kẻ Cầu Toàn Ám Ảnh",
            "core_conflict": "Định giá giá trị bản thân hoàn toàn vào thành tựu công việc. Rất sợ thất bại và sợ bị phán xét.",
            "risk_level": "High"
        }
    elif "vui vẻ" in traits_lower or "hòa đồng" in traits_lower or "khuấy động" in traits_lower:
        result = {
            "alter_ego_id": "free_child",
            "alter_ego_name": "Đứa Trẻ Vô Tư",
            "core_conflict": "Tìm kiếm niềm vui bề mặt để trốn tránh việc phải đối mặt với các vấn đề sâu sắc hoặc sự tĩnh lặng cô độc.",
            "risk_level": "Low"
        }
    elif "triết lý" in traits_lower or "suy nghĩ" in traits_lower:
        result = {
            "alter_ego_id": "solitary_sage",
            "alter_ego_name": "Nhà Hiền Triết Cô Độc",
            "core_conflict": "Cảm thấy khó đồng điệu với số đông, thường tự cô lập bản thân trong tháp ngà suy tư.",
            "risk_level": "Low"
        }
    else:
        result = {
            "alter_ego_id": "unknown_wanderer",
            "alter_ego_name": "Kẻ Lữ Hành Bí Ẩn",
            "core_conflict": "Nhân cách đa chiều, chưa bộc lộ rõ ràng mâu thuẫn cốt lõi.",
            "risk_level": "Unknown"
        }
        
    return json.dumps(result, ensure_ascii=False)


def assess_psychological_risk(symptoms: str) -> str:
    """
    Đánh giá mức độ rủi ro tâm lý khẩn cấp (Red Flags) từ lời nói của người dùng.
    
    Args:
        symptoms (str): Lời tâm sự hoặc triệu chứng của người dùng.
        
    Returns:
        str: JSON chứa status rủi ro và khuyến nghị khẩn cấp.
    """
    try:
        symp = str(symptoms).lower()
        red_flags = ["tự tử", "chết", "không muốn sống", "tổn thương bản thân", "tuyệt vọng", "giọng nói", "ảo giác"]
        
        for flag in red_flags:
            if flag in symp:
                alert = {
                    "risk_status": "RED_FLAG",
                    "urgency": "CRITICAL",
                    "message": "Phát hiện dấu hiệu nguy hiểm đến tính mạng hoặc tinh thần nghiêm trọng.",
                    "action_required": "Yêu cầu Agent ngừng phân tích nhân cách ngay lập tức. Cung cấp đường dây nóng hỗ trợ tâm lý khẩn cấp (VD: 111 - Tổng đài Bảo vệ Trẻ em, hoặc hotline bệnh viện tâm thần gần nhất) và khuyên người dùng tìm kiếm sự giúp đỡ y tế chuyên nghiệp."
                }
                return json.dumps(alert, ensure_ascii=False)
                
        return json.dumps({
            "risk_status": "SAFE",
            "urgency": "NORMAL",
            "message": "Không phát hiện rủi ro khẩn cấp."
        }, ensure_ascii=False)
    except Exception as e:
        # TRÁNH CRASH CODE
        return json.dumps({"error": f"Lỗi nội bộ tool (assess_psychological_risk): {str(e)}"}, ensure_ascii=False)


def get_counseling_action_plan(alter_ego_id: str, risk_level: str) -> str:
    """
    Lấy phác đồ hành động tư vấn tâm lý 3 bước dựa trên ID nhân cách và mức độ rủi ro.
    
    Args:
        alter_ego_id (str): ID của nhân cách (VD: 'hidden_volcano', 'hedgehog_dilemma').
        risk_level (str): Mức độ rủi ro ('Low', 'Medium', 'High').
        
    Returns:
        str: Phác đồ tư vấn dưới dạng JSON.
    """
    plans = {
        "hedgehog_dilemma": {
            "step_1_first_aid": "Thừa nhận nỗi sợ bị tổn thương của mình mà không phán xét.",
            "step_2_cognitive": "Hiểu rằng không phải ai cũng sẽ rời đi hay làm đau bạn. Lòng tin cần được xây dựng từ từ.",
            "step_3_practice": "Thử mở lòng kể một câu chuyện nhỏ về bản thân với một người bạn cảm thấy an toàn nhất."
        },
        "hidden_volcano": {
            "step_1_first_aid": "Tìm ngay một không gian an toàn để xả sự bức xúc (đấm bao cát, hét vào gối, viết giấy rồi xé).",
            "step_2_cognitive": "Dồn nén không làm vấn đề biến mất. Bạn có quyền được tức giận và nói 'Không'.",
            "step_3_practice": "Thực hành giao tiếp quyết đoán (Assertive communication): Tập nói lên ý kiến trái chiều trong những việc nhỏ."
        },
        "anxious_achiever": {
            "step_1_first_aid": "Ngừng làm việc ngay lập tức, hít thở sâu 5 phút. Nhắc nhở bản thân: 'Mình an toàn'.",
            "step_2_cognitive": "Tách bạch giá trị con người bạn khỏi những thành tựu công việc. Bạn đáng giá dù bạn không hoàn hảo.",
            "step_3_practice": "Dành ra 1 tiếng/ngày làm một việc hoàn toàn vô dụng nhưng khiến bạn vui (nghe nhạc, ngắm cây)."
        },
        "free_child": {
            "step_1_first_aid": "Dành 10 phút ngồi yên lặng một mình, không điện thoại, không âm nhạc.",
            "step_2_cognitive": "Nỗi buồn không đáng sợ. Chạy trốn nó mới làm bạn mệt mỏi.",
            "step_3_practice": "Viết nhật ký về một điều khiến bạn cảm thấy không vui trong ngày thay vì lờ nó đi."
        },
        "solitary_sage": {
            "step_1_first_aid": "Chấp nhận rằng sự cô độc là lựa chọn của bạn, không phải sự trừng phạt.",
            "step_2_cognitive": "Đôi khi góc nhìn của người khác, dù có vẻ nông cạn, cũng mang lại những màu sắc mới cho bức tranh nhân sinh.",
            "step_3_practice": "Chủ động tham gia một cuộc trò chuyện nhỏ ngoài chuyên môn mỗi tuần một lần."
        }
    }
    
    default_plan = {
        "step_1_first_aid": "Thả lỏng cơ thể và hít thở sâu.",
        "step_2_cognitive": "Quan sát cảm xúc của mình như một người ngoài cuộc.",
        "step_3_practice": "Trò chuyện với người thân thiện hoặc tìm chuyên gia."
    }
    
    selected_plan = plans.get(alter_ego_id, default_plan)
    
    response = {
        "action_plan": selected_plan,
        "note": "Cần chú ý theo dõi sát sao do mức độ rủi ro cao." if risk_level == "High" else "Hãy thực hành từ từ theo nhịp độ của bản thân."
    }
    
    return json.dumps(response, ensure_ascii=False)


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "analyze_alter_ego": analyze_alter_ego,
    "assess_psychological_risk": assess_psychological_risk,
    "get_counseling_action_plan": get_counseling_action_plan,
}
