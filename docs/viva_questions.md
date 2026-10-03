\# Viva questions and answers



\*\*Why Neo4j?\*\* The data is about relationships: candidate–question–skill–role. Neo4j stores relationships directly, so multi-hop queries are traversals rather than costly joins.



\*\*Why MongoDB?\*\* Interview sessions are semi-structured (transcripts, timelines, variable metadata). Documents hold them together without a fixed schema.



\*\*Why two NoSQL databases?\*\* Polyglot persistence: each database handles the workload it is best at, and FastAPI combines them.



\*\*What is a graph database?\*\* A database that stores nodes, relationships and properties, and queries by traversing relationships.



\*\*What is a node?\*\* An entity, such as a Candidate or Skill. \*\*A relationship?\*\* A directed, typed connection between two nodes, such as `(Candidate)-\[:HAS\_SKILL]->(Skill)`. \*\*A property?\*\* A key-value attribute on a node or relationship, such as `score`.



\*\*Why MERGE?\*\* It creates a node or relationship only if it does not exist, so seeding twice does not create duplicates.



\*\*Why constraints?\*\* Uniqueness constraints guarantee one node per id, make MERGE safe, and automatically create an index.



\*\*Why indexes?\*\* They let the database find nodes/documents without scanning everything (Neo4j property indexes, MongoDB B-tree indexes).



\*\*What is aggregation?\*\* Combining many records into summaries: Cypher `count/avg/collect`, MongoDB pipelines (`$group`, `$unwind`).



\*\*What is embedding? Referencing?\*\* Embedding nests related data inside one document (qa inside an interview). Referencing stores an id that points to another entity (candidate\_id).



\*\*Why MongoDB for transcripts?\*\* Variable size and shape, always read as a whole, no joins needed. \*\*Why Neo4j for relationships?\*\* Fast traversal over skill/role/question connections.



\*\*What is graph traversal?\*\* Following relationships from a start node, for example Candidate → Answer → Question → Skill.



\*\*What is PageRank?\*\* An algorithm that scores nodes by the importance of the nodes pointing to them; here it ranks skills. \*\*Louvain?\*\* A community-detection algorithm that groups densely connected nodes (skills tested together). \*\*Node Similarity?\*\* Compares nodes by shared neighbours (Jaccard), here candidates by shared skills.



\*\*How does candidate evaluation work?\*\* A fixed formula over answer scores (weighted by difficulty), answer length, behavioural answers and role-skill coverage. It is explainable, deterministic and uses no LLM.



\*\*How does skill-gap analysis work?\*\* Required skills of a role minus the candidate's `HAS\_SKILL` skills give the missing set; matched/required gives coverage %.



\*\*How does role recommendation work?\*\* Coverage % is computed for every role and sorted. It is labelled system-generated compatibility, not a hiring decision.



\*\*How does React talk to the databases?\*\* It never does. React calls FastAPI over HTTP/JSON; FastAPI uses the Neo4j Bolt driver and PyMongo.



\*\*How does FastAPI talk to Neo4j? MongoDB?\*\* `neo4j` driver with parameterised Cypher over Bolt (port 7687); `pymongo` over the MongoDB wire protocol (27017).



\*\*What if MongoDB is unavailable?\*\* Mongo-backed endpoints return HTTP 503; the dashboard and profile pages degrade gracefully, and graph endpoints keep working.



\*\*What if Neo4j is unavailable?\*\* Graph-backed endpoints return HTTP 503; `/health` reports it; MongoDB-only endpoints (interview list, `/analytics/mongo`) still work.



\*\*How does Docker help?\*\* One command starts four reproducible services with fixed versions, health checks, a private network and persistent volumes.

