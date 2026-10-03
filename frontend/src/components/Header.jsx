import { useEffect } from 'react';
import { Menu } from 'lucide-react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Badge } from './ui';

export default function Header({ onMenu }) {
  const { data, error, reload } = useApi(api.health, []);
  useEffect(() => {
    const t = setInterval(reload, 30000);
    return () => clearInterval(t);
  }, [reload]);
  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur lg:px-8">
      <div className="flex items-center gap-3">
        <button className="lg:hidden" onClick={onMenu}><Menu /></button>
        <div className="text-sm font-semibold text-slate-700">Interview Knowledge Graph for AI-Powered Candidate Evaluation</div>
      </div>
      <div className="flex items-center gap-2">
        <Badge tone={error ? 'rose' : 'emerald'}>{error ? 'API offline' : 'API online'}</Badge>
        {data && <Badge tone={data.neo4j ? 'emerald' : 'rose'}>Neo4j</Badge>}
        {data && <Badge tone={data.mongodb ? 'emerald' : 'rose'}>MongoDB</Badge>}
      </div>
    </header>
  );
}