
 // =============================================================================
 // Neo4j DA2 Query Pack - Q1 to Q20
 // Project: NoSQL Interview Knowledge Graph for AI-Powered Candidate Evaluation
 // Run individual queries in Neo4j Browser: http://localhost:7474
 // =============================================================================

 // Q1 Graph overview: candidates, rounds and questions
 MATCH (c:Candidate)-[:PARTICIPATES_IN]->(r:InterviewRound)-[:INCLUDES]->(q:Question)
 RETURN c, r, q LIMIT 40;

 // Q2 Node counts by label
 MATCH (n)
 RETURN labels(n)[0] AS label, count(*) AS nodes
 ORDER BY nodes DESC;

 // Q3 Relationship counts by type
 MATCH ()-[r]->()
 RETURN type(r) AS relationship, count(*) AS total
 ORDER BY total DESC;

 // Q4 Strongest candidates for Python skill
 MATCH (c:Candidate)-[:ANSWERED]->(a:Answer)-[:DEMONSTRATES]->(s:Skill)
 WHERE toLower(s.name) = toLower('Python')
 WITH c, avg(a.score) AS avg_score, count(a) AS evidence
 RETURN c.candidate_id AS candidate_id, c.name AS candidate_name,
        round(avg_score, 2) AS avg_score, evidence
 ORDER BY avg_score DESC, evidence DESC LIMIT 10;

 // Q5 Most difficult questions by average answer score
 MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
 WITH q, avg(a.score) AS avg_score, count(a) AS answers
 RETURN q.question_id AS question_id, q.difficulty AS difficulty,
        left(q.text, 80) AS question,
        round(avg_score, 2) AS avg_score, answers
 ORDER BY avg_score ASC LIMIT 10;

 // Q6 Skill co-occurrence
 MATCH (q:Question)-[:TESTS_SKILL]->(a:Skill),
       (q)-[:TESTS_SKILL]->(b:Skill)
 WHERE a.skill_id < b.skill_id
 RETURN a.name AS skill_a, b.name AS skill_b,
        count(DISTINCT q) AS together
 ORDER BY together DESC LIMIT 15;

 // Q7 Skills required for each role with stored weights
 MATCH (s:Skill)-[rel:REQUIRED_FOR]->(r:Role)
 WITH r, s, rel ORDER BY rel.weight DESC
 RETURN r.title AS role,
        collect(s.name + ' (' + toString(rel.weight) + ')') AS required_skills
 ORDER BY role;

 // Q8 Candidate skill gap and coverage
 MATCH (c:Candidate)
 WITH c ORDER BY c.candidate_id LIMIT 1
 MATCH (c)-[:INTERVIEWED_FOR]->(r:Role)
 MATCH (s:Skill)-[:REQUIRED_FOR]->(r)
 WITH c, r, collect(DISTINCT s) AS required
 WITH c, r, required,
      [s IN required WHERE EXISTS {
          MATCH (c)-[:HAS_SKILL]->(s)
      } | s.name] AS matched,
      [s IN required WHERE NOT EXISTS {
          MATCH (c)-[:HAS_SKILL]->(s)
      } | s.name] AS missing
 RETURN c.candidate_id AS candidate_id, r.title AS role,
        matched, missing,
        round(100.0 * size(matched) / size(required), 1) AS coverage_pct;

 // Q9 Important skills by graph connections
 MATCH (s:Skill)
 OPTIONAL MATCH (c:Candidate)-[:HAS_SKILL]->(s)
 WITH s, count(DISTINCT c) AS candidates
 OPTIONAL MATCH (q:Question)-[:TESTS_SKILL]->(s)
 WITH s, candidates, count(DISTINCT q) AS questions
 OPTIONAL MATCH (s)-[:REQUIRED_FOR]->(r:Role)
 RETURN s.name AS skill, candidates, questions,
        count(DISTINCT r) AS roles,
        candidates + questions + count(DISTINCT r) AS importance
 ORDER BY importance DESC LIMIT 10;

 // Q10 Candidate similarity using Jaccard
 MATCH (a:Candidate)-[:HAS_SKILL]->(s:Skill)<-[:HAS_SKILL]-(b:Candidate)
 WHERE a.candidate_id < b.candidate_id
 WITH a, b, collect(s.name) AS shared, count(s) AS inter
 OPTIONAL MATCH (a)-[:HAS_SKILL]->(sa:Skill)
 WITH a, b, shared, inter, count(sa) AS na
 OPTIONAL MATCH (b)-[:HAS_SKILL]->(sb:Skill)
 WITH a, b, shared, inter, na, count(sb) AS nb
 RETURN a.candidate_id AS candidate_1,
        b.candidate_id AS candidate_2, shared,
        round(100.0 * inter / (na + nb - inter), 1) AS similarity_pct
 ORDER BY similarity_pct DESC LIMIT 10;

 // Q11 Role-skill analysis
 MATCH (r:Role)
 OPTIONAL MATCH (s:Skill)-[:REQUIRED_FOR]->(r)
 WITH r, count(DISTINCT s) AS required_skills
 OPTIONAL MATCH (a:Answer)-[:IN_RESPONSE_TO]->(:Question)-[:FOR_ROLE]->(r)
 RETURN r.title AS role, required_skills,
        count(a) AS answers, round(avg(a.score), 2) AS avg_score
 ORDER BY avg_score DESC;

 // Q12 Company-role-question analysis
 // Uses demo Company nodes and actual OFFERED_BY relationships.
 // Does not claim candidates applied to these companies.
 MATCH (r:Role)-[:OFFERED_BY]->(co:Company)
 OPTIONAL MATCH (q:Question)-[:FOR_ROLE]->(r)
 RETURN co.name AS company, r.title AS role,
        count(DISTINCT q) AS questions
 ORDER BY company;

 // Q13 Candidate evaluation inputs
 MATCH (c:Candidate)
 WITH c ORDER BY c.candidate_id LIMIT 1
 MATCH (c)-[:ANSWERED]->(a:Answer)-[:IN_RESPONSE_TO]->(q:Question)
 OPTIONAL MATCH (a)-[:DEMONSTRATES]->(s:Skill)
 RETURN c.name AS candidate_name, q.category AS category,
        q.difficulty AS difficulty, a.score AS score,
        collect(DISTINCT s.name) AS skills
 ORDER BY difficulty;

 // Q14 Interview performance per round
 MATCH (c:Candidate)-[:PARTICIPATES_IN]->(r:InterviewRound)
 MATCH (c)-[:ANSWERED]->(a:Answer {round_id: r.round_id})
 RETURN c.candidate_id AS candidate_id,
        r.round_label AS round_label,
        r.date AS interview_date,
        count(a) AS answers,
        round(avg(a.score), 2) AS avg_score
 ORDER BY avg_score DESC LIMIT 15;

 // Q15 Candidate interview history
 MATCH (c:Candidate)
 OPTIONAL MATCH (c)-[:PARTICIPATES_IN]->(r:InterviewRound)
 WITH c, count(DISTINCT r) AS interview_rounds
 OPTIONAL MATCH (c)-[:ANSWERED]->(a:Answer)
 RETURN c.candidate_id AS candidate_id,
        c.name AS candidate_name,
        interview_rounds,
        count(DISTINCT a) AS total_answers,
        round(avg(a.score), 2) AS avg_score
 ORDER BY interview_rounds DESC, avg_score DESC LIMIT 15;

 // Q16 Most frequently tested skills
 MATCH (s:Skill)<-[:TESTS_SKILL]-(q:Question)
 OPTIONAL MATCH (a:Answer)-[:IN_RESPONSE_TO]->(q)
 RETURN s.name AS skill,
        count(DISTINCT q) AS questions,
        count(DISTINCT a) AS answers,
        round(avg(a.score), 2) AS avg_score
 ORDER BY questions DESC, answers DESC LIMIT 15;

 // Q17 Candidates with missing required skills
 MATCH (c:Candidate)-[:INTERVIEWED_FOR]->(r:Role)
 MATCH (s:Skill)-[:REQUIRED_FOR]->(r)
 WITH c, r, collect(DISTINCT s) AS required
 WITH c, r, required,
      [s IN required WHERE NOT EXISTS {
          MATCH (c)-[:HAS_SKILL]->(s)
      } | s.name] AS missing
 RETURN c.candidate_id AS candidate_id,
        r.title AS role,
        size(missing) AS missing_count,
        missing AS missing_skills
 ORDER BY missing_count DESC, candidate_id LIMIT 15;

 // =============================================================================
 // Graph Data Science (GDS)
 // The following three queries use the in-memory projection ikg_da2.
 // Create it once per Neo4j/GDS session if it does not exist:
 //
 // CALL gds.graph.project(
 //   'ikg_da2',
 //   ['Candidate', 'Skill'],
 //   {HAS_SKILL: {orientation: 'UNDIRECTED'}}
 // );
 //
 // =============================================================================

 // Q18 PageRank: influential skills in candidate-skill network
 CALL gds.pageRank.stream('ikg_da2')
 YIELD nodeId, score
 WITH gds.util.asNode(nodeId) AS n, score
 WHERE n:Skill
 RETURN n.name AS skill,
        round(score, 3) AS page_rank
 ORDER BY page_rank DESC LIMIT 10;

 // Q19 Louvain: candidate communities
 CALL gds.louvain.stream('ikg_da2')
 YIELD nodeId, communityId
 WITH gds.util.asNode(nodeId) AS n, communityId
 WHERE n:Candidate
 RETURN communityId,
        count(n) AS candidates,
        collect(n.candidate_id) AS candidate_ids
 ORDER BY candidates DESC;

 // Q20 Node Similarity: candidate pairs sharing skills
 CALL gds.nodeSimilarity.stream('ikg_da2')
 YIELD node1, node2, similarity
 WITH gds.util.asNode(node1) AS a,
      gds.util.asNode(node2) AS b,
      similarity
 WHERE a:Candidate AND b:Candidate
 RETURN a.candidate_id AS candidate_1,
        b.candidate_id AS candidate_2,
        round(similarity * 100, 1) AS similarity_pct
 ORDER BY similarity_pct DESC LIMIT 10;
