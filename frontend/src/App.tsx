import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate, Link } from 'react-router-dom';
import { LayoutDashboard, Users, Inbox, Clock, CheckSquare } from 'lucide-react';
import Overview from './pages/Overview';
import Meetings from './pages/Meetings';
import DecisionInbox from './pages/DecisionInbox';
import DecisionTimeline from './pages/DecisionTimeline';
import DecisionDetail from './pages/DecisionDetail';
import Execution from './pages/Execution';
import NewMeeting from './pages/NewMeeting';
import MeetingDetail from './pages/MeetingDetail';
import Memory from './pages/Memory';

const Sidebar = () => {
  const navItems = [
    { name: 'Overview', path: '/overview', icon: LayoutDashboard },
    { name: 'Meetings', path: '/meetings', icon: Users },
    { name: 'Decision Inbox', path: '/decisions/inbox', icon: Inbox },
    { name: 'Decision Timeline', path: '/decisions', icon: Clock },
    { name: 'Execution', path: '/execution', icon: CheckSquare },
    { name: 'Memory', path: '/memory', icon: LayoutDashboard }, // using LayoutDashboard for now
  ];

  return (
    <div className="w-64 bg-white border-r border-gray-200 h-screen flex flex-col">
      <div className="h-16 flex items-center justify-between px-6 border-b border-gray-200">
        <span className="font-bold text-lg text-gray-900 tracking-tight">Decisions.ai</span>
      </div>
      
      <div className="px-4 py-4 border-b border-gray-100">
        <Link to="/new" className="w-full flex items-center justify-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors">
          + New Meeting
        </Link>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            end={item.path === '/decisions' || item.path === '/meetings' || item.path === '/overview'}
            className={({ isActive }) =>
              `flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            <item.icon className="mr-3 flex-shrink-0 h-4 w-4" aria-hidden="true" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-sm font-medium text-gray-600">JS</div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-700 text-sm">Jane Smith</p>
            <p className="text-xs font-medium text-gray-500 text-xs">Director of Prod</p>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/new" element={<NewMeeting />} />
            <Route path="/meetings" element={<Meetings />} />
            <Route path="/meetings/:id" element={<MeetingDetail />} />
            <Route path="/decisions/inbox" element={<DecisionInbox />} />
            <Route path="/decisions/:id" element={<DecisionDetail />} />
            <Route path="/decisions" element={<DecisionTimeline />} />
            <Route path="/execution" element={<Execution />} />
            <Route path="/memory" element={<Memory />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
