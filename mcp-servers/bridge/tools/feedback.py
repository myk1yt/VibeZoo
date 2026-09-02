import os
import json
import datetime
from bridge.utils import _markdown_header, _markdown_footer
from bridge.i18n import t

def register(mcp):
    @mcp.tool()
    def vibezoo_feedback(category: str, description: str, suggested_snippet: str = "") -> str:
        """
        에이전트가 작업 중 한계를 느끼거나 반복적인 스크립트 작성을 인지했을 때, 
        사용자(이온기반 지능)에게 시스템 개선을 능동적으로 제안하는 도구.
        
        Args:
            category (str): 'missing_tool', 'repetitive_task', 'optimization_idea', 'bug_report'
            description (str): 제안하는 내용의 구체적 설명 및 배경
            suggested_snippet (str, optional): 기능 자동화를 위해 에이전트가 즉흥적으로 작성해 본 파이썬 스크립트나 셸 명령어
        """
        valid_categories = ['missing_tool', 'repetitive_task', 'optimization_idea', 'bug_report']
        if category not in valid_categories:
            return _markdown_header("Feedback Error", "❌") + f"Invalid category. Must be one of: {', '.join(valid_categories)}" + _markdown_footer()

        # Write to feedbacks/autonomous_agent_suggestions.jsonl
        feedback_dir = "feedbacks"
        os.makedirs(feedback_dir, exist_ok=True)
        feedback_file = os.path.join(feedback_dir, "autonomous_agent_suggestions.jsonl")
        
        feedback_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "category": category,
            "description": description,
            "suggested_snippet": suggested_snippet
        }
        
        try:
            with open(feedback_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")
                
            output = _markdown_header("Feedback Submitted", "✅")
            output += f"**Category**: {category}\n"
            output += f"**Description**: {description}\n"
            if suggested_snippet:
                output += f"**Snippet Attached**: Yes\n"
            output += "Thank you for the autonomous suggestion. The user will review it.\n"
            output += _markdown_footer()
            return output
            
        except Exception as e:
            return _markdown_header("Feedback Error", "❌") + f"Failed to save feedback: {str(e)}" + _markdown_footer()
