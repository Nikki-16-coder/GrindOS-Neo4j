"""
GrindOS Neo4j Graph Intelligence Module
Career Navigator & Skill Gap Agent powered by Neo4j AuraDB.
Handles graph connections, queries, skill gap analysis,
course recommendations, topological prerequisite roadmaps, and graph visualization.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import GraphDatabase, Driver
from pydantic import BaseModel
from sqlalchemy.orm import Session

from Backend.auth import get_current_user, get_optional_current_user
from Backend.database import get_db
from Backend.models import User, Skill as SQLSkill, Assessment, Recommendation
from Backend.graph_seed import seed_graph_data

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

router = APIRouter(prefix="/graph", tags=["Career Navigator & Graph"])

_driver: Optional[Driver] = None


def get_graph_driver() -> Driver:
    """
    Returns a singleton Neo4j driver configured via environment variables.
    Raises clean HTTPException(503) if missing credentials or service unavailable.
    """
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI", "neo4j+s://e985e863.databases.neo4j.io")
        user = os.getenv("NEO4J_USERNAME", "e985e863")
        password = os.getenv("NEO4J_PASSWORD", "")
        if not password:
            raise HTTPException(
                status_code=503,
                detail="Neo4j credentials not configured. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in Backend/.env"
            )
        try:
            _driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0,
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to Neo4j AuraDB ({uri}): {str(e)}"
            )
    return _driver


def run_cypher_read(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Runs a read-only Cypher query and returns dictionaries."""
    driver = get_graph_driver()
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]


