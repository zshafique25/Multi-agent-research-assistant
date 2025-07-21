# backend/evaluation/metrics.py
from collections import defaultdict

class ResearchMetrics:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.agent_performance = defaultdict(lambda: {"tasks": 0, "errors": 0})
        self.task_timings = []
        self.tool_usage = defaultdict(int)

    def log_agent_task(self, agent_name: str, success: bool):
        self.agent_performance[agent_name]["tasks"] += 1
        if not success:
            self.agent_performance[agent_name]["errors"] += 1

    def log_tool_usage(self, tool_name: str):
        self.tool_usage[tool_name] += 1

    def generate_report(self):
        return {
            "agent_performance": dict(self.agent_performance),
            "tool_usage": dict(self.tool_usage)
        }
