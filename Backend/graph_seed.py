"""
Seed script for Neo4j AuraDB graph database.
Creates idempotent sample data for Careers, Skills, Courses, and Prerequisites.
Never deletes existing data; uses MERGE throughout.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CAREERS = [
    {
        "id": "c-fullstack",
        "title": "Full Stack Developer",
        "domain": "Web Engineering",
        "description": "Architects and implements end-to-end web applications, modern interactive user interfaces, and robust APIs.",
        "avg_salary_inr": "₹8 - ₹16 LPA (Fresher to 2 YOE)",
        "growth_rate": "High Demand across Indian startups and MNCs",
        "skills": [
            ("s-git", "critical"),
            ("s-js", "critical"),
            ("s-react", "critical"),
            ("s-html-css", "important"),
            ("s-ts", "important"),
            ("s-rest", "critical"),
            ("s-fastapi", "important"),
            ("s-sql", "critical"),
            ("s-postgres", "important"),
            ("s-docker", "important"),
            ("s-dsa", "critical"),
            ("s-redis", "nice_to_have"),
        ]
    },
    {
        "id": "c-backend",
        "title": "Backend & Distributed Systems Engineer",
        "domain": "Systems & Platform",
        "description": "Specializes in high-throughput backend services, data modeling, concurrency, and scalable distributed architectures.",
        "avg_salary_inr": "₹10 - ₹20 LPA",
        "growth_rate": "Very High (Fintech, E-commerce, SaaS)",
        "skills": [
            ("s-git", "critical"),
            ("s-python", "critical"),
            ("s-dsa", "critical"),
            ("s-linux", "important"),
            ("s-rest", "critical"),
            ("s-fastapi", "critical"),
            ("s-sql", "critical"),
            ("s-postgres", "critical"),
            ("s-redis", "important"),
            ("s-docker", "critical"),
            ("s-k8s", "important"),
            ("s-queues", "important"),
            ("s-microservices", "important"),
            ("s-neo4j", "nice_to_have"),
        ]
    },
    {
        "id": "c-ai-ml",
        "title": "AI & Machine Learning Engineer",
        "domain": "Artificial Intelligence",
        "description": "Builds and deploys predictive ML models, deep neural networks, and Generative AI / RAG knowledge-graph applications.",
        "avg_salary_inr": "₹12 - ₹24 LPA",
        "growth_rate": "Exponential (GenAI, LLMs, Agentic AI)",
        "skills": [
            ("s-git", "critical"),
            ("s-python", "critical"),
            ("s-dsa", "important"),
            ("s-numpy-pandas", "critical"),
            ("s-sklearn", "critical"),
            ("s-pytorch", "critical"),
            ("s-llm", "critical"),
            ("s-neo4j", "critical"),
            ("s-vectordb", "critical"),
            ("s-fastapi", "important"),
            ("s-docker", "important"),
        ]
    },
    {
        "id": "c-cloud-devops",
        "title": "Cloud Platform & DevOps Engineer",
        "domain": "Infrastructure & Cloud",
        "description": "Automates deployment pipelines, cloud provisioning, container orchestration, and system reliability.",
        "avg_salary_inr": "₹9 - ₹18 LPA",
        "growth_rate": "Sustained high market demand",
        "skills": [
            ("s-git", "critical"),
            ("s-linux", "critical"),
            ("s-python", "important"),
            ("s-docker", "critical"),
            ("s-k8s", "critical"),
            ("s-cicd", "critical"),
            ("s-aws", "critical"),
            ("s-terraform", "important"),
            ("s-observability", "important"),
            ("s-security-iam", "important"),
        ]
    },
    {
        "id": "c-data-scientist",
        "title": "Data Scientist & Analytics Specialist",
        "domain": "Data & Business Intelligence",
        "description": "Extracts actionable insights from enterprise data using statistical modeling, machine learning, and graph analytics.",
        "avg_salary_inr": "₹9 - ₹17 LPA",
        "growth_rate": "High across product and analytics firms",
        "skills": [
            ("s-python", "critical"),
            ("s-sql", "critical"),
            ("s-numpy-pandas", "critical"),
            ("s-sklearn", "critical"),
            ("s-neo4j", "important"),
            ("s-postgres", "important"),
            ("s-dsa", "important"),
            ("s-git", "important"),
        ]
    }
]

SKILLS = [
    {"id": "s-git", "name": "Git & Version Control", "category": "Foundations", "difficulty": "Beginner", "description": "Branching, PRs, merge workflows, GitHub/GitLab collaboration."},
    {"id": "s-dsa", "name": "Data Structures & Algorithms", "category": "Foundations", "difficulty": "Intermediate", "description": "Arrays, trees, graphs, dynamic programming, space/time complexity."},
    {"id": "s-linux", "name": "Linux & Shell Scripting", "category": "Foundations", "difficulty": "Beginner", "description": "Bash commands, file permissions, process management, SSH."},
    {"id": "s-python", "name": "Python Core", "category": "Programming", "difficulty": "Beginner", "description": "OOP, list comprehensions, generators, type hinting, virtual environments."},
    {"id": "s-js", "name": "JavaScript & ES6+", "category": "Programming", "difficulty": "Beginner", "description": "Async/await, DOM, closures, promises, event loop."},
    {"id": "s-ts", "name": "TypeScript", "category": "Programming", "difficulty": "Intermediate", "description": "Static typing, generics, interfaces, union types with React/Node."},
    {"id": "s-html-css", "name": "HTML5 & Modern CSS", "category": "Frontend", "difficulty": "Beginner", "description": "Semantic markup, Flexbox, Grid, responsive layouts, CSS variables."},
    {"id": "s-react", "name": "React.js", "category": "Frontend", "difficulty": "Intermediate", "description": "Hooks, component lifecycle, custom hooks, state management, render optimization."},
    {"id": "s-rest", "name": "RESTful API Design", "category": "Backend", "difficulty": "Beginner", "description": "HTTP verbs, status codes, request/response contracts, auth headers."},
    {"id": "s-fastapi", "name": "FastAPI", "category": "Backend", "difficulty": "Intermediate", "description": "High-performance Python API framework, Pydantic schemas, async endpoints."},
    {"id": "s-sql", "name": "SQL & Relational DBs", "category": "Data", "difficulty": "Beginner", "description": "SELECT, JOINs, indexing, transactions, ACID properties, schema normalization."},
    {"id": "s-postgres", "name": "PostgreSQL & SQLAlchemy", "category": "Data", "difficulty": "Intermediate", "description": "Advanced indexing, JSONB queries, ORM migrations, connection pooling."},
    {"id": "s-redis", "name": "Redis Caching", "category": "Data", "difficulty": "Intermediate", "description": "In-memory key-value caching, TTLs, session storage, Pub/Sub."},
    {"id": "s-neo4j", "name": "Neo4j Graph Database & Cypher", "category": "Data", "difficulty": "Intermediate", "description": "Property graph modeling, nodes/relationships, Cypher queries, graph algorithms, GraphRAG."},
    {"id": "s-numpy-pandas", "name": "NumPy & Pandas", "category": "AI / Data", "difficulty": "Beginner", "description": "Vectorized computations, DataFrames, data cleaning, exploratory analysis."},
    {"id": "s-sklearn", "name": "Scikit-Learn Machine Learning", "category": "AI / Data", "difficulty": "Intermediate", "description": "Supervised/unsupervised learning, feature engineering, cross-validation, metrics."},
    {"id": "s-pytorch", "name": "PyTorch Deep Learning", "category": "AI / Data", "difficulty": "Advanced", "description": "Tensors, autograd, CNNs, RNNs, Transformer architectures, training loops."},
    {"id": "s-llm", "name": "LLMs & Agentic Systems", "category": "AI / Data", "difficulty": "Advanced", "description": "Prompt engineering, function calling, tool use, LangChain/LangGraph, model evaluation."},
    {"id": "s-vectordb", "name": "Vector Databases & GraphRAG", "category": "AI / Data", "difficulty": "Advanced", "description": "Embeddings, cosine similarity, hybrid graph + vector retrieval, knowledge graphs."},
    {"id": "s-docker", "name": "Docker & Containers", "category": "DevOps", "difficulty": "Intermediate", "description": "Dockerfiles, multi-stage builds, container networking, docker-compose."},
    {"id": "s-k8s", "name": "Kubernetes Orchestration", "category": "DevOps", "difficulty": "Advanced", "description": "Pods, Deployments, Services, ConfigMaps, Ingress, cluster management."},
    {"id": "s-cicd", "name": "CI/CD Automation", "category": "DevOps", "difficulty": "Intermediate", "description": "GitHub Actions, automated test suites, build pipelines, continuous delivery."},
    {"id": "s-aws", "name": "AWS Cloud Fundamentals", "category": "DevOps", "difficulty": "Intermediate", "description": "EC2, S3, IAM, VPC, Lambda, RDS, security groups."},
    {"id": "s-terraform", "name": "Terraform (IaC)", "category": "DevOps", "difficulty": "Intermediate", "description": "Declarative infrastructure as code, state management, provider modules."},
    {"id": "s-queues", "name": "Message Queues & Event Streaming", "category": "Backend", "difficulty": "Advanced", "description": "Kafka, RabbitMQ, asynchronous task processing, Celery."},
    {"id": "s-microservices", "name": "Microservices & Distributed Systems", "category": "Backend", "difficulty": "Advanced", "description": "Service discovery, API gateways, circuit breakers, event-driven architecture."},
    {"id": "s-observability", "name": "Observability & Monitoring", "category": "DevOps", "difficulty": "Intermediate", "description": "Prometheus, Grafana, structured logging, distributed tracing."},
    {"id": "s-security-iam", "name": "Security & IAM Practices", "category": "Security", "difficulty": "Intermediate", "description": "OWASP Top 10, JWT tokens, RBAC, secrets management, encryption at rest/transit."},
]

PREREQUISITES = [
    # (PreReqSkillID, TargetSkillID) -> PreReq is PREREQUISITE_OF Target
    ("s-git", "s-cicd"),
    ("s-linux", "s-docker"),
    ("s-docker", "s-k8s"),
    ("s-python", "s-fastapi"),
    ("s-python", "s-numpy-pandas"),
    ("s-numpy-pandas", "s-sklearn"),
    ("s-sklearn", "s-pytorch"),
    ("s-pytorch", "s-llm"),
    ("s-sql", "s-postgres"),
    ("s-sql", "s-neo4j"),
    ("s-neo4j", "s-vectordb"),
    ("s-llm", "s-vectordb"),
    ("s-js", "s-react"),
    ("s-js", "s-ts"),
    ("s-html-css", "s-react"),
    ("s-rest", "s-fastapi"),
    ("s-fastapi", "s-microservices"),
    ("s-postgres", "s-redis"),
    ("s-redis", "s-queues"),
    ("s-docker", "s-cicd"),
    ("s-aws", "s-terraform"),
    ("s-dsa", "s-microservices"),
]

COURSES = [
    {
        "id": "crs-neo4j-fund",
        "title": "Neo4j Graph Fundamentals & Cypher",
        "provider": "Neo4j GraphAcademy",
        "url": "https://graphacademy.neo4j.com/courses/neo4j-fundamentals/",
        "duration_hours": 4,
        "rating": 4.9,
        "level": "Beginner to Intermediate",
        "teaches": ["s-neo4j"]
    },
    {
        "id": "crs-graph-rag",
        "title": "GraphRAG & LLM Knowledge Graphs with Neo4j",
        "provider": "Neo4j GraphAcademy & DeepLearning.AI",
        "url": "https://graphacademy.neo4j.com/courses/llm-fundamentals/",
        "duration_hours": 6,
        "rating": 4.95,
        "level": "Advanced",
        "teaches": ["s-neo4j", "s-vectordb", "s-llm"]
    },
    {
        "id": "crs-cs50-python",
        "title": "CS50P: Introduction to Programming with Python",
        "provider": "Harvard University / edX",
        "url": "https://cs50.harvard.edu/python/",
        "duration_hours": 30,
        "rating": 4.9,
        "level": "Beginner",
        "teaches": ["s-python"]
    },
    {
        "id": "crs-fastapi",
        "title": "Building Modern APIs with FastAPI and Python",
        "provider": "freeCodeCamp",
        "url": "https://www.freecodecamp.org/news/fastapi-quickstart/",
        "duration_hours": 8,
        "rating": 4.8,
        "level": "Intermediate",
        "teaches": ["s-fastapi", "s-rest"]
    },
    {
        "id": "crs-react-complete",
        "title": "The Joy of React & Modern Frontend Architecture",
        "provider": "freeCodeCamp & Joy of React",
        "url": "https://react.dev/learn",
        "duration_hours": 20,
        "rating": 4.85,
        "level": "Intermediate",
        "teaches": ["s-react", "s-js", "s-html-css"]
    },
    {
        "id": "crs-sql-mastery",
        "title": "SQL and Relational Database Design Mastery",
        "provider": "Khan Academy & PostgreSQL Org",
        "url": "https://www.postgresql.org/docs/tutorial/",
        "duration_hours": 10,
        "rating": 4.75,
        "level": "Beginner to Intermediate",
        "teaches": ["s-sql", "s-postgres"]
    },
    {
        "id": "crs-docker-k8s",
        "title": "Docker and Kubernetes: The Complete Practical Guide",
        "provider": "Coursera & Linux Foundation",
        "url": "https://www.coursera.org/learn/cloud-infrastructure-technologies",
        "duration_hours": 16,
        "rating": 4.8,
        "level": "Intermediate to Advanced",
        "teaches": ["s-docker", "s-k8s", "s-linux"]
    },
    {
        "id": "crs-ml-specialization",
        "title": "Machine Learning Specialization",
        "provider": "DeepLearning.AI / Andrew Ng",
        "url": "https://www.deeplearning.ai/courses/machine-learning-specialization/",
        "duration_hours": 40,
        "rating": 4.95,
        "level": "Intermediate",
        "teaches": ["s-numpy-pandas", "s-sklearn"]
    },
    {
        "id": "crs-dl-pytorch",
        "title": "Deep Learning with PyTorch: Zero to Mastery",
        "provider": "PyTorch Foundation / learnpytorch.io",
        "url": "https://learnpytorch.io/",
        "duration_hours": 25,
        "rating": 4.9,
        "level": "Advanced",
        "teaches": ["s-pytorch"]
    },
    {
        "id": "crs-aws-cloud",
        "title": "AWS Cloud Practitioner & Solution Architecture",
        "provider": "AWS Skill Builder",
        "url": "https://aws.amazon.com/training/digital/",
        "duration_hours": 15,
        "rating": 4.7,
        "level": "Intermediate",
        "teaches": ["s-aws", "s-security-iam"]
    },
    {
        "id": "crs-dsa-grind",
        "title": "Data Structures & Algorithmic Problem Solving",
        "provider": "NeetCode & MIT OpenCourseWare",
        "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms/",
        "duration_hours": 35,
        "rating": 4.85,
        "level": "Intermediate",
        "teaches": ["s-dsa"]
    },
    {
        "id": "crs-redis-distributed",
        "title": "High Performance Caching & Redis Fundamentals",
        "provider": "Redis University",
        "url": "https://university.redis.com/",
        "duration_hours": 8,
        "rating": 4.8,
        "level": "Intermediate",
        "teaches": ["s-redis"]
    },
]

# Repeatable sample student profiles for instant demo showcase
SAMPLE_STUDENTS = [
    {
        "id": "demo-student-nikhil",
        "name": "Nikhil Rao (Student)",
        "email": "nikhil@grindos.dev",
        "target_career": "Full Stack Developer",
        "skills": ["s-git", "s-html-css", "s-js", "s-python"]
    },
    {
        "id": "demo-student-adithya",
        "name": "Adithya B (Aspiring AI Engineer)",
        "email": "adithya@grindos.dev",
        "target_career": "AI & Machine Learning Engineer",
        "skills": ["s-git", "s-python", "s-numpy-pandas", "s-sql"]
    }
]

def seed_graph_data(driver) -> dict:
    """
    Executes idempotent Cypher queries to seed Neo4j graph nodes and relationships.
    Safe to run repeatedly; uses MERGE on unique identifiers.
    """
    stats = {"careers": 0, "skills": 0, "prerequisites": 0, "courses": 0, "students": 0}

    with driver.session() as session:
        # 1. Constraints for performance and uniqueness
        constraints = [
            "CREATE CONSTRAINT career_id IF NOT EXISTS FOR (c:Career) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT course_id IF NOT EXISTS FOR (crs:Course) REQUIRE crs.id IS UNIQUE",
            "CREATE CONSTRAINT student_id IF NOT EXISTS FOR (st:Student) REQUIRE st.id IS UNIQUE",
        ]
        for c in constraints:
            try:
                session.run(c)
            except Exception as e:
                # Aura free or specific editions might ignore or throw if already exists
                pass

        # 2. Seed Skills
        skill_query = """
        UNWIND $skills AS s
        MERGE (skill:Skill {id: s.id})
        SET skill.name = s.name,
            skill.category = s.category,
            skill.difficulty = s.difficulty,
            skill.description = s.description
        RETURN count(skill) AS cnt
        """
        res = session.run(skill_query, skills=SKILLS)
        stats["skills"] = res.single()["cnt"]

        # 3. Seed Prerequisites
        prereq_query = """
        UNWIND $prereqs AS p
        MATCH (pre:Skill {id: p[0]})
        MATCH (target:Skill {id: p[1]})
        MERGE (pre)-[r:PREREQUISITE_OF]->(target)
        RETURN count(r) AS cnt
        """
        res = session.run(prereq_query, prereqs=PREREQUISITES)
        stats["prerequisites"] = res.single()["cnt"]

        # 4. Seed Careers & Requirements
        for c in CAREERS:
            career_query = """
            MERGE (career:Career {id: $id})
            SET career.title = $title,
                career.domain = $domain,
                career.description = $description,
                career.avg_salary_inr = $avg_salary_inr,
                career.growth_rate = $growth_rate
            """
            session.run(career_query, **{k: c[k] for k in ["id", "title", "domain", "description", "avg_salary_inr", "growth_rate"]})
            stats["careers"] += 1

            # Connect skills
            career_skills_query = """
            MATCH (career:Career {id: $career_id})
            UNWIND $skill_pairs AS pair
            MATCH (skill:Skill {id: pair[0]})
            MERGE (career)-[r:REQUIRES_SKILL]->(skill)
            SET r.importance = pair[1]
            """
            session.run(career_skills_query, career_id=c["id"], skill_pairs=c["skills"])

        # 5. Seed Courses & TEACHES relationships
        for crs in COURSES:
            course_query = """
            MERGE (course:Course {id: $id})
            SET course.title = $title,
                course.provider = $provider,
                course.url = $url,
                course.duration_hours = $duration_hours,
                course.rating = $rating,
                course.level = $level
            WITH course
            UNWIND $teaches AS skill_id
            MATCH (skill:Skill {id: skill_id})
            MERGE (course)-[:TEACHES]->(skill)
            """
            session.run(course_query, **crs)
            stats["courses"] += 1

        # 6. Seed Sample Students
        for st in SAMPLE_STUDENTS:
            student_query = """
            MERGE (student:Student {id: $id})
            SET student.name = $name,
                student.email = $email,
                student.target_career = $target_career
            WITH student
            MATCH (career:Career {title: $target_career})
            MERGE (student)-[:TARGETS]->(career)
            WITH student
            UNWIND $skills AS skill_id
            MATCH (skill:Skill {id: skill_id})
            MERGE (student)-[:HAS_SKILL {proficiency: 'intermediate'}]->(skill)
            """
            session.run(student_query, **st)
            stats["students"] += 1

    return stats


if __name__ == "__main__":
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    if not (uri and user and password):
        print("Missing NEO4J credentials in environment. Check Backend/.env.")
        exit(1)

    print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    print("Seeding repeatable graph data...")
    res = seed_graph_data(driver)
    print("Graph seed complete! Stats:", res)
    driver.close()
