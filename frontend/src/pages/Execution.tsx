import React, { useEffect, useState } from 'react';
import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Execution() {
  const [commitments, setCommitments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/commitments')
      .then(res => res.json())
      .then(data => setCommitments(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-gray-500">Loading execution...</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">Execution</h1>
        <p className="text-gray-500 mt-1 text-sm">Track commitments created from organizational decisions.</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Owner</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Task</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Deadline</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Source Decision</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {commitments.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  No commitments tracked yet.
                </td>
              </tr>
            ) : (
              commitments.map((c: any, i: number) => (
                <tr key={i} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <div className="flex items-center">
                      <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs mr-2">
                        {c.owner.charAt(0)}
                      </div>
                      {c.owner}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 font-medium">{c.task}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{c.deadline}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {c.decision_title ? (
                      <Link to={`/decisions/${c.decision_id}`} className="text-blue-600 hover:underline">
                        {c.decision_title.length > 30 ? c.decision_title.substring(0,30) + '...' : c.decision_title}
                      </Link>
                    ) : 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                      c.status === 'Completed' ? 'bg-green-50 text-green-700 border-green-200' :
                      c.status === 'At risk' ? 'bg-red-50 text-red-700 border-red-200' :
                      'bg-gray-50 text-gray-700 border-gray-200'
                    }`}>
                      {c.status === 'Completed' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                      {c.status === 'At risk' && <AlertCircle className="w-3 h-3 mr-1" />}
                      {c.status !== 'Completed' && c.status !== 'At risk' && <Clock className="w-3 h-3 mr-1" />}
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
