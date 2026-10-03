// =============================================================================
// Neo4j query pack (run in Neo4j Browser, http://localhost:7474). Each is a DA2 screenshot candidate.
// =============================================================================

// Q1 Graph overview: candidates, rounds and questions
MATCH (c:Candidate)-[:PARTICIPATES_IN]->(r:InterviewRound)-[:INCLUDES]->(q:Question)
RETURN c, r, q LIMIT 40;

// Q2 Node counts by label
MATCH (n) RETURN labels(n)[0] AS label, count(*) AS nodes ORDER BY nodes DESC;

// Q3 Relationship counts by type
MATCH ()-[r]->() RETURN type(r) AS relationship, count(*) AS total ORDER BY total DESC;

// Q4 Strongest candidates for a skill (change the skill name)
MATCH (c:Candidate)-[:ANSWERED]->(a:Answer)-[:DEMONSTRATES]->(s:Skill)
WHERE toLower(s.name) = toLower('Python')
WITH c, avg(a.score) AS avg_score, count(a) AS evidence
RETURN c.candidate_id, c.name, round(avg_score, 2) AS avg_score, evidence
ORDER BY avg_score DESC, evidence DESC LIMIT 10;

// Q5 Most difficult questions (lowest average answer score)
MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
WITH q, avg(a.score) AS avg_score, count(a) AS answers
RETURN q.question_id, q.difficulty, left(q.text, 80) AS question, round(avg_score, 2) AS avg_score
ORDER BY avg_score ASC LIMIT 10;

// Q6 Skill co-occurrence (skills tested together by the same question)
MATCH (q:Question)-[:TESTS_SKILL]->(a:Skill), (q)-[:TESTS_SKILL]->(b:Skill)
WHERE a.skill_id < b.skill_id
RETURN a.name AS skill_a, b.name AS skill_b, count(DISTINCT q) AS together
ORDER BY together DESC LIMIT 15;

// Q7 Skills required for each role (weighted)
MATCH (s:Skill)-[rel:REQUIRED_FOR]->(r:Role)
WITH r, s, rel ORDER BY rel.weight DESC
RETURN r.title AS role, collect(s.name + ' (' + rel.weight + ')') AS required_skills
ORDER BY role;

// Q8 Skill gap for the first candidate against their interviewed role(s)
MATCH (c:Candidate) WITH c ORDER BY c.candidate_id LIMIT 1
MATCH (c)-[:INTERVIEWED_FOR]->(r:Role)
MATCH (s:Skill)-[:REQUIRED_FOR]->(r)
WITH c, r, collect(DISTINCT s) AS required
WITH c, r, required, [s IN required WHERE (c)-[:HAS_SKILL]->(s) | s.name] AS matched,
     [s IN required WHERE NOT (c)-[:HAS_SKILL]->(s) | s.name] AS missing
RETURN c.candidate_id, r.title AS role, matched, missing,
       round(100.0 * size(matched) / size(required), 1) AS coverage_pct;

// Q9 Important skills (most connected: candidates + questions + roles)
MATCH (s:Skill)
OPTIONAL MATCH (c:Candidate)-[:HAS_SKILL]->(s)
WITH s, count(DISTINCT c) AS candidates
OPTIONAL MATCH (q:Question)-[:TESTS_SKILL]->(s)
WITH s, candidates, count(DISTINCT q) AS questions
OPTIONAL MATCH (s)-[:REQUIRED_FOR]->(r:Role)
RETURN s.name, candidates, questions, count(DISTINCT r) AS roles,
       candidates + questions + count(DISTINCT r) AS importance
ORDER BY importance DESC LIMIT 10;

// Q10 Candidate similarity by shared skills (Jaccard)
MATCH (a:Candidate)-[:HAS_SKILL]->(s:Skill)<-[:HAS_SKILL]-(b:Candidate)
WHERE a.candidate_id < b.candidate_id
WITH a, b, collect(s.name) AS shared, count(s) AS inter
OPTIONAL MATCH (a)-[:HAS_SKILL]->(sa:Skill) WITH a, b, shared, inter, count(sa) AS na
OPTIONAL MATCH (b)-[:HAS_SKILL]->(sb:Skill)
WITH a, b, shared, inter, na, count(sb) AS nb
RETURN a.candidate_id, b.candidate_id, shared, round(100.0 * inter / (na + nb - inter), 1) AS similarity_pct
ORDER BY similarity_pct DESC LIMIT 10;

// Q11 Role-skill analysis (required skills, questions, mean score)
MATCH (r:Role)
OPTIONAL MATCH (s:Skill)-[:REQUIRED_FOR]->(r)
WITH r, count(DISTINCT s) AS required_skills
OPTIONAL MATCH (a:Answer)-[:IN_RESPONSE_TO]->(:Question)-[:FOR_ROLE]->(r)
RETURN r.title, required_skills, count(a) AS answers, round(avg(a.score), 2) AS avg_score ORDER BY avg_score DESC;

// Q12 Company-question analysis (returns rows only if the dataset has a company column)
MATCH (c:Candidate)-[:APPLIED_TO]->(co:Company)
MATCH (c)-[:ANSWERED]->(:Answer)-[:IN_RESPONSE_TO]->(q:Question)
RETURN co.name, q.category, count(*) AS asked ORDER BY asked DESC LIMIT 20;

// Q13 Full candidate evaluation inputs (first candidate)
MATCH (c:Candidate) WITH c ORDER BY c.candidate_id LIMIT 1
MATCH (c)-[:ANSWERED]->(a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
OPTIONAL MATCH (a)-[:DEMONSTRATES]->(s:Skill)
RETURN c.name, q.category, q.difficulty, a.score, collect(DISTINCT s.name) AS skills ORDER BY q.difficulty;

// Q14 Interview performance per round
MATCH (c:Candidate)-[:PARTICIPATES_IN]->(r:InterviewRound)
MATCH (a:Answer {round_id: r.round_id})
RETURN c.candidate_id, r.round_label, r.date, count(a) AS answers, round(avg(a.score), 2) AS avg_score
ORDER BY avg_score DESC LIMIT 15;