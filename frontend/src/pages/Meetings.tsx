import React, { useEffect, useState } from 'react';
import { Users as UsersIcon, Calendar, CheckSquare, BrainCircuit } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Meetings() {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/meetings')
      .then(res => res.json())
      .then(data => setMeetings(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-gray-500">Loading meetings...</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Meetings</h1>
          <p className="text-gray-500 mt-1 text-sm">Meeting transcripts ingested into organizational memory.</p>
        </div>
        <Link to="/new" className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm">
          + New Meeting
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {meetings.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-500">
            No meetings have been analyzed yet.
          </div>
        ) : (
          meetings.map((m: any, i: number) => (
            <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col md:flex-row md:items-center justify-between hover:border-blue-200 transition-colors">
              <div className="flex-1 mb-4 md:mb-0">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900 tracking-tight">{m.title}</h3>
                  <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full border border-gray-200">
                    {m.source}
                  </span>
                </div>
                
                <div className="flex items-center space-x-6 text-sm text-gray-500">
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1.5" />
                    {m.date || m.created_at?.substring(0, 10)}
                  </div>
                  <div className="flex items-center">
                    <UsersIcon className="w-4 h-4 mr-1.5" />
                    {(() => {
                      try {
                        const parts = JSON.parse(m.participants);
                        return parts.join(", ");
                      } catch (e) {
                        return "Unknown";
                      }
                    })()}
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col md:items-end space-y-2 border-t md:border-t-0 md:border-l border-gray-100 pt-4 md:pt-0 md:pl-6">
                <div className="text-sm font-medium text-gray-900 flex items-center">
                  <BrainCircuit className="w-4 h-4 text-purple-500 mr-2" />
                  Processed by AI
                </div>
                {/* For a true V1, we would aggregate the counts here via SQL */}
                <div className="text-sm text-gray-500">
                  See Decisions and Commitments
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
