# backend/evaluation/report_generator.py
def generate_performance_report(metrics: dict):
    """Generate and print performance report to console"""
    print("\n" + "="*50)
    print(" RESEARCH PERFORMANCE REPORT ".center(50))
    print("="*50)
    
    print("\nAgent Performance:")
    for agent, stats in metrics["agent_performance"].items():
        success_rate = (stats["tasks"] - stats["errors"]) / stats["tasks"] if stats["tasks"] else 0
        print(f"- {agent}: {stats['tasks']} tasks | {stats['errors']} errors | {success_rate:.1%} success")
    
    print("\nTool Usage:")
    for tool, count in metrics["tool_usage"].items():
        print(f"- {tool}: {count} uses")
    
    print("\n" + "="*50)
