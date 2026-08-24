import React, { useEffect, useState } from 'react';
import { ArrowRight, AlertTriangle, CheckCircle2, FileText, CheckSquare, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Overview() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/dashboard')
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-gray-500">Loading overview...</div>;
  if (!data) return <div className="p-8 text-red-500">Failed to load overview data.</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-900 mb-8 tracking-tight">Overview</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[
          { label: 'Total Decisions', value: data.metrics.decisions, icon: FileText },
          { label: 'Requires Review', value: data.metrics.decisions_requiring_review, icon: AlertTriangle, alert: data.metrics.decisions_requiring_review > 0 },
          { label: 'Active Commitments', value: data.metrics.active_commitments, icon: CheckSquare },
          { label: 'Overdue', value: data.metrics.overdue_commitments, icon: Settings, alert: data.metrics.overdue_commitments > 0 },
        ].map((stat, i) => (
          <div key={i} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between h-32">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">{stat.label}</span>
              <stat.icon className={`w-5 h-5 ${stat.alert ? 'text-amber-500' : 'text-gray-400'}`} />
            </div>
            <span className={`text-3xl font-semibold ${stat.alert ? 'text-amber-600' : 'text-gray-900'}`}>{stat.value}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <div className="flex justify-between items-end mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Decisions</h2>
            <Link to="/decisions" className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center">
              View timeline <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Decision</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Value</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.recent_decisions.length === 0 ? (
                  <tr><td colSpan={4} className="px-6 py-8 text-center text-sm text-gray-500">No recent decisions</td></tr>
                ) : (
                  data.recent_decisions.map((item: any, i: number) => (
                    <tr key={i} className="hover:bg-gray-50 transition-colors cursor-pointer" onClick={() => window.location.href = `/decisions/${item.id}`}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.title}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.current_value}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                          item.status === 'Approved' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}>
                          {item.status === 'Approved' ? <CheckCircle2 className="w-3 h-3 mr-1" /> : <AlertTriangle className="w-3 h-3 mr-1" />}
                          {item.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.created_at.substring(0, 10)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
        
        <div>
          <div className="flex justify-between items-end mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Needs Attention</h2>
            <Link to="/decisions/inbox" className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center">
              Go to inbox <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
          
          <div className="space-y-4">
            {data.needs_attention.length === 0 ? (
              <div className="bg-white p-6 rounded-xl border border-gray-200 text-center text-gray-500 text-sm shadow-sm">
                Inbox Zero! All clear.
              </div>
            ) : (
              data.needs_attention.map((item: any, i: number) => (
                <Link key={i} to={`/decisions/${item.id}`} className="block bg-white p-5 rounded-xl border border-amber-200 shadow-sm hover:border-amber-400 transition-colors">
                  <div className="flex items-center mb-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 mr-2" />
                    <span className="text-xs font-bold text-amber-800 uppercase tracking-wider">Approval required</span>
                  </div>
                  <h3 className="text-base font-semibold text-gray-900 mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-600 line-clamp-2">{item.reason}</p>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
