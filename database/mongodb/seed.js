// =============================================================================
// MongoDB Initialization Script
// Runs automatically on first container startup via docker-entrypoint-initdb.d
// Full seed data populated by backend seed module (Phase 4)
// =============================================================================

db = db.getSiblingDB('interview_db');

db.createCollection('raw_interviews');
db.createCollection('emotion_logs');

db.raw_interviews.createIndex({ candidate_id: 1 });
db.raw_interviews.createIndex({ _id: 1 });
db.emotion_logs.createIndex({ interview_id: 1 });
db.emotion_logs.createIndex({ timestamp_sec: 1 });

print('MongoDB collections and indexes initialized for interview_db');
