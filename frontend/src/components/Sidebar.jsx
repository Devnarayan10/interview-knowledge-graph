import { NavLink } from 'react-router-dom';
import {
  Brain, Briefcase, ClipboardCheck, Database, GitCompare, HelpCircle, Info, LayoutDashboard,
  MessagesSquare, Share2, Target, Users, X,
} from 'lucide-react';

const NAV = [
  ['/', 'Dashboard', LayoutDashboard], ['/candidates', 'Candidates', Users], ['/compare', 'Compare', GitCompare],
  ['/interviews', 'Interviews', MessagesSquare], ['/questions', 'Questions', HelpCircle], ['/skills', 'Skills', Brain],
  ['/roles', 'Roles', Briefcase], ['/graph', 'Knowledge Graph', Share2], ['/evaluation', 'Evaluation', ClipboardCheck],
  ['/recommendations', 'Recommendations', Target], ['/database', 'Database & NoSQL', Database], ['/about', 'About', Info],
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-slate-900/50 lg:hidden" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-slate-900 text-slate-200 transition lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between px-5 py-5">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-indigo-500 p-2"><Share2 size={18} className="text-white" /></div>
            <div>
              <div className="text-sm font-bold text-white">Interview KG</div>
              <div className="text-[11px] text-slate-400">Neo4j + MongoDB</div>
            </div>
          </div>
          <button className="lg:hidden" onClick={onClose}><X size={18} /></button>
        </div>
        <nav className="space-y-1 px-3">
          {NAV.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={onClose}
              className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${isActive ? 'bg-indigo-600 text-white' : 'text-slate-300 hover:bg-slate-800'}`}>
              <Icon size={17} /> {label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}