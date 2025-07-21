// frontend/src/components/ApprovalModal.js
import React from 'react';

const ApprovalModal = ({ request, onDecision }) => (
  <div className="approval-modal">
    <h3>Approval Required: {request.agent}</h3>
    <p>Action: {request.action}</p>
    <div className="context">
      {Object.entries(request.context).map(([key, value]) => (
        <p key={key}><strong>{key}:</strong> {value}</p>
      ))}
    </div>
    <div className="actions">
      <button onClick={() => onDecision(true)}>Approve</button>
      <button onClick={() => onDecision(false)}>Reject</button>
    </div>
  </div>
);
