import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function DecisionDetail() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch(`/api/decisions/${id}`)
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, [id]);

  if (!data) return <div className="p-8 text-gray-500">Loading decision...</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <Link to="/decisions" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-6 font-medium">
        <ArrowLeft className="w-4 h-4 mr-1" /> Back to Timeline
      </Link>
      
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-2">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{data.meeting_date}</span>
          <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full font-medium flex items-center">
            <CheckCircle2 className="w-3 h-3 mr-1" /> {data.status}
          </span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">{data.title}</h1>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-200">
          <div className="p-6 bg-gray-50">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Previous Value</h3>
            <p className="text-lg text-gray-500 line-through">{data.previous_value || 'None'}</p>
          </div>
          <div className="p-6 bg-blue-50">
            <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-2">Current Value</h3>
            <p className="text-xl font-semibold text-blue-900">{data.current_value}</p>
          </div>
        </div>
        
        {data.reason && (
          <div className="p-6 border-t border-gray-200">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Reason for Change</h3>
            <p className="text-gray-900 font-medium">{data.reason}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Historical Evidence</h2>
          {data.evidence && data.evidence.length > 0 ? (
            <div className="space-y-3">
              {data.evidence.map((ev: any, idx: number) => (
                <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-sm text-gray-700 italic">
                  "{ev.excerpt}"
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No historical evidence linked.</p>
          )}
        </div>
        
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Related Commitments</h2>
          {data.commitments && data.commitments.length > 0 ? (
            <div className="space-y-3">
              {data.commitments.map((com: any, idx: number) => (
                <div key={idx} className="p-4 bg-white rounded-lg border border-gray-200 flex justify-between items-start">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{com.task}</p>
                    <p className="text-xs text-gray-500 mt-1">Owner: {com.owner} • Due: {com.deadline}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    com.status === 'Completed' ? 'bg-green-100 text-green-800' :
                    com.status === 'At risk' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {com.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No commitments created from this decision.</p>
          )}
        </div>
      </div>
    </div>
  );
}

