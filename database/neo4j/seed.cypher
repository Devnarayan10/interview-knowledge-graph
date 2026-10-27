// =============================================================================
// Neo4j Seed Data
// Full dataset will be populated via backend seed module (Phase 4)
// This file contains reference MERGE patterns used during seeding
// =============================================================================

// Example MERGE pattern (not executed standalone — used by seed_database.py):
//
// MERGE (c:Candidate {candidate_id: 'C001'})
// SET c.name = 'Aditi Rao',
//     c.email = 'aditi.rao@example.com',
//     c.experience_years = 2;
