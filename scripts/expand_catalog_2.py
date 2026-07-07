#!/usr/bin/env python3
"""Second expansion batch — deepens fields and adds a few more, toward ~3x depth.

Idempotent merge into catalog.json (dedups by id). Every brief names specific,
teachable, question-generable concepts. Re-runnable; existing ids untouched.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "content" / "catalog.json"

NEW_THEMES = [
    {"id": "earth-sciences", "title": "Earth & Space Sciences", "color": "#0891B2"},
    {"id": "humanities", "title": "History & Philosophy", "color": "#B45309"},
    {"id": "arts-music", "title": "Arts & Music", "color": "#DB2777"},
    {"id": "skilled-trades", "title": "Skilled Trades", "color": "#EA580C"},
    {"id": "fitness-wellness", "title": "Fitness & Wellness", "color": "#059669"},
    {"id": "transportation-logistics", "title": "Transportation & Logistics", "color": "#64748B"},
]

NEW_SUBTOPICS = [
    # ---- programming (more depth) ----
    ("rust-fundamentals", "Rust fundamentals", "programming", 20, "Rust essentials: ownership and borrowing, the borrow checker, move semantics, lifetimes conceptually, Result and Option, pattern matching, traits, why Rust prevents data races, when its strictness pays off."),
    ("api-design", "API design", "programming", 20, "Designing good APIs: REST resource modeling, versioning strategies, pagination and filtering, error responses, idempotency, consistency and naming, REST vs GraphQL vs gRPC tradeoffs, backward compatibility, good docs."),
    ("microservices-architecture", "Microservices", "programming", 20, "Microservices: monolith vs services tradeoffs, service boundaries, inter-service communication, distributed transactions and saga, service discovery, resilience (circuit breakers, retries), when a monolith is better, operational cost."),
    ("caching-strategies", "Caching strategies", "programming", 20, "Caching: cache-aside vs write-through vs write-back, TTL and eviction (LRU/LFU), cache invalidation problems, CDN caching, application vs database caching, stampede/thundering herd, staleness tradeoffs."),
    ("refactoring-tech-debt", "Refactoring & tech debt", "programming", 20, "Improving code: code smells, refactoring safely with tests, incremental vs big-bang, when to refactor vs rewrite, measuring and communicating tech debt, the boy-scout rule, refactoring anti-patterns."),
    ("event-driven-architecture", "Event-driven architecture", "programming", 20, "Async systems: events vs commands, pub/sub, event sourcing conceptually, eventual consistency, message ordering and delivery guarantees, dead-letter queues, choreography vs orchestration, debugging async flows."),
    # ---- ml-ai (more depth) ----
    ("transfer-learning", "Transfer learning", "ml-ai", 20, "Reusing models: pretraining and fine-tuning, feature extraction vs fine-tuning, frozen layers, domain adaptation, few-shot and zero-shot, when transfer helps vs hurts, catastrophic forgetting, foundation models."),
    ("data-labeling-annotation", "Data labeling", "ml-ai", 20, "Building training data: labeling guidelines, inter-annotator agreement, active learning to reduce labeling, weak supervision, label noise effects, class balance in labels, quality control, the cost of good labels."),
    ("ab-testing-for-ml", "Online ML evaluation", "ml-ai", 20, "Evaluating models live: offline vs online metrics gap, A/B testing models, guardrail metrics, interleaving, novelty and primacy effects, statistical power for ML tests, shadow mode, ramp-up strategies."),
    ("bayesian-ml", "Bayesian methods", "ml-ai", 20, "Bayesian ML: priors and posteriors in modeling, uncertainty quantification, credible intervals, when to be Bayesian, Bayesian A/B testing, hierarchical models conceptually, computational cost, interpretability benefits."),
    # ---- web-dev (more depth) ----
    ("state-management", "Frontend state management", "web-dev", 20, "Managing state: local vs global state, prop drilling, context, when to reach for a store (Redux/Zustand conceptually), derived vs source state, server vs client state, immutability, common state bugs."),
    ("browser-apis", "Browser APIs & the DOM", "web-dev", 20, "The browser platform: the DOM and events, event bubbling and delegation, localStorage vs cookies vs IndexedDB, fetch and CORS, the event loop and rendering, Web Workers, history and routing, common gotchas."),
    ("frontend-testing", "Frontend testing", "web-dev", 20, "Testing UIs: unit vs component vs e2e, testing user behavior not implementation, mocking network, accessibility in tests, snapshot testing pitfalls, flaky test causes, test pyramid for frontend, tools conceptually."),
    ("graphql", "GraphQL", "web-dev", 20, "GraphQL: schema and types, queries vs mutations vs subscriptions, resolvers, over- and under-fetching vs REST, the N+1 problem, caching challenges, pagination patterns, when REST is simpler."),
    # ---- data-eng (more depth) ----
    ("change-data-capture", "Change data capture", "data-eng", 20, "CDC: log-based vs query-based capture, why CDC beats batch polling, ordering and deduplication, schema evolution in streams, snapshot plus incremental, downstream materialization, common pitfalls."),
    ("sql-performance-tuning", "SQL performance tuning", "data-eng", 20, "Fast queries: reading execution plans, indexes and when they help/hurt, sargable predicates, join strategies, partition pruning, statistics, avoiding full scans, over-indexing costs, query rewriting."),
    ("data-lakes-lakehouse", "Data lakes & lakehouse", "data-eng", 20, "Lake architecture: object storage, file formats (Parquet/ORC), partitioning, schema-on-read, the small-files problem, table formats (Iceberg/Delta conceptually), lake vs warehouse vs lakehouse, governance challenges."),
    # ---- cybersecurity (more depth) ----
    ("threat-modeling", "Threat modeling", "cybersecurity", 20, "Anticipating attacks: STRIDE, attack trees, trust boundaries, data flow diagrams, ranking risks, abuse cases, threat modeling in the SDLC, keeping it lightweight, common blind spots."),
    ("malware-analysis", "Malware & threats", "cybersecurity", 20, "Understanding threats: malware types (virus/worm/trojan/ransomware), the kill chain, C2 conceptually, static vs dynamic analysis basics, indicators of compromise, sandboxing, defensive takeaways only."),
    ("privacy-engineering", "Privacy engineering", "cybersecurity", 20, "Building for privacy: data minimization, anonymization vs pseudonymization, differential privacy conceptually, consent and purpose limitation, privacy by design, re-identification risk, PII inventory, retention."),
    # ---- design (more depth) ----
    ("design-thinking", "Design thinking", "design", 20, "Human-centered process: empathize/define/ideate/prototype/test, problem framing, divergent vs convergent, how-might-we, reframing, jobs-to-be-done, avoiding solutioning too early, iteration."),
    ("iconography-illustration", "Iconography & illustration", "design", 20, "Visual language: icon consistency and metaphor, grid and optical alignment, illustration styles, when icons help vs confuse, scalability, cultural meaning, illustration in product, maintaining a set."),
    ("data-visualization-design", "Data visualization", "design", 20, "Charts that inform: choosing encodings, the data-ink ratio, color for data, avoiding chartjunk and distortion, annotation, small multiples, accessibility in charts, when a table beats a chart."),
    # ---- writing-content (more depth) ----
    ("content-strategy", "Content strategy", "writing-content", 20, "Strategic content: audience and goals, content audits, editorial governance, structured content and reuse, voice and tone systems, content lifecycle, measuring content, aligning content to the funnel."),
    ("ux-writing", "UX writing", "writing-content", 20, "Words in interfaces: microcopy, button and error text, clarity under space constraints, voice consistency, progressive disclosure, writing for scanning, localization-friendly copy, testing microcopy."),
    ("journalism-fundamentals", "Journalism fundamentals", "writing-content", 20, "Reporting: the inverted pyramid, the five Ws, sourcing and verification, on vs off the record, leads and nut graphs, objectivity vs balance, fact-checking, ethics in reporting."),
    # ---- earth-sciences (new) ----
    ("geology-basics", "Geology", "earth-sciences", 20, "Earth's structure: rock cycle (igneous/sedimentary/metamorphic), plate tectonics, earthquakes and volcanoes, geologic time, weathering and erosion, minerals, reading the rock record."),
    ("meteorology-weather", "Meteorology", "earth-sciences", 20, "Weather: air pressure and fronts, humidity and dew point, cloud types, how storms form, the water cycle, forecasting basics and uncertainty, weather vs climate, reading a weather map."),
    ("oceanography", "Oceanography", "earth-sciences", 20, "The oceans: currents and circulation, tides, salinity and density, marine ecosystems, the ocean's role in climate, waves, coastal processes, ocean acidification."),
    ("environmental-science", "Environmental science", "earth-sciences", 20, "Human-environment systems: biogeochemical cycles, pollution types and pathways, resource depletion, biodiversity loss, environmental impact assessment, sustainability tradeoffs, ecosystem services."),
    ("climate-systems", "Climate systems", "earth-sciences", 20, "How climate works: energy balance and albedo, ocean-atmosphere coupling, natural variability (El Nino), feedbacks, paleoclimate evidence, models and scenarios, distinguishing weather from climate signals."),
    # ---- humanities (new) ----
    ("world-history-basics", "World history", "humanities", 20, "Major arcs: agricultural and industrial revolutions, major civilizations, causes of historical change, primary vs secondary sources, historiography basics, cause and contingency, avoiding presentism."),
    ("philosophy-basics", "Philosophy", "humanities", 20, "Big questions: epistemology (how we know), metaphysics basics, major ethical theories, logic and arguments, free will debate, philosophy of mind intro, reading arguments charitably."),
    ("ethics-applied", "Applied ethics", "humanities", 20, "Ethics in practice: consequentialism vs deontology vs virtue ethics, moral dilemmas, professional ethics, the trolley problem and its lessons, moral relativism debate, ethical reasoning steps, technology ethics."),
    ("art-history", "Art history", "humanities", 20, "Art across time: major movements (Renaissance to modern), reading a composition, medium and technique, form vs content, patronage and context, iconography, why art history matters."),
    ("world-religions", "World religions", "humanities", 20, "Comparative religion: major traditions' core beliefs and practices, sacred texts, ritual and community, the academic study of religion (not advocacy), secularization, religious literacy for a global world."),
    # ---- arts-music (new) ----
    ("music-theory", "Music theory", "arts-music", 20, "Music fundamentals: notes and intervals, scales and keys, chords and progressions, rhythm and meter, the circle of fifths, major vs minor, reading notation, tension and resolution."),
    ("music-production", "Music production", "arts-music", 20, "Making music: DAW workflow, recording and MIDI, mixing (EQ/compression/reverb), arrangement, the frequency spectrum, gain staging, mastering basics, why arrangement beats gear."),
    ("music-performance", "Music performance & practice", "arts-music", 20, "Getting better: deliberate practice, sight-reading, ear training, technique vs musicality, performance nerves, practice scheduling, feedback loops, why slow practice works."),
    ("creative-writing", "Creative writing", "arts-music", 20, "Fiction and poetry: character and voice, scene vs summary, dialogue, imagery and metaphor, point of view, revision, showing not telling, finding your voice."),
    # ---- skilled-trades (new) ----
    ("electrical-trade", "Electrical trade", "skilled-trades", 20, "Practical wiring: circuits and loads, breakers and GFCI, wire gauge and ampacity, grounding and bonding, series vs parallel in practice, code basics conceptually, safety and lockout, common faults."),
    ("plumbing-basics", "Plumbing", "skilled-trades", 20, "Water systems: supply vs drain-waste-vent, pipe materials, pressure and flow, traps and venting, common leaks and fixes, water heaters, backflow prevention, why slope matters."),
    ("hvac-fundamentals", "HVAC", "skilled-trades", 20, "Heating and cooling: the refrigeration cycle, heat load calculation, airflow and ducting, thermostats and controls, filters and maintenance, efficiency ratings (SEER), common failures, comfort factors."),
    ("automotive-basics", "Automotive fundamentals", "skilled-trades", 20, "How cars work: the four-stroke engine, drivetrain, brakes and hydraulics, the electrical system and battery, diagnostics (OBD), maintenance intervals, EV vs ICE basics, common warning signs."),
    ("welding-fabrication", "Welding & fabrication", "skilled-trades", 20, "Joining metal: welding processes (MIG/TIG/stick) conceptually, heat and penetration, joint types, metal properties, distortion and warping, safety and PPE, reading weld symbols, quality of a weld."),
    # ---- fitness-wellness (new) ----
    ("exercise-science", "Exercise science", "fitness-wellness", 20, "Training the body: energy systems, progressive overload, hypertrophy vs strength vs endurance, recovery and adaptation, common form errors, periodization, the specificity principle, evidence vs bro-science."),
    ("nutrition-fitness", "Nutrition for performance", "fitness-wellness", 20, "Fueling training: energy balance, protein needs, macros and timing, hydration, supplements evidence vs hype, weight management honestly, nutrient density, common diet myths."),
    ("sleep-recovery", "Sleep & recovery", "fitness-wellness", 20, "Rest and repair: sleep stages and cycles, circadian rhythm, sleep hygiene evidence, recovery modalities, overtraining signs, stress and cortisol, the role of rest in adaptation, sleep myths."),
    ("mental-wellness-practices", "Mental wellness practices", "fitness-wellness", 20, "Evidence-based wellbeing: stress management, mindfulness and its evidence, cognitive reframing, building habits, work-life boundaries, burnout recovery, when to seek help, self-care vs avoidance."),
    # ---- transportation-logistics (new) ----
    ("logistics-fundamentals", "Logistics fundamentals", "transportation-logistics", 20, "Moving goods: transportation modes and tradeoffs, freight and incoterms basics, warehousing, hub-and-spoke vs point-to-point, last-mile challenges, load optimization, transit time vs cost, tracking and visibility."),
    ("fleet-management", "Fleet management", "transportation-logistics", 20, "Running a fleet: route optimization, vehicle maintenance scheduling, fuel and cost management, driver safety and hours, telematics, utilization metrics, total cost of ownership, EV transition considerations."),
    ("aviation-basics", "Aviation basics", "transportation-logistics", 20, "How flight works: the four forces, lift and airfoils, basic flight controls, air traffic and airspace conceptually, weather's role, navigation basics, why aviation is so safe (systems thinking)."),
    ("maritime-shipping", "Maritime & shipping", "transportation-logistics", 20, "Global shipping: container logistics, ports and drayage, the shipping cost cycle, incoterms, transit times, chokepoints, why 90% of trade goes by sea, supply chain fragility."),
    # ---- finance (more depth) ----
    ("venture-capital", "Venture capital & startups", "finance", 20, "Startup finance: how VC works, dilution and cap tables, valuation (pre/post money), rounds and terms, liquidation preferences, the power law of returns, dilution math, exit paths."),
    ("options-trading", "Options & volatility", "finance", 20, "Options deeper: the Greeks conceptually (delta/gamma/theta/vega), implied vs realized volatility, spreads, covered calls vs naked, assignment risk, why most options expire worthless, leverage danger."),
    ("macroeconomic-indicators", "Reading the economy", "finance", 20, "Market-moving data: GDP, CPI, employment reports, yield curve signals, central bank meetings, leading vs lagging indicators, how markets react to data, separating signal from noise."),
    # ---- business (more depth) ----
    ("okrs-goal-setting", "OKRs & goal setting", "business", 20, "Aligning goals: objectives vs key results, outcome vs output KRs, cascading vs autonomy, ambition and stretch, common OKR failures, measuring what matters, quarterly cadence, OKRs vs KPIs."),
    ("business-ethics", "Business ethics", "business", 20, "Ethics in business: stakeholder vs shareholder views, conflicts of interest, whistleblowing, corporate responsibility vs greenwashing, ethical decision frameworks, short-term vs long-term, famous failures."),
    ("innovation-management", "Innovation management", "business", 20, "Managing innovation: exploration vs exploitation, disruptive vs sustaining, stage-gate vs lean, the innovator's dilemma, portfolio balance, killing projects, measuring innovation, culture's role."),
    # ---- product (more depth) ----
    ("technical-product-management", "Technical PM", "product", 20, "PM for technical products: working with engineers, technical tradeoffs, API and platform products, technical debt prioritization, feasibility assessment, reading system design, spec writing, scoping under uncertainty."),
    ("product-discovery", "Product discovery", "product", 20, "Finding what to build: continuous discovery, opportunity solution trees, assumption testing, the riskiest assumption, prototype to learn, avoiding confirmation bias, interviewing for problems, discovery vs delivery balance."),
    # ---- communication (more depth) ----
    ("storytelling-business", "Storytelling for business", "communication", 20, "Narrative at work: the pitch arc, structuring a persuasive case, data plus story, the curse of knowledge, tailoring to audience, memorable messages, executive communication, story vs data balance."),
    ("influence-persuasion", "Influence & persuasion", "communication", 20, "Ethical influence: reciprocity, commitment, social proof, authority, liking, scarcity (Cialdini), framing, building credibility, persuasion vs manipulation, influence without authority."),
    # ---- healthcare (more depth) ----
    ("health-informatics", "Health informatics", "healthcare", 20, "Health IT: EHR workflows, interoperability (HL7/FHIR conceptually), clinical decision support, coding systems (ICD/CPT), data quality in clinical data, alert fatigue, privacy in health IT."),
    ("global-health", "Global & population health", "healthcare", 20, "Health at scale: burden of disease, health systems compared, determinants of health, screening tradeoffs at population level, vaccination and herd immunity, health equity, cost-effectiveness of interventions."),
    # ---- economics (more depth) ----
    ("monetary-policy", "Monetary policy & central banking", "economics", 20, "Central banks: interest rate tools, inflation targeting, quantitative easing conceptually, the transmission mechanism, independence, the dual mandate, liquidity traps, why central banks matter to everyone."),
    ("public-finance", "Public finance & taxation", "economics", 20, "Government economics: taxes and deadweight loss, progressive vs regressive, public goods, deficits and debt, fiscal multipliers, tax incidence, cost-benefit of spending, intergenerational equity."),
    # ---- math (more depth) ----
    ("probability-theory", "Probability theory", "math", 20, "Rigorous probability: sample spaces and events, combinatorial probability, conditional probability and Bayes, random variables, expectation and variance, common distributions, the law of large numbers, independence subtleties."),
    ("graph-theory", "Graph theory", "math", 20, "Graphs and networks: vertices and edges, directed vs undirected, paths and cycles, trees, connectivity, shortest paths, graph coloring, applications (networks, scheduling), NP-hardness intuition."),
]

# id, title, blurb, [subtopic ids]
NEW_TRACKS = [
    ("rust-developer", "Rust / Systems Developer", "Ownership, systems thinking, and safe low-level code.", ["rust-fundamentals", "concurrency-parallelism", "data-structures", "system-design-basics", "debugging-troubleshooting", "linux-command-line"]),
    ("platform-architect", "Software Architect", "Systems, services, and the big technical decisions.", ["system-design-basics", "microservices-architecture", "api-design", "caching-strategies", "event-driven-architecture", "database-design"]),
    ("staff-engineer", "Staff / Senior Engineer", "Depth, breadth, and the judgment interviews probe at senior level.", ["system-design-basics", "refactoring-tech-debt", "code-review-collaboration", "algorithms-basics", "debugging-troubleshooting", "clean-code-testing"]),
    ("web3-developer", "Web3 / Blockchain Developer", "Blockchain concepts, security, and decentralized apps.", ["crypto-blockchain", "cryptography-basics", "web-security-basics", "javascript-fundamentals", "apis-http", "system-design-basics"]),
    ("game-designer", "Game Designer", "Systems, levels, and the craft of fun.", ["game-design-fundamentals", "level-design", "game-physics-math", "user-research", "motivation-habits", "product-analytics"]),
    ("meteorologist", "Meteorology & Climate", "Weather, climate systems, and the science of the atmosphere.", ["meteorology-weather", "climate-systems", "climate-science-basics", "physics-thermodynamics", "statistical-inference", "data-storytelling"]),
    ("environmental-scientist", "Environmental Scientist", "Ecosystems, climate, and human impact with the data to prove it.", ["environmental-science", "ecology-environment", "climate-science-basics", "statistical-inference", "environmental-economics", "geology-basics"]),
    ("historian", "History & Humanities", "Sources, arguments, and reasoning about the past.", ["world-history-basics", "philosophy-basics", "critical-thinking", "writing-fundamentals", "world-religions", "art-history"]),
    ("philosopher-ethicist", "Ethics & Philosophy", "Arguments, ethics, and clear reasoning.", ["philosophy-basics", "ethics-applied", "critical-thinking", "logic-proofs", "business-ethics", "medical-ethics"]),
    ("musician", "Musician / Producer", "Theory, production, and performance.", ["music-theory", "music-production", "music-performance", "audio-podcasting", "creative-writing", "motivation-habits"]),
    ("electrician", "Electrician", "Wiring, code, safety, and the electrical trade.", ["electrical-trade", "electronics-basics", "digital-logic", "industrial-safety", "physics-electromagnetism", "hvac-fundamentals"]),
    ("plumber", "Plumber", "Water systems, fixtures, and the plumbing trade.", ["plumbing-basics", "hvac-fundamentals", "building-systems-mep", "industrial-safety", "construction-management", "physics-thermodynamics"]),
    ("hvac-technician", "HVAC Technician", "Heating, cooling, refrigeration, and controls.", ["hvac-fundamentals", "electrical-trade", "physics-thermodynamics", "control-systems", "industrial-safety", "building-systems-mep"]),
    ("automotive-technician", "Automotive Technician", "Engines, systems, diagnostics, and repair.", ["automotive-basics", "electronics-basics", "mechanical-engineering-basics", "control-systems", "industrial-safety", "debugging-troubleshooting"]),
    ("personal-trainer", "Personal Trainer / Coach", "Exercise science, nutrition, and coaching that works.", ["exercise-science", "nutrition-fitness", "sleep-recovery", "human-anatomy-physiology", "motivation-habits", "emotional-intelligence"]),
    ("nutritionist", "Nutrition & Dietetics", "Evidence-based nutrition for health and performance.", ["nutrition-science", "nutrition-fitness", "human-anatomy-physiology", "statistical-inference", "public-health", "critical-thinking"]),
    ("wellness-coach", "Wellness Coach", "Habits, mental wellness, and sustainable change.", ["mental-wellness-practices", "motivation-habits", "sleep-recovery", "emotional-intelligence", "positive-psychology", "learning-science"]),
    ("logistics-coordinator", "Logistics Coordinator", "Freight, fleets, and moving goods efficiently.", ["logistics-fundamentals", "fleet-management", "supply-chain-basics", "inventory-logistics", "operations-management", "forecasting-basics"]),
    ("venture-analyst", "Venture / Startup Analyst", "Startup finance, models, and market judgment.", ["venture-capital", "financial-modeling", "unit-economics", "business-model-design", "competitive-strategy", "go-to-market"]),
    ("trader", "Trader / Markets", "Options, volatility, and reading the economy.", ["options-trading", "derivatives-basics", "macroeconomic-indicators", "probability-basics", "risk-management", "portfolio-risk-return"]),
    ("economist-macro", "Macro / Central Bank Economist", "Monetary policy, public finance, and the big picture.", ["monetary-policy", "public-finance", "macroeconomics", "macroeconomic-indicators", "statistical-inference", "data-storytelling"]),
    ("journalist", "Journalist / Reporter", "Reporting, verification, and telling true stories.", ["journalism-fundamentals", "writing-fundamentals", "critical-thinking", "data-storytelling", "editing-proofreading", "ethics-applied"]),
    ("content-designer", "Content Designer / UX Writer", "Words in products, content strategy, and clarity.", ["ux-writing", "content-strategy", "writing-fundamentals", "ux-design-principles", "user-research", "web-accessibility"]),
    ("innovation-lead", "Innovation / Strategy Lead", "Frameworks, innovation, and business models.", ["innovation-management", "competitive-strategy", "business-model-design", "strategy-frameworks", "critical-thinking", "go-to-market"]),
    ("health-informatics-analyst", "Health Informatics Analyst", "Clinical data, EHRs, and health IT systems.", ["health-informatics", "healthcare-analytics", "health-data-privacy", "sql-querying", "descriptive-stats", "medical-terminology"]),
    ("aviation-professional", "Aviation Professional", "How flight, airspace, and aviation systems work.", ["aviation-basics", "physics-mechanics", "control-systems", "networking-fundamentals", "risk-stakeholder-mgmt", "critical-thinking"]),
]


def main():
    cat = json.loads(CATALOG.read_text())
    theme_ids = {t["id"] for t in cat["themes"]}
    for t in NEW_THEMES:
        if t["id"] not in theme_ids:
            cat["themes"].append(t); theme_ids.add(t["id"])

    sub_ids = {s["id"] for s in cat["subtopics"]}
    for sid, title, theme, size, brief in NEW_SUBTOPICS:
        if sid not in sub_ids:
            cat["subtopics"].append({"id": sid, "title": title, "theme": theme, "size": size, "brief": brief})
            sub_ids.add(sid)

    track_ids = {t["id"] for t in cat["tracks"]}
    valid = {s["id"] for s in cat["subtopics"]}
    for tid, title, blurb, subs in NEW_TRACKS:
        if tid in track_ids:
            continue
        missing = [s for s in subs if s not in valid]
        if missing:
            print(f"  WARN track {tid} references missing subtopics: {missing}")
        cat["tracks"].append({"id": tid, "title": title, "blurb": blurb, "subtopics": subs})
        track_ids.add(tid)

    cat["version"] = cat.get("version", 4) + 1
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=1))
    print(f"catalog now: {len(cat['themes'])} themes, {len(cat['subtopics'])} subtopics, {len(cat['tracks'])} tracks")


if __name__ == "__main__":
    main()
