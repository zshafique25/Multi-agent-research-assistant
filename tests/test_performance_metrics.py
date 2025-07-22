# tests/test_performance_metrics.py
import sys
import os
import pytest

# Add backend to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))

from evaluation.metrics import ResearchMetrics

def test_metrics_tracking():
    """Test the functionality of the ResearchMetrics class"""
    metrics = ResearchMetrics()
    
    # Test agent logging
    metrics.log_agent_task("TestAgent", True)
    metrics.log_agent_task("TestAgent", False)
    assert metrics.agent_performance["TestAgent"]["tasks"] == 2
    assert metrics.agent_performance["TestAgent"]["errors"] == 1
    
    # Test tool logging
    metrics.log_tool_usage("test_tool")
    metrics.log_tool_usage("test_tool")
    assert metrics.tool_usage["test_tool"] == 2
    
    # Test error logging
    metrics.log_tool_usage("test_tool_error")
    assert metrics.tool_usage["test_tool_error"] == 1
    
    # Test report generation
    report = metrics.generate_report()
    assert "TestAgent" in report["agent_performance"]
    assert report["agent_performance"]["TestAgent"]["tasks"] == 2
    assert report["agent_performance"]["TestAgent"]["errors"] == 1
    assert report["tool_usage"]["test_tool"] == 2
    assert report["tool_usage"]["test_tool_error"] == 1

def test_metrics_reset():
    """Test the reset functionality of ResearchMetrics"""
    metrics = ResearchMetrics()
    
    # Log some data
    metrics.log_agent_task("TestAgent", True)
    metrics.log_tool_usage("test_tool")
    
    # Reset metrics
    metrics.reset()
    
    # Verify reset
    assert metrics.agent_performance == {}
    assert metrics.tool_usage == {}
    
    report = metrics.generate_report()
    assert report["agent_performance"] == {}
    assert report["tool_usage"] == {}

if __name__ == "__main__":
    pytest.main([__file__])
