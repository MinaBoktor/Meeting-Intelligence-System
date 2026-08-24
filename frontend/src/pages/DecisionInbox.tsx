import React, { useEffect, useState } from 'react';
import { AlertTriangle, Check, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function DecisionInbox() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchInbox = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/pending_decisions');
      if (!res.ok) throw new Error('Failed to fetch inbox');
      const json = await res.json();
      if (json && json.length > 0) {
        setData(json[0]);
      } else {
        setData(null);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInbox();
  }, []);

  const handleApprove = async () => {
    if (!data) return;
    try {
      const res = await fetch('/api/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: data.thread_id, approved: true })
      });
      if (res.ok) {
        setData(null);
        navigate('/decisions');
      } else {
        throw new Error('Failed to approve');
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) return <div className="p-8 text-gray-500">Loading inbox...</div>;
  if (error) return <div className="p-8 text-red-500">{error}</div>;
  if (!data) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6 tracking-tight">Decision Inbox</h1>
        <div className="bg-white p-12 text-center rounded-lg border border-gray-200 shadow-sm">
          <Check className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900">Inbox Zero</h2>
          <p className="text-gray-500 mt-2">No pending decisions require your review.</p>
        </div>
      </div>
    );
  }

  const conflict = data.conflicts?.[0];
  const decision = data.decisions?.[0];
  const item = conflict || decision;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Decision Review</h1>
          <p className="text-gray-500 mt-1 text-sm">Review AI-detected organizational changes.</p>
        </div>
        <div className="text-sm font-medium text-gray-500 bg-gray-100 px-3 py-1 rounded-full border border-gray-200">
          Confidence: 96%
        </div>
      </div>

      <div className={`bg-white rounded-lg border shadow-sm overflow-hidden mb-6 ${conflict ? 'border-amber-200' : 'border-blue-200'}`}>
        <div className={`${conflict ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'} px-6 py-4 border-b flex items-center`}>
          <AlertTriangle className={`w-5 h-5 mr-3 ${conflict ? 'text-amber-600' : 'text-blue-600'}`} />
          <span className={`text-base font-semibold ${conflict ? 'text-amber-900' : 'text-blue-900'}`}>
            {conflict ? 'Decision Change Requires Review' : 'New Decision Requires Review'}
          </span>
        </div>
        
        <div className="p-6">
          <h2 className="text-xl font-medium text-gray-900 mb-6">{conflict ? conflict.new_decision : decision.decision}</h2>
          
          <div className="grid grid-cols-2 gap-8 mb-8">
            <div className="bg-gray-50 rounded-lg p-5 border border-gray-100 relative">
              <span className="absolute -top-3 left-4 bg-white px-2 text-xs font-bold text-gray-500 uppercase tracking-wider">Previous Decision</span>
              <p className={`text-lg font-medium text-gray-900 ${conflict ? 'line-through text-gray-500' : ''}`}>
                {conflict ? conflict.previous_decision : 'None'}
              </p>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-5 border border-blue-100 relative shadow-sm">
              <span className="absolute -top-3 left-4 bg-white px-2 text-xs font-bold text-blue-600 uppercase tracking-wider">New Decision</span>
              <p className="text-lg font-medium text-blue-900">{conflict ? conflict.new_decision : decision.decision}</p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Reason for Change</h3>
            <p className="text-gray-900 bg-gray-50 p-4 rounded-lg border border-gray-100 font-medium">
              {conflict ? conflict.reason : decision?.context}
            </p>
          </div>

          {conflict?.evidence && (
            <div className="mb-8">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Historical Evidence</h3>
              <div className="bg-gray-50 rounded-lg border border-gray-100 p-4">
                <div className="flex items-start">
                  <FileText className="w-4 h-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" />
                  <p className="text-sm text-gray-700 italic">"{conflict.evidence}"</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {data.clarification_question && (
        <div className="bg-white rounded-lg border border-purple-200 shadow-sm overflow-hidden mb-6">
           <div className="bg-purple-50 px-6 py-4 border-b border-purple-200 flex items-center">
            <span className="text-base font-semibold text-purple-900">🤖 AI Needs Clarification</span>
          </div>
          <div className="p-6">
            <p className="text-gray-700 mb-4">I found a commitment, but I couldn't determine all details.</p>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 mb-4">
              <p className="text-xs text-gray-500 uppercase font-bold mb-1">Commitment</p>
              <p className="font-medium text-gray-900 mb-3">{data.clarification_question.commitment}</p>
              <p className="text-xs text-gray-500 uppercase font-bold mb-1">Missing Information</p>
              <p className="font-medium text-red-600">{data.clarification_question.missing_info}</p>
            </div>
            
            <p className="font-medium text-gray-900 mb-4">{data.clarification_question.question}</p>
            <div className="space-y-2">
              {data.clarification_question.options.map((opt: string) => (
                <label key={opt} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                  <input 
                    type="radio" 
                    name="clarification" 
                    className="h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <span className="text-sm font-medium text-gray-900">{opt}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-end space-x-4">
        <button className="px-6 py-2.5 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors">
          Reject
        </button>
        <button 
          onClick={handleApprove}
          className="px-6 py-2.5 border border-transparent shadow-sm text-sm font-medium rounded-lg text-white bg-gray-900 hover:bg-black transition-colors"
        >
          Approve Change
        </button>
      </div>
    </div>
  );
}
