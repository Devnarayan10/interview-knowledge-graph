\# DA2 evidence checklist



Run `docker compose up -d --build`, then `docker compose exec backend python seed\_database.py`.



1\. Docker containers: `docker compose ps` (4 services healthy)

2\. Neo4j Browser graph: `MATCH p=()-\[]->() RETURN p LIMIT 50` (http://localhost:7474)

3\. Neo4j node counts: queries.cypher Q2

4\. Neo4j relationship counts: Q3

5\. MongoDB collections: `docker compose exec mongodb mongosh interview\_db --eval "db.getCollectionNames()"`

6\. MongoDB documents: `db.raw\_interviews.findOne()` and `db.emotion\_logs.findOne()`

7\. Dashboard page (counts + charts)

8\. Candidate list page

9\. Candidate profile page

10\. CRUD Create (new candidate modal, then the row in the table)

11\. CRUD Read (profile or detail view)

12\. CRUD Update (edit modal, updated row)

13\. CRUD Delete (confirmation dialog, row gone)

14\. Same four CRUD shots for Questions or Interviews (MongoDB)

15–29. Cypher Q4–Q17 results (one screenshot per query; at least 10 needed)

30\. GDS PageRank / Louvain / Node Similarity (Q18–Q20) or the Skills page GDS panel

31\. MongoDB queries M1–M11 (at least 6 screenshots)

32\. Neo4j constraints: `SHOW CONSTRAINTS`; indexes: `SHOW INDEXES`

33\. MongoDB indexes: `db.raw\_interviews.getIndexes()`, plus the Database \& NoSQL page index section

34\. MongoDB aggregation output (M4, M7, M8) and the live aggregations on the Database page

35\. Application–database connectivity: header badges, `/health` JSON, Database page connected badges

36\. Knowledge Graph page (full graph, a selected node, a candidate subgraph)

37\. Evaluation page and Recommendations page (skill gap)

38\. `python -m pytest -q` and `python validate\_system.py` output

39\. Swagger UI (`http://localhost:8000/docs`)

