# backend/evaluation/report_generator.py
def generate_performance_report(metrics: dict):
    """Generate and print performance report to console"""
    print("\n" + "="*50)
    print(" RESEARCH PERFORMANCE REPORT ".center(50))
    print("="*50)
    
    print("\nAgent Performance:")
    for agent, stats in metrics["agent_performance"].items():
        tasks = stats["tasks"]
        errors = stats["errors"]
        success_rate = (tasks - errors) / tasks if tasks else 0
        print(f"- {agent}: {tasks} tasks | {errors} errors | {success_rate:.1%} success")
    
    print("\nTool Usage:")
    for tool, count in metrics["tool_usage"].items():
        print(f"- {tool}: {count} uses")
    
    # Add success rate summary
    total_tasks = sum(stats["tasks"] for stats in metrics["agent_performance"].values())
    total_errors = sum(stats["errors"] for stats in metrics["agent_performance"].values())
    overall_success = (total_tasks - total_errors) / total_tasks if total_tasks else 1.0
    
    print("\nSummary:")
    print(f"Total Tasks: {total_tasks}")
    print(f"Total Errors: {total_errors}")
    print(f"Overall Success Rate: {overall_success:.1%}")
    
    print("\n" + "="*50)
