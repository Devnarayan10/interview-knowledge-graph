// MongoDB initialisation (runs once on a fresh volume via docker-entrypoint-initdb.d).
// Data itself is loaded by the backend seed (POST /api/seed or python seed_database.py).
db = db.getSiblingDB('interview_db');

db.createCollection('raw_interviews');
db.createCollection('emotion_logs');

['candidate_id', 'round_id', 'target_role', 'started_at'].forEach(f => db.raw_interviews.createIndex({ [f]: 1 }));
['candidate_id', 'interview_id', 'label', 'timestamp', 'confidence'].forEach(f => db.emotion_logs.createIndex({ [f]: 1 }));

print('MongoDB collections and indexes initialised for interview_db');