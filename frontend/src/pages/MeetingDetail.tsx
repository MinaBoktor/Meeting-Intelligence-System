import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Users, Calendar, BrainCircuit, FileText } from 'lucide-react';

export default function MeetingDetail() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/meetings/${id}`)
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-8 text-gray-500">Loading meeting...</div>;
  if (!data) return <div className="p-8 text-red-500">Meeting not found.</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto h-[calc(100vh-64px)] flex flex-col">
      <div className="mb-6">
        <Link to="/meetings" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Meetings
        </Link>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">{data.title}</h1>
            <div className="flex items-center space-x-6 mt-3 text-sm text-gray-600">
              <div className="flex items-center bg-gray-100 px-2.5 py-1 rounded-md border border-gray-200">
                <Calendar className="w-4 h-4 mr-2 text-gray-500" />
                <span className="font-medium">{data.date || data.created_at?.substring(0, 10)}</span>
              </div>
              <div className="flex items-center bg-gray-100 px-2.5 py-1 rounded-md border border-gray-200">
                <Users className="w-4 h-4 mr-2 text-gray-500" />
                <span className="font-medium">
                  {(() => {
                    try {
                      return JSON.parse(data.participants).join(", ");
                    } catch (e) {
                      return "Unknown";
                    }
                  })()}
                </span>
              </div>
              <div className="flex items-center bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200 text-blue-700">
                <BrainCircuit className="w-4 h-4 mr-2" />
                <span className="font-medium capitalize">{data.processing_status.replace('_', ' ')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center">
          <FileText className="w-5 h-5 text-gray-500 mr-2" />
          <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wider">Original Transcript</h2>
        </div>
        <div className="flex-1 overflow-auto p-6 bg-gray-50">
          <pre className="text-sm text-gray-800 font-mono whitespace-pre-wrap leading-relaxed max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-sm border border-gray-100">
            {data.transcript}
          </pre>
        </div>
      </div>
    </div>
  );
}

