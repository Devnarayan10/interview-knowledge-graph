import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

export default function Layout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="min-w-0 flex-1">
        <Header onMenu={() => setOpen(true)} />
        <main className="mx-auto max-w-[1500px] p-4 lg:p-8"><Outlet /></main>
      </div>
    </div>
  );
}