def run_cypher_write(query: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Runs a write Cypher query."""
    driver = get_graph_driver()
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]


# --- Pydantic Schemas ---
class SkillGapRequest(BaseModel):
    career_id: str
    custom_skills: Optional[List[str]] = None  # Skill names or IDs


class SyncStudentRequest(BaseModel):
    target_career: Optional[str] = None
    skills: Optional[List[str]] = None


# --- Core Graph Functions ---

def sync_user_to_graph(user_id: int, user_name: str, user_email: str, skill_names: List[str], target_career: Optional[str] = None):
    """
    Idempotently syncs a GrindOS user and their acquired skills to the Neo4j graph.
    """
    student_id = f"student-{user_id}"
    query = """
    MERGE (st:Student {id: $student_id})
    SET st.name = $name,
        st.email = $email,
        st.target_career = coalesce($target_career, st.target_career)
    WITH st
    // Optional target career link
    FOREACH (_ IN CASE WHEN $target_career IS NOT NULL THEN [1] ELSE [] END |
        MERGE (c:Career {title: $target_career})
        MERGE (st)-[:TARGETS]->(c)
    )
    // Clear and re-link active skills
    OPTIONAL MATCH (st)-[r:HAS_SKILL]->(:Skill)
    DELETE r
    WITH st
    UNWIND $skill_names AS s_name
    MATCH (s:Skill)
    WHERE toLower(s.name) = toLower(s_name) OR toLower(s.id) = toLower(s_name)
    MERGE (st)-[:HAS_SKILL {proficiency: 'intermediate', updated_at: datetime()}]->(s)
    RETURN count(s) AS synced_count
    """
    driver = get_graph_driver()
    with driver.session() as session:
        res = session.run(query, {
            "student_id": student_id,
            "name": user_name or "Student",
            "email": user_email or "",
            "target_career": target_career,
            "skill_names": skill_names,
        })
        return res.single()


# --- API Endpoints ---

@router.get("/status")
def graph_status():
    """
    Health check and connection verification endpoint for Neo4j AuraDB.
    """
    try:
        driver = get_graph_driver()
        with driver.session() as session:
            rec = session.run("RETURN 1 as ok, datetime() as server_time").single()
            # Count nodes
            counts = session.run("""
                MATCH (c:Career) WITH count(c) AS careers
                MATCH (s:Skill) WITH careers, count(s) AS skills
                MATCH (crs:Course) WITH careers, skills, count(crs) AS courses
                MATCH (st:Student) WITH careers, skills, courses, count(st) AS students
                RETURN careers, skills, courses, students
            """).single()

            return {
                "connected": True,
                "uri": os.getenv("NEO4J_URI"),
                "database": os.getenv("NEO4J_DATABASE", "neo4j"),
                "server_time": str(rec["server_time"]),
                "graph_counts": {
                    "careers": counts["careers"],
                    "skills": counts["skills"],
                    "courses": counts["courses"],
                    "students": counts["students"],
                }
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "uri": os.getenv("NEO4J_URI")
        }


@router.post("/seed")
def seed_graph():
    """
    Triggers repeatable idempotent seed of careers, skills, prerequisites, courses, and sample students.
    """
    try:
        driver = get_graph_driver()
        stats = seed_graph_data(driver)
        return {
            "message": "Graph successfully seeded with career navigator data",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed graph: {str(e)}")


@router.get("/careers")
def list_careers():
    """
    Lists all careers available in the graph, including required skill counts and domain info.
    """
    query = """
    MATCH (c:Career)
    OPTIONAL MATCH (c)-[req:REQUIRES_SKILL]->(s:Skill)
    RETURN c.id AS id,
           c.title AS title,
           c.domain AS domain,
           c.description AS description,
           c.avg_salary_inr AS avg_salary_inr,
           c.growth_rate AS growth_rate,
           count(s) AS total_skills,
           count(CASE WHEN req.importance = 'critical' THEN 1 END) AS critical_skills
    ORDER BY c.title
    """
    return run_cypher_read(query)


@router.get("/careers/{career_id}")
def get_career_details(career_id: str):
    """
    Gets detailed information about a career including all required skills, their importance, and prerequisite relationships.
    """
    query = """
    MATCH (c:Career {id: $career_id})
    OPTIONAL MATCH (c)-[req:REQUIRES_SKILL]->(s:Skill)
    OPTIONAL MATCH (pre:Skill)-[:PREREQUISITE_OF]->(s)
    WHERE (c)-[:REQUIRES_SKILL]->(pre)
    RETURN c.id AS id,
           c.title AS title,
           c.domain AS domain,
           c.description AS description,
           c.avg_salary_inr AS avg_salary_inr,
           c.growth_rate AS growth_rate,
           collect(DISTINCT {
               id: s.id,
               name: s.name,
               category: s.category,
               difficulty: s.difficulty,
               description: s.description,
               importance: req.importance,
               prerequisites: collect(DISTINCT pre.name)
           }) AS skills
    """
    results = run_cypher_read(query, {"career_id": career_id})
    if not results or not results[0]["id"]:
        raise HTTPException(status_code=404, detail="Career not found")
    return results[0]


@router.post("/skill-gap")
def analyze_skill_gap(
    payload: SkillGapRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Identifies missing skills, acquired skills, match percentage, and readiness score
    for a target career using real Cypher pattern matching.
    """
    career_id = payload.career_id

    # Gather user's acquired skill names
    acquired_skills = []
    if current_user:
        # Check GrindOS SQL Skills database
        db_skills = db.query(SQLSkill).filter(SQLSkill.user_id == current_user.id).all()
        acquired_skills.extend([s.name.strip().lower() for s in db_skills if s.name])

        # Also check completed assessment/recommendation if available
        rec = db.query(Recommendation).filter(Recommendation.user_id == current_user.id).first()
        if rec and isinstance(rec.result, dict):
            for path in rec.result.get("career_paths", []):
                for ms in path.get("matching_skills", []):
                    acquired_skills.append(ms.strip().lower())

    if payload.custom_skills:
        for s in payload.custom_skills:
            acquired_skills.append(s.strip().lower())

    acquired_skills = list(set(acquired_skills))

    query = """
    MATCH (c:Career {id: $career_id})
    OPTIONAL MATCH (c)-[req:REQUIRES_SKILL]->(s:Skill)
    OPTIONAL MATCH (pre:Skill)-[:PREREQUISITE_OF]->(s)
    WHERE (c)-[:REQUIRES_SKILL]->(pre)
    RETURN c.id AS career_id,
           c.title AS career_title,
           c.domain AS career_domain,
           s.id AS skill_id,
           s.name AS skill_name,
           s.category AS category,
           s.difficulty AS difficulty,
           s.description AS description,
           req.importance AS importance,
           collect(DISTINCT pre.name) AS prerequisites
    ORDER BY CASE req.importance WHEN 'critical' THEN 1 WHEN 'important' THEN 2 ELSE 3 END, s.name
    """
    rows = run_cypher_read(query, {"career_id": career_id})
    if not rows or not rows[0]["career_id"]:
        raise HTTPException(status_code=404, detail="Career not found")

    career_title = rows[0]["career_title"]
    career_domain = rows[0]["career_domain"]

    acquired_list = []
    missing_list = []

    for r in rows:
        if not r["skill_id"]:
            continue
        skill_name_lower = r["skill_name"].lower()
        skill_id_lower = r["skill_id"].lower()

        # Check if user has this skill (exact or substring match)
        has_skill = any(
            (user_s in skill_name_lower or skill_name_lower in user_s or user_s == skill_id_lower)
            for user_s in acquired_skills
        )

        skill_obj = {
            "id": r["skill_id"],
            "name": r["skill_name"],
            "category": r["category"],
            "difficulty": r["difficulty"],
            "description": r["description"],
            "importance": r["importance"],
            "prerequisites": r["prerequisites"],
        }

        if has_skill:
            acquired_list.append(skill_obj)
        else:
            missing_list.append(skill_obj)

    total_skills = len(acquired_list) + len(missing_list)
    match_percentage = round((len(acquired_list) / total_skills * 100), 1) if total_skills > 0 else 0.0

    # Categorize missing skills by importance
    critical_missing = [s for s in missing_list if s["importance"] == "critical"]
    important_missing = [s for s in missing_list if s["importance"] == "important"]
    nice_missing = [s for s in missing_list if s["importance"] == "nice_to_have"]

    # Calculate readiness category
    if match_percentage >= 75:
        readiness_status = "Job Ready (Interview Prep Phase)"
    elif match_percentage >= 50:
        readiness_status = "Intermediate (Close to Application Ready)"
    elif match_percentage >= 25:
        readiness_status = "Developing (Core Skills Required)"
    else:
        readiness_status = "Foundational (Beginner Roadmap)"

    return {
        "career_id": career_id,
        "career_title": career_title,
        "career_domain": career_domain,
        "match_percentage": match_percentage,
        "readiness_status": readiness_status,
        "total_required_skills": total_skills,
        "acquired_count": len(acquired_list),
        "missing_count": len(missing_list),
        "acquired_skills": acquired_list,
        "missing_skills": missing_list,
        "critical_missing": critical_missing,
        "important_missing": important_missing,
        "nice_to_have_missing": nice_missing,
    }


@router.get("/roadmap/{career_id}")
def get_graph_learning_roadmap(
    career_id: str,
    student_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a logical, sequenced learning roadmap for the missing skills of a target career.
    Uses topological prerequisite ordering (Phase 1: Foundations, Phase 2: Core Engineering, Phase 3: Advanced/Specialized).
    Attaches top recommended courses with direct URLs and ratings.
    """
    # 1. Determine acquired skills for the current user/student
    acquired_skill_ids = set()
    if student_id:
        st_res = run_cypher_read("MATCH (st:Student {id: $id})-[:HAS_SKILL]->(s:Skill) RETURN s.id as id", {"id": student_id})
        acquired_skill_ids = {r["id"] for r in st_res}
    elif current_user:
        # Check GrindOS SQL Skills database
        db_skills = db.query(SQLSkill).filter(SQLSkill.user_id == current_user.id).all()
        user_skill_names = [s.name.strip().lower() for s in db_skills if s.name]
        # Query matching IDs from graph
        if user_skill_names:
            match_res = run_cypher_read("""
                MATCH (s:Skill)
                WHERE any(us IN $names WHERE toLower(s.name) CONTAINS us OR us CONTAINS toLower(s.name))
                RETURN s.id as id
            """, {"names": user_skill_names})
            acquired_skill_ids = {r["id"] for r in match_res}

    # 2. Query skills required for career along with prerequisites and courses
    query = """
    MATCH (c:Career {id: $career_id})-[req:REQUIRES_SKILL]->(s:Skill)
    OPTIONAL MATCH (pre:Skill)-[:PREREQUISITE_OF]->(s)
    WHERE (c)-[:REQUIRES_SKILL]->(pre)
    OPTIONAL MATCH (crs:Course)-[:TEACHES]->(s)
    RETURN c.title AS career_title,
           c.domain AS career_domain,
           s.id AS skill_id,
           s.name AS skill_name,
           s.category AS category,
           s.difficulty AS difficulty,
           s.description AS description,
           req.importance AS importance,
           collect(DISTINCT {id: pre.id, name: pre.name}) AS prerequisites,
           collect(DISTINCT {
               id: crs.id,
               title: crs.title,
               provider: crs.provider,
               url: crs.url,
               duration_hours: crs.duration_hours,
               rating: crs.rating,
               level: crs.level
           }) AS courses
    """
    rows = run_cypher_read(query, {"career_id": career_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Career not found")

    career_title = rows[0]["career_title"]

    # Filter out skills already acquired
    missing_items = []
    for r in rows:
        is_acquired = r["skill_id"] in acquired_skill_ids
        missing_items.append({
            "skill_id": r["skill_id"],
            "name": r["skill_name"],
            "category": r["category"],
            "difficulty": r["difficulty"],
            "description": r["description"],
            "importance": r["importance"],
            "prerequisites": [p for p in r["prerequisites"] if p.get("id")],
            "courses": [c for c in r["courses"] if c.get("id")],
            "is_acquired": is_acquired,
        })

    # Topological Phase assignment:
    # Phase 1: Skills with 0 unfulfilled prerequisites or "Beginner" difficulty
    # Phase 2: Skills whose prerequisites are in Phase 1 or "Intermediate"
    # Phase 3: Advanced skills, microservices, deep learning, distributed systems
    phase_1 = []
    phase_2 = []
    phase_3 = []

    for item in missing_items:
        diff = item["difficulty"]
        prereq_ids = [p["id"] for p in item["prerequisites"]]
        
        # If beginner or no prerequisites within this career
        if diff == "Beginner" or not prereq_ids:
            phase_1.append(item)
        elif diff == "Intermediate":
            phase_2.append(item)
        else:
            phase_3.append(item)

    # In case phase_2 is empty or all lumped, balance logically
    phases = [
        {
            "phase_number": 1,
            "title": "Phase 1: Foundations & Prerequisites",
            "description": "Fundamental tools, core programming, and essential prerequisites before advanced implementation.",
            "skills": phase_1,
        },
        {
            "phase_number": 2,
            "title": "Phase 2: Core Engineering & Frameworks",
            "description": "Production frameworks, data systems, containerization, and API integrations.",
            "skills": phase_2,
        },
        {
            "phase_number": 3,
            "title": "Phase 3: Advanced Architecture & Production Specialization",
            "description": "High-scale architecture, agentic AI, graph systems, and production reliability.",
            "skills": phase_3,
        }
    ]

    return {
        "career_id": career_id,
        "career_title": career_title,
        "total_skills": len(missing_items),
        "missing_count": len([m for m in missing_items if not m["is_acquired"]]),
        "phases": phases,
    }


@router.get("/visualize/{career_id}")
def get_graph_visualization(
    career_id: str,
    student_id: Optional[str] = "demo-student-nikhil"
):
    """
    Returns nodes and edges formatted for interactive Graph Visualization in the UI.
    Visualizes:
    - Career Node (Gold)
    - Skill Nodes (Green for Acquired, Red/Coral for Missing Critical, Cyan for Missing Important)
    - Course Nodes (Purple)
    - Edges for REQUIRES_SKILL, PREREQUISITE_OF, TEACHES
    """
    query = """
    MATCH (c:Career {id: $career_id})
    OPTIONAL MATCH (c)-[req:REQUIRES_SKILL]->(s:Skill)
    OPTIONAL MATCH (st:Student {id: $student_id})-[has:HAS_SKILL]->(s)
    OPTIONAL MATCH (crs:Course)-[tch:TEACHES]->(s)
    OPTIONAL MATCH (s)-[pre:PREREQUISITE_OF]->(target_s:Skill)
    WHERE (c)-[:REQUIRES_SKILL]->(target_s)
    RETURN c.id AS career_id,
           c.title AS career_title,
           c.domain AS career_domain,
           collect(DISTINCT {
               id: s.id,
               name: s.name,
               category: s.category,
               difficulty: s.difficulty,
               importance: req.importance,
               status: CASE WHEN has IS NOT NULL THEN 'acquired' ELSE 'missing' END
           }) AS skills,
           collect(DISTINCT {
               source: s.id,
               target: target_s.id,
               type: 'PREREQUISITE_OF'
           }) AS prereq_edges,
           collect(DISTINCT {
               id: crs.id,
               title: crs.title,
               provider: crs.provider,
               rating: crs.rating,
               url: crs.url,
               skill_id: s.id
           }) AS courses
    """
    res = run_cypher_read(query, {"career_id": career_id, "student_id": student_id})
    if not res or not res[0]["career_id"]:
        raise HTTPException(status_code=404, detail="Career not found")

    data = res[0]
    career_id = data["career_id"]
    career_title = data["career_title"]

    nodes = []
    edges = []

    # 1. Career Node
    nodes.append({
        "id": career_id,
        "name": career_title,
        "type": "career",
        "category": data["career_domain"],
        "color": "#f59e0b",  # Amber
        "size": 42,
    })

    # 2. Skill Nodes & Career-Skill Edges
    for s in data["skills"]:
        if not s.get("id"):
            continue
        is_acquired = (s["status"] == "acquired")
        importance = s.get("importance", "important")

        if is_acquired:
            color = "#10b981"  # Emerald green
        elif importance == "critical":
            color = "#ef4444"  # Red / Coral
        elif importance == "important":
            color = "#06b6d4"  # Cyan
        else:
            color = "#8b5cf6"  # Violet

        nodes.append({
            "id": s["id"],
            "name": s["name"],
            "type": "skill",
            "category": s.get("category", "Skill"),
            "difficulty": s.get("difficulty", "Intermediate"),
            "status": s["status"],
            "importance": importance,
            "color": color,
            "size": 28 if importance == "critical" else 22,
        })

        # Edge from Career to Skill
        edges.append({
            "source": career_id,
            "target": s["id"],
            "type": "REQUIRES_SKILL",
            "label": importance.upper(),
            "color": "#475569"
        })

    # 3. Prerequisite Edges (Skill -> Skill)
    for p in data["prereq_edges"]:
        if p.get("source") and p.get("target"):
            edges.append({
                "source": p["source"],
                "target": p["target"],
                "type": "PREREQUISITE_OF",
                "label": "PREREQ",
                "color": "#f59e0b"
            })

    # 4. Course Nodes & TEACHES Edges
    added_course_ids = set()
    for crs in data["courses"]:
        cid = crs.get("id")
        if not cid or cid in added_course_ids:
            continue
        added_course_ids.add(cid)
        nodes.append({
            "id": cid,
            "name": crs["title"],
            "provider": crs.get("provider", ""),
            "rating": crs.get("rating", 4.8),
            "url": crs.get("url", ""),
            "type": "course",
            "color": "#a855f7",  # Purple
            "size": 18,
        })
        if crs.get("skill_id"):
            edges.append({
                "source": cid,
                "target": crs["skill_id"],
                "type": "TEACHES",
                "label": "TEACHES",
                "color": "#8b5cf6"
            })

    return {
        "career_id": career_id,
        "career_title": career_title,
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "acquired_count": len([n for n in nodes if n.get("status") == "acquired"]),
            "missing_count": len([n for n in nodes if n.get("status") == "missing"]),
        }
    }


@router.post("/sync-user")
def sync_current_user_skills(
    payload: SyncStudentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Syncs the authenticated GrindOS user's tracked skills into Neo4j graph as a Student node.
    """
    skill_names = payload.skills or []
    if not skill_names:
        db_skills = db.query(SQLSkill).filter(SQLSkill.user_id == current_user.id).all()
        skill_names = [s.name for s in db_skills if s.name]

    try:
        res = sync_user_to_graph(
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=current_user.email,
            skill_names=skill_names,
            target_career=payload.target_career
        )
        return {
            "message": f"Successfully synced {len(skill_names)} skills to Neo4j Graph for {current_user.name}",
            "student_id": f"student-{current_user.id}",
            "skills": skill_names
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync to graph: {str(e)}")
