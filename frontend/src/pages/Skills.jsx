import { useState } from 'react';
import { Search } from 'lucide-react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Async, PageHeader } from '../components/ui';

export default function Skills() {
  const [q, setQ] = useState('');
  const state = useApi(() => api.skills(), []);

  return (
    <>
      <PageHeader
        title="Skills"
        subtitle="Skills available in the Interview Knowledge Graph."
      />

      <div className="mb-4 relative max-w-xl">
        <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
        <input
          className="input pl-9"
          placeholder="Search skills..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      <Async state={state}>
        {(data) => {
          const raw = Array.isArray(data) ? data : (data?.items || []);

          const skills = raw
            .map((item) => item?.s || item)
            .filter(Boolean)
            .filter((skill) => {
              const name =
                skill.name ||
                skill.skill_name ||
                skill.skill_id ||
                '';

              return name.toLowerCase().includes(q.toLowerCase());
            });

          return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {skills.map((skill, index) => {
                const name =
                  skill.name ||
                  skill.skill_name ||
                  skill.skill_id ||
                  `Skill ${index + 1}`;

                return (
                  <div
                    key={skill.skill_id || skill.id || name}
                    className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                  >
                    <div className="font-semibold text-slate-800">
                      {name}
                    </div>

                    {skill.description && (
                      <div className="mt-1 text-sm text-slate-500">
                        {skill.description}
                      </div>
                    )}

                    {skill.skill_id && skill.skill_id !== name && (
                      <div className="mt-2 text-xs text-slate-400">
                        ID: {skill.skill_id}
                      </div>
                    )}
                  </div>
                );
              })}

              {skills.length === 0 && (
                <div className="col-span-full text-sm text-slate-500">
                  No skills found.
                </div>
              )}
            </div>
          );
        }}
      </Async>
    </>
  );
}
