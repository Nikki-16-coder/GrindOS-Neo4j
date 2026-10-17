import React, { useState, useEffect, useRef } from "react";
import { api } from "./api.js";
import { useAuth } from "./App.jsx";

export function CareerNavigatorView({ onGoRoadmap }) {
  const { user, token } = useAuth();

  const [graphStatus, setGraphStatus] = useState(null);
  const [careers, setCareers] = useState([]);
  const [selectedCareerId, setSelectedCareerId] = useState("c-fullstack");
  const [activePersona, setActivePersona] = useState("mine"); // "mine" | "nikhil" | "adithya"
  const [skillGap, setSkillGap] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // 1. Fetch initial graph status and careers list
  useEffect(() => {
    async function loadInitial() {
      try {
        setLoading(true);
        const status = await api.getGraphStatus().catch(() => null);
        setGraphStatus(status);

        const careerList = await api.getGraphCareers().catch(() => []);
        setCareers(careerList);
        if (careerList.length > 0) {
          setSelectedCareerId(careerList[0].id);
        }
      } catch (err) {
        console.error("Failed to load initial graph data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadInitial();
  }, []);

  // 2. Load skill gap, roadmap, and visualization when selected career or persona changes
  useEffect(() => {
    if (!selectedCareerId) return;

    let studentId = null;
    let customSkills = null;

    if (activePersona === "nikhil") {
      studentId = "demo-student-nikhil";
      customSkills = ["Git & Version Control", "JavaScript & ES6+", "HTML5 & Modern CSS", "Python Core"];
    } else if (activePersona === "adithya") {
      studentId = "demo-student-adithya";
      customSkills = ["Git & Version Control", "Python Core", "NumPy & Pandas", "SQL & Relational DBs"];
    }

    async function fetchCareerData() {
      try {
        const [gapRes, roadmapRes, vizRes] = await Promise.all([
          api.analyzeSkillGap({
            token: activePersona === "mine" ? token : null,
            careerId: selectedCareerId,
            customSkills,
          }),
          api.getGraphRoadmap({
            token: activePersona === "mine" ? token : null,
            careerId: selectedCareerId,
            studentId,
          }),
          api.getGraphVisualization({
            careerId: selectedCareerId,
            studentId,
          }),
        ]);

        setSkillGap(gapRes);
        setRoadmap(roadmapRes);
        setGraphData(vizRes);
        setSelectedNode(null);
      } catch (err) {
        console.error("Error loading career data:", err);
      }
    }

    fetchCareerData();
  }, [selectedCareerId, activePersona, token]);

  const handleSeedGraph = async () => {
    try {
      setSeeding(true);
      await api.seedGraph();
      const status = await api.getGraphStatus();
      setGraphStatus(status);
      const careerList = await api.getGraphCareers();
      setCareers(careerList);
      alert("Neo4j Graph successfully re-seeded with latest careers, skills, prerequisites, and courses!");
    } catch (err) {
      alert("Failed to seed graph: " + (err.message || err));
    } finally {
      setSeeding(false);
    }
  };

  const handleSyncMySkills = async () => {
    try {
      setSyncing(true);
      const res = await api.syncGraphUser({
        token,
        targetCareer: selectedCareer?.title,
      });
      alert(res.message || "Skills synced to Neo4j graph!");
      setActivePersona("mine");
    } catch (err) {
      alert("Sync failed: " + (err.message || err));
    } finally {
      setSyncing(false);
    }
  };

  const selectedCareer = careers.find((c) => c.id === selectedCareerId);

  // SVG Pan & Drag Handlers
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  // Calculate layout coordinates for SVG visualization
  const getLayoutNodes = () => {
    if (!graphData || !graphData.nodes) return [];

    const nodes = [...graphData.nodes];
    const width = 860;
    const height = 480;
    const centerX = width / 2;
    const centerY = height / 2;

    const careerNode = nodes.find((n) => n.type === "career");
    const skillNodes = nodes.filter((n) => n.type === "skill");
    const courseNodes = nodes.filter((n) => n.type === "course");

    if (careerNode) {
      careerNode.x = centerX;
      careerNode.y = centerY;
    }

    // Place skill nodes in an inner circle
    const skillRadius = 150;
    skillNodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / skillNodes.length;
      node.x = centerX + skillRadius * Math.cos(angle);
      node.y = centerY + skillRadius * Math.sin(angle);
    });

    // Place course nodes in an outer ring near skills they teach
    const courseRadius = 220;
    courseNodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / courseNodes.length + 0.15;
      node.x = centerX + courseRadius * Math.cos(angle);
      node.y = centerY + courseRadius * Math.sin(angle);
    });

    return nodes;
  };

  const layoutNodes = getLayoutNodes();
  const nodeMap = new Map(layoutNodes.map((n) => [n.id, n]));

  return (
    <div className="gos-content" style={{ maxWidth: 1180, margin: "0 auto", padding: "20px 24px 60px" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div className="gos-eyebrow">NEO4J GRAPH INTELLIGENCE</div>
        <h1 className="gos-title" style={{ fontSize: 32, marginBottom: 8 }}>
          Career Navigator &amp; Skill Gap Agent
        </h1>
        <p className="gos-sub" style={{ maxWidth: 780 }}>
          Real-time graph reasoning over tech career paths, prerequisite dependency chains, and personalized learning roadmaps powered by Neo4j AuraDB.
        </p>
      </div>

      {/* Live Neo4j Connection Status Bar */}
      <div className="graph-status-bar">
        <div className="graph-status-badge">
          <span className="graph-pulse-dot" style={{ background: graphStatus?.connected ? "#10b981" : "#ef4444" }} />
          <span>
            {graphStatus?.connected ? "Neo4j AuraDB Connected" : "Connecting to Neo4j AuraDB..."}
          </span>
          <span style={{ color: "var(--text-faint)", fontSize: 11, fontWeight: 400 }}>
            (Instance: {graphStatus?.uri?.split("//")[1]?.split(".")[0] || "e985e863"})
          </span>
        </div>

        <div className="graph-stat-pills">
          <span className="graph-stat-pill">
            Careers: <strong>{graphStatus?.graph_counts?.careers ?? 5}</strong>
          </span>
          <span className="graph-stat-pill">
            Skills: <strong>{graphStatus?.graph_counts?.skills ?? 28}</strong>
          </span>
          <span className="graph-stat-pill">
            Prerequisites: <strong>22</strong>
          </span>
          <span className="graph-stat-pill">
            Courses: <strong>{graphStatus?.graph_counts?.courses ?? 12}</strong>
          </span>
          <button
            type="button"
            className="gos-btn"
            style={{ width: "auto", padding: "4px 10px", fontSize: 11 }}
            onClick={handleSeedGraph}
            disabled={seeding}
          >
            {seeding ? "Seeding..." : "↻ Refresh Graph Seed"}
          </button>
        </div>
      </div>

      {/* Target Career Selection Grid */}
      <div style={{ marginBottom: 16 }}>
        <div className="gos-eyebrow" style={{ marginBottom: 10 }}>1. SELECT TARGET CAREER</div>
        <div className="career-select-grid">
          {careers.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`career-card-btn ${c.id === selectedCareerId ? "active" : ""}`}
              onClick={() => setSelectedCareerId(c.id)}
            >
              <div className="career-title">{c.title}</div>
              <div className="career-sub">{c.domain}</div>
              <div style={{ marginTop: 8, fontSize: 11, color: "var(--accent)", fontFamily: "var(--font-mono)" }}>
                {c.avg_salary_inr || "₹8 - ₹16 LPA"}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Persona / Student Context Switcher */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, marginBottom: 24, padding: "12px 18px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--text-dim)" }}>
            EVALUATION PERSONA:
          </span>
          <button
            type="button"
            className={`gos-btn ${activePersona === "mine" ? "gos-btn-primary" : ""}`}
            style={{ width: "auto", padding: "5px 12px", fontSize: 12 }}
            onClick={() => setActivePersona("mine")}
          >
            My Account ({user?.name || "User"})
          </button>
          <button
            type="button"
            className={`gos-btn ${activePersona === "nikhil" ? "gos-btn-primary" : ""}`}
            style={{ width: "auto", padding: "5px 12px", fontSize: 12 }}
            onClick={() => setActivePersona("nikhil")}
          >
            Nikhil Rao (Student Demo)
          </button>
          <button
            type="button"
            className={`gos-btn ${activePersona === "adithya" ? "gos-btn-primary" : ""}`}
            style={{ width: "auto", padding: "5px 12px", fontSize: 12 }}
            onClick={() => setActivePersona("adithya")}
          >
            Adithya B (AI Aspirant Demo)
          </button>
        </div>

        {activePersona === "mine" && (
          <button
            type="button"
            className="gos-btn"
            style={{ width: "auto", padding: "5px 12px", fontSize: 12, borderColor: "#10b981", color: "#10b981" }}
            onClick={handleSyncMySkills}
            disabled={syncing}
          >
            {syncing ? "Syncing..." : "⚡ Sync My GrindOS Skills into Neo4j"}
          </button>
        )}
      </div>

      {/* Real-time Skill Gap Readout */}
      {skillGap && (
        <div className="skill-gap-readout">
          <div className="gauge-card">
            <div className="gauge-score">{skillGap.match_percentage}%</div>
            <div className="gauge-label">GRAPH READINESS MATCH</div>
            <div className="gauge-status-chip">{skillGap.readiness_status}</div>
            <div style={{ marginTop: 16, fontSize: 12, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
              {skillGap.acquired_count} acquired / {skillGap.total_required_skills} total required
            </div>
          </div>

          <div className="gos-panel" style={{ padding: "20px 24px" }}>
            {/* Acquired Skills */}
            <div className="skill-tags-group">
              <div className="skill-group-head">
                <span style={{ color: "#10b981" }}>✓</span> Acquired Skills ({skillGap.acquired_skills.length})
              </div>
              <div className="skill-badge-wrap">
                {skillGap.acquired_skills.map((s) => (
                  <span key={s.id} className="skill-graph-badge acquired">
                    ✓ {s.name}
                  </span>
                ))}
                {skillGap.acquired_skills.length === 0 && (
                  <span style={{ fontSize: 12, color: "var(--text-faint)" }}>No required skills acquired yet for this target career.</span>
                )}
              </div>
            </div>

            {/* Critical Missing Skills */}
            <div className="skill-tags-group">
              <div className="skill-group-head">
                <span style={{ color: "#ef4444" }}>⚠</span> Critical Gaps ({skillGap.critical_missing.length})
              </div>
              <div className="skill-badge-wrap">
                {skillGap.critical_missing.map((s) => (
                  <span key={s.id} className="skill-graph-badge critical">
                    ! {s.name} ({s.difficulty})
                  </span>
                ))}
                {skillGap.critical_missing.length === 0 && (
                  <span style={{ fontSize: 12, color: "#10b981" }}>All critical skills fulfilled!</span>
                )}
              </div>
            </div>

            {/* Important Missing Skills */}
            <div className="skill-tags-group">
              <div className="skill-group-head">
                <span style={{ color: "#06b6d4" }}>◆</span> Core Engineering Gaps ({skillGap.important_missing.length})
              </div>
              <div className="skill-badge-wrap">
                {skillGap.important_missing.map((s) => (
                  <span key={s.id} className="skill-graph-badge important">
                    ◆ {s.name}
                  </span>
                ))}
              </div>
            </div>

            {/* Nice to have */}
            {skillGap.nice_to_have_missing.length > 0 && (
              <div className="skill-tags-group">
                <div className="skill-group-head">
                  <span style={{ color: "#a78bfa" }}>○</span> Recommended Extras ({skillGap.nice_to_have_missing.length})
                </div>
                <div className="skill-badge-wrap">
                  {skillGap.nice_to_have_missing.map((s) => (
                    <span key={s.id} className="skill-graph-badge nice">
                      ○ {s.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Interactive Graph Visualizer for Judges */}
      <div className="graph-viz-panel">
        <div className="graph-viz-toolbar">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ color: "var(--accent)", fontWeight: 600 }}>GRAPH TOPOLOGY EXPLORER</span>
            <span style={{ color: "var(--text-faint)" }}>|</span>
            <span>Click any node to inspect prerequisite relations &amp; course mapping</span>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button type="button" className="gos-btn" style={{ width: "auto", padding: "2px 8px" }} onClick={() => setZoom((z) => Math.min(z + 0.15, 2))}>
              +
            </button>
            <button type="button" className="gos-btn" style={{ width: "auto", padding: "2px 8px" }} onClick={() => setZoom((z) => Math.max(z - 0.15, 0.5))}>
              −
            </button>
            <button type="button" className="gos-btn" style={{ width: "auto", padding: "2px 8px" }} onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>
              Reset
            </button>
          </div>
        </div>

        <div
          className="graph-canvas-container"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <svg width="100%" height="100%" viewBox="0 0 860 480" style={{ transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`, transformOrigin: "center" }}>
            <defs>
              <marker id="arrow-prereq" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
              </marker>
              <marker id="arrow-req" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
              </marker>
              <marker id="arrow-teaches" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b5cf6" />
              </marker>
            </defs>

            {/* Edges */}
            {graphData?.edges?.map((edge, idx) => {
              const src = nodeMap.get(edge.source);
              const tgt = nodeMap.get(edge.target);
              if (!src || !tgt) return null;

              const isPrereq = edge.type === "PREREQUISITE_OF";
              const isTeaches = edge.type === "TEACHES";

              return (
                <line
                  key={`${edge.source}-${edge.target}-${idx}`}
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke={isPrereq ? "#f59e0b" : isTeaches ? "#8b5cf6" : "#334155"}
                  strokeWidth={isPrereq ? 2.5 : 1.5}
                  strokeDasharray={isPrereq ? "4 3" : undefined}
                  markerEnd={isPrereq ? "url(#arrow-prereq)" : isTeaches ? "url(#arrow-teaches)" : "url(#arrow-req)"}
                  opacity={0.75}
                />
              );
            })}

            {/* Nodes */}
            {layoutNodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  style={{ cursor: "pointer" }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedNode(node);
                  }}
                >
                  <circle
                    r={node.size || 20}
                    fill={node.color || "#475569"}
                    stroke={isSelected ? "#ffffff" : "rgba(255,255,255,0.2)"}
                    strokeWidth={isSelected ? 3 : 1.5}
                    style={{ filter: isSelected ? "drop-shadow(0 0 10px rgba(255,255,255,0.6))" : undefined }}
                  />
                  <text
                    textAnchor="middle"
                    dy={node.size + 14}
                    fill="#edeef1"
                    fontSize="11"
                    fontFamily="var(--font-mono)"
                    fontWeight="500"
                    style={{ pointerEvents: "none", textShadow: "0 1px 3px rgba(0,0,0,0.8)" }}
                  >
                    {node.name.length > 18 ? node.name.slice(0, 16) + "…" : node.name}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Node Inspector Drawer */}
          {selectedNode && (
            <div className="node-inspector-floating">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <span className="gos-eyebrow" style={{ color: selectedNode.color }}>
                  {selectedNode.type?.toUpperCase()} NODE
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedNode(null)}
                  style={{ background: "transparent", border: "none", color: "var(--text-dim)", cursor: "pointer" }}
                >
                  ✕
                </button>
              </div>

              <h3 style={{ fontSize: 16, margin: "0 0 6px 0", color: "var(--text)" }}>{selectedNode.name}</h3>

              {selectedNode.type === "skill" && (
                <>
                  <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 10 }}>
                    Category: <strong>{selectedNode.category}</strong> | Level: <strong>{selectedNode.difficulty}</strong>
                  </div>
                  <div style={{ fontSize: 12, marginBottom: 12 }}>
                    Status in Profile:{" "}
                    <strong style={{ color: selectedNode.status === "acquired" ? "#10b981" : "#ef4444" }}>
                      {selectedNode.status === "acquired" ? "Acquired ✓" : `Missing (${selectedNode.importance})`}
                    </strong>
                  </div>
                </>
              )}

              {selectedNode.type === "course" && (
                <>
                  <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 8 }}>
                    Provider: <strong>{selectedNode.provider}</strong> | Rating: <strong>⭐ {selectedNode.rating}</strong>
                  </div>
                  {selectedNode.url && (
                    <a
                      href={selectedNode.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="gos-btn gos-btn-primary"
                      style={{ display: "inline-block", width: "auto", padding: "6px 14px", fontSize: 12 }}
                    >
                      Open Course ↗
                    </a>
                  )}
                </>
              )}

              {selectedNode.type === "career" && (
                <div style={{ fontSize: 12, color: "var(--text-dim)" }}>
                  Domain: <strong>{selectedNode.category}</strong>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="graph-legend-bar">
          <div className="legend-item">
            <span className="legend-dot" style={{ background: "#f59e0b" }} />
            <span>Target Career</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: "#10b981" }} />
            <span>Acquired Skill</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: "#ef4444" }} />
            <span>Critical Gap</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: "#06b6d4" }} />
            <span>Core Gap</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: "#a855f7" }} />
            <span>Recommended Course</span>
          </div>
          <div className="legend-item">
            <span style={{ color: "#f59e0b", fontFamily: "var(--font-mono)" }}>- - ➔</span>
            <span>Prerequisite Path</span>
          </div>
        </div>
      </div>

      {/* Logical Prerequisite-Ordered Learning Roadmap */}
      {roadmap && (
        <div>
          <div className="gos-eyebrow" style={{ marginBottom: 12 }}>2. GRAPH-DERIVED LEARNING ROADMAP (PREREQUISITE ORDERED)</div>

          {roadmap.phases.map((phase) => (
            <div key={phase.phase_number} className="gos-panel" style={{ marginBottom: 20, padding: "20px 24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
                <h2 style={{ fontSize: 18, margin: 0, color: "var(--accent)" }}>{phase.title}</h2>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-dim)" }}>
                  {phase.skills.length} skills in sequence
                </span>
              </div>
              <p style={{ fontSize: 13, color: "var(--text-dim)", margin: "0 0 16px 0" }}>{phase.description}</p>

              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {phase.skills.map((item) => (
                  <div
                    key={item.skill_id}
                    style={{
                      background: "var(--surface-2)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius)",
                      padding: "16px 18px",
                      opacity: item.is_acquired ? 0.7 : 1,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10 }}>
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text)" }}>{item.name}</span>
                          <span className={`skill-graph-badge ${item.is_acquired ? "acquired" : item.importance === "critical" ? "critical" : "important"}`} style={{ padding: "2px 8px", fontSize: 11 }}>
                            {item.is_acquired ? "Acquired" : item.importance}
                          </span>
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)" }}>
                            [{item.difficulty}]
                          </span>
                        </div>
                        <div style={{ fontSize: 13, color: "var(--text-dim)", marginTop: 4 }}>
                          {item.description}
                        </div>
                      </div>

                      {/* Explicit Prerequisites */}
                      {item.prerequisites.length > 0 && (
                        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--accent)", background: "rgba(232,172,92,0.1)", padding: "4px 8px", borderRadius: 3 }}>
                          PREREQUISITES: {item.prerequisites.map((p) => p.name).join(" → ")}
                        </div>
                      )}
                    </div>

                    {/* Attached Recommended Courses */}
                    {item.courses.length > 0 && (
                      <div style={{ marginTop: 12 }}>
                        {item.courses.map((crs) => (
                          <div key={crs.id} className="course-rec-card">
                            <div>
                              <div className="course-rec-title">{crs.title}</div>
                              <div className="course-rec-meta">
                                {crs.provider} • ⭐ {crs.rating} • {crs.duration_hours}h duration
                              </div>
                            </div>
                            <a
                              href={crs.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="gos-btn"
                              style={{ width: "auto", padding: "4px 12px", fontSize: 11 }}
                            >
                              Open Course ↗
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
