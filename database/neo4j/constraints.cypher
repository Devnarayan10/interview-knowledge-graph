// =============================================================================
// Neo4j Constraints and Indexes
// Run on first startup to ensure unique node identifiers
// =============================================================================

CREATE CONSTRAINT candidate_id_unique IF NOT EXISTS
FOR (c:Candidate) REQUIRE c.candidate_id IS UNIQUE;

CREATE CONSTRAINT question_id_unique IF NOT EXISTS
FOR (q:Question) REQUIRE q.question_id IS UNIQUE;

CREATE CONSTRAINT skill_id_unique IF NOT EXISTS
FOR (s:Skill) REQUIRE s.skill_id IS UNIQUE;

CREATE CONSTRAINT role_id_unique IF NOT EXISTS
FOR (r:Role) REQUIRE r.role_id IS UNIQUE;

CREATE CONSTRAINT company_id_unique IF NOT EXISTS
FOR (co:Company) REQUIRE co.company_id IS UNIQUE;

CREATE CONSTRAINT answer_id_unique IF NOT EXISTS
FOR (a:Answer) REQUIRE a.answer_id IS UNIQUE;

CREATE CONSTRAINT emotion_id_unique IF NOT EXISTS
FOR (e:Emotion) REQUIRE e.emotion_id IS UNIQUE;

CREATE CONSTRAINT feedback_id_unique IF NOT EXISTS
FOR (f:Feedback) REQUIRE f.feedback_id IS UNIQUE;

CREATE CONSTRAINT tech_id_unique IF NOT EXISTS
FOR (t:Technology) REQUIRE t.tech_id IS UNIQUE;

CREATE CONSTRAINT round_id_unique IF NOT EXISTS
FOR (ir:InterviewRound) REQUIRE ir.round_id IS UNIQUE;

// Performance indexes
CREATE INDEX candidate_name_idx IF NOT EXISTS FOR (c:Candidate) ON (c.name);
CREATE INDEX skill_name_idx IF NOT EXISTS FOR (s:Skill) ON (s.name);
CREATE INDEX question_category_idx IF NOT EXISTS FOR (q:Question) ON (q.category);
CREATE INDEX role_title_idx IF NOT EXISTS FOR (r:Role) ON (r.title);
CREATE INDEX company_name_idx IF NOT EXISTS FOR (co:Company) ON (co.name);
