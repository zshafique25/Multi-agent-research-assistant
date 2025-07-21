# backend/services/approval_service.py
import json
from typing import Dict, Any

class ApprovalService:
    async def request_approval_async(self, agent: str, action: str, context: Dict[str, Any]) -> bool:
        """Asynchronous approval request (for future frontend integration)"""
        print(f"\n🔔 ASYNC HUMAN APPROVAL REQUIRED 🔔")
        print(f"Agent: {agent}\nAction: {action}\nContext: {json.dumps(context, indent=2)}")
        # In real implementation, this would await frontend response
        return True  # Simulate approval for now
    
    def request_approval_sync(self, agent: str, action: str, context: Dict[str, Any]) -> bool:
        """Synchronous approval request for CLI-based workflow"""
        print(f"\n🔔 HUMAN APPROVAL REQUIRED 🔔")
        print(f"Agent: {agent}\nAction: {action}")
        print("Context summary:")
        for key, value in context.items():
            print(f"- {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
        return input("\nApprove this action? (y/n): ").lower() == 'y'
