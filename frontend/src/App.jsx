import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import About from './pages/About';
import CandidateProfile from './pages/CandidateProfile';
import Candidates from './pages/Candidates';
import CompareCandidates from './pages/CompareCandidates';
import Dashboard from './pages/Dashboard';
import Database from './pages/Database';
import Evaluation from './pages/Evaluation';
import Interviews from './pages/Interviews';
import KnowledgeGraph from './pages/KnowledgeGraph';
import Questions from './pages/Questions';
import Recommendations from './pages/Recommendations';
import Roles from './pages/Roles';
import Skills from './pages/Skills';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/candidates" element={<Candidates />} />
          <Route path="/candidates/:id" element={<CandidateProfile />} />
          <Route path="/compare" element={<CompareCandidates />} />
          <Route path="/interviews" element={<Interviews />} />
          <Route path="/questions" element={<Questions />} />

          <Route path="/roles" element={<Roles />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/graph" element={<KnowledgeGraph />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/database" element={<Database />} />
          <Route path="/about" element={<About />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
