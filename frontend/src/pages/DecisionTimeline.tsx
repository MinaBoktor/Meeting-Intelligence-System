import React, { useEffect, useState } from 'react';
import { Clock, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DecisionTimeline() {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/decisions')
      .then(res => res.json())
      .then(data => setDecisions(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-gray-500">Loading timeline...</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Decision Timeline</h1>
          <p className="text-gray-500 mt-1 text-sm">The organizational memory and evolution of past decisions.</p>
        </div>
      </div>

      <div className="space-y-12">
        {decisions.length === 0 ? (
          <div className="text-gray-500 text-center p-12 bg-white rounded-lg border border-gray-200">
            No decisions tracked yet.
          </div>
        ) : (
          decisions.map((d: any) => (
            <div key={d.id} className="relative">
              <Link to={`/decisions/${d.id}`} className="inline-block mb-6 hover:opacity-80 transition-opacity">
                <h2 className="text-xl font-bold text-gray-900 tracking-tight">{d.title}</h2>
              </Link>
              
              <div className="ml-4 space-y-6 border-l-2 border-gray-200 pb-2">
                {d.timeline.map((event: any, idx: number) => (
                  <div key={idx} className="relative pl-6">
                    <div className="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-blue-500 ring-4 ring-white" />
                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">{event.date}</span>
                      <span className="text-base font-semibold text-gray-900">{event.event}</span>
                      {event.detail && <p className="text-sm text-gray-600 mt-1">{event.detail}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
