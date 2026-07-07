#!/usr/bin/env python3
"""Merge a large expansion into content/catalog.json (idempotent; dedups by id).

Adds new fields (themes), deepens existing fields with more subtopics, and adds
career tracks. Every brief names the specific concepts to cover so the generator
produces real, teachable questions. Safe to re-run: existing ids are untouched.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "content" / "catalog.json"

NEW_THEMES = [
    {"id": "design", "title": "Design & Creative", "color": "#DB2777"},
    {"id": "writing-content", "title": "Writing & Editing", "color": "#0284C7"},
    {"id": "teaching-education", "title": "Education & Teaching", "color": "#65A30D"},
    {"id": "physical-sciences", "title": "Physics & Chemistry", "color": "#7C3AED"},
    {"id": "life-sciences", "title": "Biology & Life Sciences", "color": "#059669"},
    {"id": "engineering", "title": "Engineering Disciplines", "color": "#EA580C"},
    {"id": "hardware-embedded", "title": "Hardware & Embedded", "color": "#64748B"},
    {"id": "game-dev", "title": "Game Development", "color": "#C026D3"},
    {"id": "media-production", "title": "Media & Production", "color": "#DB2777"},
    {"id": "sales", "title": "Sales", "color": "#E11D48"},
    {"id": "customer-experience", "title": "Customer Success & Support", "color": "#0891B2"},
    {"id": "real-estate", "title": "Real Estate & Property", "color": "#D97706"},
    {"id": "hospitality-tourism", "title": "Hospitality & Tourism", "color": "#0284C7"},
    {"id": "manufacturing", "title": "Manufacturing & Industry", "color": "#EA580C"},
    {"id": "public-policy", "title": "Government & Public Policy", "color": "#64748B"},
    {"id": "languages-linguistics", "title": "Languages & Linguistics", "color": "#7C3AED"},
    {"id": "architecture-construction", "title": "Architecture & Construction", "color": "#65A30D"},
    {"id": "agriculture-food", "title": "Agriculture & Food Science", "color": "#059669"},
]

# id, title, theme, size, brief
NEW_SUBTOPICS = [
    # ---- programming (deepen) ----
    ("java-fundamentals", "Java fundamentals", "programming", 20, "Core Java: primitives vs objects, references and equals vs ==, collections (List/Map/Set), exceptions checked vs unchecked, generics basics, interfaces vs abstract classes, autoboxing pitfalls, the JVM and garbage collection conceptually."),
    ("cpp-fundamentals", "C++ fundamentals", "programming", 20, "Core C++: value vs reference vs pointer, stack vs heap, RAII and destructors, references, const correctness, the rule of three/five conceptually, undefined behavior examples, templates basics, why manual memory matters."),
    ("go-fundamentals", "Go fundamentals", "programming", 20, "Go essentials: goroutines and channels, error-as-value handling, slices vs arrays, interfaces (implicit), defer, structs and methods, the zero value, why Go omits exceptions and inheritance, common concurrency mistakes."),
    ("concurrency-parallelism", "Concurrency & parallelism", "programming", 20, "Concurrency concepts: threads vs processes, race conditions and data races, locks/mutexes and deadlock, atomicity, async vs parallel, thread pools, the actor model conceptually, why shared mutable state is hard."),
    ("functional-programming", "Functional programming", "programming", 20, "FP concepts: pure functions and side effects, immutability, higher-order functions, map/filter/reduce, closures, recursion vs iteration, referential transparency, why FP aids testability, when imperative is clearer."),
    ("debugging-troubleshooting", "Debugging & troubleshooting", "programming", 20, "Systematic debugging: reading stack traces, reproducing bugs reliably, bisecting, hypothesis-driven debugging, print vs debugger vs logging, rubber-duck method, off-by-one and boundary bugs, root cause vs symptom."),
    ("system-design-basics", "System design basics", "programming", 30, "Designing systems: scaling vertical vs horizontal, load balancing, caching layers and invalidation, database replication and sharding, CAP tradeoffs, message queues, rate limiting, idempotency, back-of-envelope capacity estimation."),
    ("mobile-dev-basics", "Mobile development basics", "programming", 20, "Mobile app concepts: native vs cross-platform tradeoffs, app lifecycle and state, responsive layouts for varied screens, permissions and privacy, offline-first and sync, push notifications, app store review basics, battery and performance."),
    ("shell-scripting", "Shell scripting", "programming", 20, "Bash scripting: variables and quoting pitfalls, exit codes and set -e, conditionals and loops, functions, command substitution, pipes and redirection in scripts, arguments and getopts, when to reach for Python instead."),
    ("code-review-collaboration", "Code review & collaboration", "programming", 20, "Working on a team codebase: reviewing for correctness vs style, giving actionable feedback, small PRs, reading unfamiliar code, pair programming, documentation that helps, handling disagreement, review anti-patterns (nitpicking, rubber-stamping)."),
    # ---- ml-ai (deepen) ----
    ("computer-vision", "Computer vision", "ml-ai", 20, "Vision fundamentals: pixels and channels, convolution intuition, CNN feature hierarchies, image classification vs detection vs segmentation, data augmentation, transfer learning for images, common failure modes, evaluation metrics for detection."),
    ("reinforcement-learning", "Reinforcement learning", "ml-ai", 20, "RL concepts: agent/environment/reward loop, exploration vs exploitation, states/actions/policies, value functions and Q-learning intuition, reward shaping pitfalls, on- vs off-policy, when RL fits vs supervised learning, sample-efficiency problems."),
    ("generative-ai", "Generative AI", "ml-ai", 30, "Generative models: how autoregressive text generation works, diffusion for images conceptually, tokens and sampling (temperature, top-p), hallucination causes, fine-tuning vs prompting vs RAG, evaluation of generative output, watermarking and provenance, misuse risks."),
    ("ai-agents", "AI agents & tool use", "ml-ai", 20, "LLM agents: tool/function calling, the plan-act-observe loop, memory and context management, multi-step reasoning, when agents fail (loops, hallucinated tools), guardrails, human-in-the-loop, evaluating agent reliability, cost/latency tradeoffs."),
    ("embeddings-vector-search", "Embeddings & vector search", "ml-ai", 20, "Semantic search: what embeddings represent, cosine similarity, vector databases and ANN indexes, chunking strategies for RAG, hybrid keyword+vector retrieval, reranking, embedding drift, evaluating retrieval quality."),
    ("model-interpretability", "Model interpretability", "ml-ai", 20, "Explainable ML: feature importance vs SHAP vs LIME conceptually, global vs local explanations, partial dependence, why black-box models need explanation, correlation in importances, fooling explanations, interpretability-accuracy tradeoff."),
    ("ml-fairness-ethics", "ML fairness & ethics", "ml-ai", 20, "Responsible ML: sources of bias (data, labels, proxy features), fairness definitions and their conflicts, disparate impact, feedback loops, privacy in training data, consent, dual-use, when not to build a model."),
    ("gradient-boosting", "Gradient boosting & trees", "ml-ai", 20, "Tree ensembles: decision tree splits, why single trees overfit, bagging vs boosting, random forests, gradient boosting (XGBoost/LightGBM) intuition, feature importance from trees, hyperparameters that matter, tabular data strengths."),
    ("anomaly-detection", "Anomaly detection", "ml-ai", 20, "Finding outliers: statistical vs ML approaches, unsupervised vs supervised anomaly detection, precision-recall under extreme imbalance, seasonality in anomaly detection, alert fatigue, isolation forest intuition, evaluating rare-event detectors."),
    ("ml-system-design", "ML system design", "ml-ai", 20, "Designing ML systems: framing a business problem as ML, offline vs online metrics, training-serving skew, feature pipelines, model retraining cadence, A/B testing models, fallback behavior, cost and latency budgets."),
    # ---- data-eng (deepen) ----
    ("dbt-analytics-eng", "Analytics engineering (dbt)", "data-eng", 20, "Analytics engineering: transformation as code, staging vs marts layers, models and refs, tests and documentation, incremental models, idempotent rebuilds, semantic consistency, the analytics-engineer role between data eng and analysis."),
    ("data-modeling", "Data modeling", "data-eng", 20, "Modeling data: conceptual vs logical vs physical, dimensional (Kimball) vs normalized (Inmon), fact grain, conformed dimensions, junk and degenerate dimensions, one-big-table tradeoffs, modeling for change."),
    ("data-observability", "Data observability", "data-eng", 20, "Trustworthy data: freshness/volume/schema/distribution monitors, anomaly alerting, lineage for impact analysis, SLAs on data, incident response for broken pipelines, silent data corruption, testing at ingestion vs transformation."),
    ("realtime-analytics", "Real-time analytics", "data-eng", 20, "Streaming analytics: event vs processing time, windowing (tumbling/sliding/session), materialized views, exactly-once vs at-least-once, lambda vs kappa architecture, latency-freshness-cost tradeoffs, when batch is fine."),
    # ---- cloud-devops (deepen) ----
    ("serverless-architecture", "Serverless architecture", "cloud-devops", 20, "Serverless: functions-as-a-service model, cold starts, statelessness, event-driven design, when serverless saves vs costs money, vendor lock-in, timeout and concurrency limits, orchestrating functions, observability challenges."),
    ("networking-fundamentals", "Networking fundamentals", "cloud-devops", 20, "Networking: OSI layers pragmatically, IP/subnets/CIDR, TCP vs UDP, DNS resolution, HTTP/HTTPS, ports and NAT, load balancers, latency vs bandwidth, common connectivity debugging (ping/traceroute/dig)."),
    ("cost-optimization-cloud", "Cloud cost optimization", "cloud-devops", 20, "FinOps: on-demand vs reserved vs spot, right-sizing, autoscaling economics, storage tiering, egress costs surprises, tagging and cost allocation, idle-resource waste, the cost of over-provisioning vs downtime."),
    ("platform-engineering", "Platform engineering", "cloud-devops", 20, "Internal platforms: golden paths, self-service infrastructure, developer experience, paved roads vs guardrails, internal developer portals, reducing cognitive load, platform-as-product thinking, when a platform team is premature."),
    # ---- cybersecurity (deepen) ----
    ("application-security", "Application security", "cybersecurity", 20, "AppSec: OWASP Top 10 beyond XSS/SQLi (SSRF, deserialization, broken access control), secure SDLC, threat modeling (STRIDE), secrets management, dependency vulnerabilities, security code review, defense in depth in code."),
    ("penetration-testing", "Penetration testing", "cybersecurity", 20, "Ethical hacking concepts: recon and enumeration, the attack lifecycle, common vulnerability classes, privilege escalation conceptually, reporting and remediation, scope and rules of engagement, red vs blue vs purple team, authorized testing only."),
    ("cloud-security", "Cloud security", "cybersecurity", 20, "Securing cloud: shared responsibility model, IAM least privilege and misconfigurations, public bucket exposure, security groups vs NACLs, secrets in cloud, encryption at rest/in transit, logging and audit trails, CSPM concepts."),
    ("security-operations-siem", "Security operations (SOC)", "cybersecurity", 20, "SOC work: log aggregation and SIEM, detection rules and tuning, true vs false positives, alert triage and enrichment, threat intelligence, MITRE ATT&CK framework, EDR concepts, avoiding alert fatigue."),
    ("digital-forensics", "Digital forensics", "cybersecurity", 20, "Forensics basics: chain of custody, evidence preservation and imaging, volatile vs persistent data order, timeline analysis, artifacts (logs, registry, memory), anti-forensics awareness, when to call professionals, legal admissibility."),
    # ---- design (new) ----
    ("design-principles", "Design principles", "design", 30, "Visual design foundations: hierarchy, contrast, alignment, repetition, proximity (CRAP), balance and tension, focal points, gestalt principles, the role of whitespace, when to break the rules purposefully."),
    ("typography", "Typography", "design", 20, "Type in practice: serif vs sans vs mono uses, type scale and rhythm, line length and leading, pairing typefaces, kerning/tracking, hierarchy through weight and size, readability vs legibility, common type crimes."),
    ("color-theory", "Color theory", "design", 20, "Color for designers: hue/saturation/value, color harmonies, warm vs cool, contrast and accessibility (WCAG), color meaning and culture, palettes that scale, color in data viz, avoiding color-alone signaling."),
    ("layout-composition", "Layout & composition", "design", 20, "Composition: grid systems and columns, the rule of thirds, visual flow and scanning patterns, negative space, alignment systems, responsive composition, focal hierarchy, density vs breathing room."),
    ("branding-identity", "Brand identity design", "design", 20, "Identity design: logo types and when each fits, brand guidelines, consistency across touchpoints, distinctive assets, scalability and simplicity, brand voice in visuals, rebrand risks, mood boards to system."),
    ("motion-design", "Motion & animation", "design", 20, "Motion design: purpose over decoration, easing and timing, the 12 principles adapted, micro-interactions, transitions that orient, performance and reduced-motion, storytelling through motion, when animation distracts."),
    ("design-critique", "Design critique & process", "design", 20, "Design practice: giving and receiving critique, separating opinion from principle, design rationale, iteration and divergence/convergence, presenting work, stakeholder feedback, defending decisions with reasons not taste."),
    # ---- writing-content (new) ----
    ("writing-fundamentals", "Writing fundamentals", "writing-content", 30, "Clear writing: sentence structure and variety, active vs passive voice, concision and cutting, paragraph unity, transitions, avoiding jargon, showing vs telling, the revision mindset, reading level awareness."),
    ("copywriting", "Copywriting", "writing-content", 20, "Persuasive copy: features vs benefits, headlines that work, calls to action, voice and tone, addressing objections, social proof, urgency honestly, the AIDA model, avoiding hype that erodes trust."),
    ("editing-proofreading", "Editing & proofreading", "writing-content", 20, "Editing craft: developmental vs line vs copy editing, common grammar errors, style guide consistency, clarity and flow edits, killing your darlings, fact-checking, proofreading technique, editing others' work respectfully."),
    ("storytelling-narrative", "Storytelling & narrative", "writing-content", 20, "Narrative craft: story structure (setup/conflict/resolution), character and stakes, show don't tell, pacing, the hook, narrative arc in nonfiction, emotional resonance, applying story to business communication."),
    ("technical-writing", "Technical writing", "writing-content", 20, "Docs that work: knowing your audience, task-based vs reference docs, step clarity, screenshots and code samples, information architecture, minimalism, testing docs with real users, keeping docs current."),
    ("grammar-usage", "Grammar & usage", "writing-content", 20, "English mechanics: subject-verb agreement, pronoun clarity, comma rules, its vs it's and common confusions, parallel structure, modifiers and dangling participles, tense consistency, descriptivism vs prescriptivism."),
    # ---- teaching-education (new) ----
    ("instructional-design", "Instructional design", "teaching-education", 20, "Designing learning: learning objectives (Bloom's taxonomy), backward design, scaffolding, chunking, cognitive load management, formative vs summative assessment, ADDIE model, aligning assessment to objectives."),
    ("pedagogy-teaching-methods", "Teaching methods", "teaching-education", 20, "Effective teaching: direct instruction vs inquiry, active learning, questioning techniques, wait time, differentiation, checking for understanding, managing a classroom, feedback that improves learning."),
    ("assessment-evaluation", "Assessment & evaluation", "teaching-education", 20, "Assessing learning: validity and reliability, formative vs summative, rubrics, avoiding bias in grading, standardized test limits, authentic assessment, feedback vs grades, assessment for vs of learning."),
    ("learning-theory", "Learning theory", "teaching-education", 20, "How people learn: behaviorism/cognitivism/constructivism, working memory limits, spacing and retrieval, transfer of learning, motivation (intrinsic/extrinsic), Zone of Proximal Development, misconceptions and conceptual change."),
    ("edtech-online-learning", "EdTech & online learning", "teaching-education", 20, "Digital learning: synchronous vs asynchronous, engagement online, LMS basics, accessibility in courses, video and multimedia principles, discussion facilitation, academic integrity online, blended learning design."),
    # ---- physical-sciences (new) ----
    ("physics-mechanics", "Classical mechanics", "physical-sciences", 20, "Newtonian physics: force and acceleration, momentum and conservation, energy (kinetic/potential) and work, friction, circular motion, torque and equilibrium, common misconceptions (heavier falls faster), free-body reasoning."),
    ("physics-electromagnetism", "Electricity & magnetism", "physical-sciences", 20, "E&M basics: charge and Coulomb's law, current/voltage/resistance and Ohm's law, series vs parallel circuits, power, magnetic fields and induction conceptually, capacitors, why AC vs DC, safety intuition."),
    ("physics-thermodynamics", "Thermodynamics", "physical-sciences", 20, "Heat and energy: temperature vs heat, laws of thermodynamics conceptually, entropy intuition, heat transfer (conduction/convection/radiation), phase changes, efficiency limits, why perpetual motion fails."),
    ("chemistry-general", "General chemistry", "physical-sciences", 20, "Chemistry foundations: atomic structure and the periodic table, ionic vs covalent bonds, moles and stoichiometry basics, states of matter, reactions and balancing, acids and bases/pH, exothermic vs endothermic."),
    ("chemistry-organic", "Organic chemistry basics", "physical-sciences", 20, "Organic chemistry: carbon bonding, functional groups, isomers, naming basics, common reaction types conceptually, polymers, why carbon is versatile, reading structural formulas."),
    ("astronomy-basics", "Astronomy & cosmology", "physical-sciences", 20, "The cosmos: scale of the universe, stellar life cycles, the electromagnetic spectrum in astronomy, gravity and orbits, the Big Bang evidence, exoplanets, light-years and lookback time, common misconceptions."),
    # ---- life-sciences (new) ----
    ("cell-biology", "Cell biology", "life-sciences", 20, "Cells: prokaryotes vs eukaryotes, organelles and functions, the cell membrane and transport, cellular respiration and photosynthesis conceptually, mitosis vs meiosis, DNA to protein overview, why cell size is limited."),
    ("molecular-biology", "Molecular biology", "life-sciences", 20, "Molecular basis of life: DNA structure and replication, transcription and translation, the genetic code, gene regulation basics, mutations and their effects, PCR conceptually, central dogma exceptions."),
    ("evolution-genetics", "Evolution & genetics", "life-sciences", 20, "Evolution and heredity: natural selection mechanism, Mendelian inheritance, dominant/recessive, genetic variation sources, allele frequency, common misconceptions about evolution, speciation, evidence for evolution."),
    ("ecology-environment", "Ecology", "life-sciences", 20, "Ecosystems: food webs and energy flow, trophic levels, population dynamics, carrying capacity, biodiversity and its value, nutrient cycles, keystone species, human impact on ecosystems, succession."),
    ("human-anatomy-physiology", "Anatomy & physiology", "life-sciences", 20, "The human body: major organ systems and their functions, homeostasis, the cardiovascular and respiratory link, the nervous system basics, digestion overview, the immune system conceptually, feedback loops."),
    ("microbiology", "Microbiology", "life-sciences", 20, "Microbes: bacteria vs viruses vs fungi, how infections spread, the immune response, antibiotics and resistance, vaccines conceptually, the microbiome, sterilization vs disinfection, why viruses aren't 'alive' debate."),
    # ---- engineering (new) ----
    ("mechanical-engineering-basics", "Mechanical engineering", "engineering", 20, "Mech-E foundations: stress and strain, statics and free-body diagrams, materials selection, factors of safety, simple machines and mechanical advantage, thermodynamic cycles conceptually, tolerances and fits."),
    ("electrical-engineering-basics", "Electrical engineering", "engineering", 20, "EE foundations: circuit analysis (Kirchhoff's laws), AC vs DC, impedance conceptually, semiconductors and diodes/transistors basics, digital logic gates, signal vs noise, power vs signal circuits, grounding."),
    ("civil-structural-basics", "Civil & structural engineering", "engineering", 20, "Civil-E basics: loads (dead/live/wind), tension vs compression, beams and trusses, foundations, factor of safety, materials (concrete/steel) properties, redundancy, why structures fail (famous cases)."),
    ("control-systems", "Control systems", "engineering", 20, "Control theory intuition: open vs closed loop, feedback and setpoints, PID control conceptually, stability and oscillation, sensors and actuators, latency in control, overshoot and damping, real-world examples."),
    ("cad-engineering-drawing", "CAD & engineering drawing", "engineering", 20, "Technical drawing: orthographic projection, dimensioning and tolerancing (GD&T basics), section and detail views, scale, assembly vs part drawings, CAD parametric modeling concepts, drawing standards."),
    # ---- hardware-embedded (new) ----
    ("embedded-systems", "Embedded systems", "hardware-embedded", 20, "Embedded computing: microcontrollers vs microprocessors, GPIO/ADC/PWM, interrupts vs polling, memory constraints, real-time requirements, firmware vs software, power management, debugging without a screen."),
    ("iot-fundamentals", "IoT fundamentals", "hardware-embedded", 20, "Internet of Things: sensors and actuators, edge vs cloud processing, connectivity (BLE/WiFi/cellular/LoRa) tradeoffs, power budgets, device provisioning and updates, IoT security risks, data volume challenges."),
    ("electronics-basics", "Electronics basics", "hardware-embedded", 20, "Practical electronics: resistors/capacitors/inductors roles, reading schematics, breadboarding, voltage dividers, pull-up/pull-down resistors, multimeter use, common failure modes, soldering safety conceptually."),
    ("digital-logic", "Digital logic", "hardware-embedded", 20, "Digital design: binary and hex, logic gates and truth tables, combinational vs sequential, flip-flops and registers, clocks, adders and multiplexers, Boolean simplification, why timing matters."),
    # ---- game-dev (new) ----
    ("game-design-fundamentals", "Game design fundamentals", "game-dev", 20, "Game design: core loops, mechanics vs dynamics vs aesthetics (MDA), player motivation, difficulty curves and flow, feedback and juice, balancing, onboarding, why fun is hard to design."),
    ("game-programming", "Game programming", "game-dev", 20, "Game code: the game loop, delta time and frame independence, sprites and rendering basics, collision detection, state machines for entities, input handling, object pooling, common performance traps."),
    ("game-physics-math", "Game physics & math", "game-dev", 20, "Game math: vectors for movement, dot and cross products uses, interpolation (lerp), basic collision math, rigid body intuition, coordinate systems, trigonometry for rotation, fixed vs variable timestep."),
    ("level-design", "Level design", "game-dev", 20, "Designing levels: pacing and rhythm, guiding the player without hand-holding, difficulty ramps, sightlines and landmarks, reward placement, playtesting levels, environmental storytelling, gating and progression."),
    # ---- media-production (new) ----
    ("photography", "Photography", "media-production", 20, "Photography craft: exposure triangle (aperture/shutter/ISO), depth of field, composition rules, lighting basics, white balance, focal length effects, RAW vs JPEG, common beginner mistakes."),
    ("video-production", "Video production", "media-production", 20, "Video craft: shot types and framing, the 180-degree rule, sequencing and coverage, three-point lighting, audio's outsized importance, frame rates and resolution, b-roll, continuity, pre-production value."),
    ("video-editing", "Video editing", "media-production", 20, "Editing craft: cuts and transitions purposefully, pacing and rhythm, J and L cuts, color grading basics, audio mixing and levels, the edit tells the story, avoiding over-editing, export settings."),
    ("audio-podcasting", "Audio & podcasting", "media-production", 20, "Audio production: microphone types and technique, gain staging, room treatment vs post, noise and hum, editing dialogue, loudness normalization (LUFS), music and rights, why audio quality retains listeners."),
    ("streaming-content-creation", "Content creation & streaming", "media-production", 20, "Creator craft: platform algorithms honestly, hooks and retention, thumbnails and titles, consistency vs burnout, community building, monetization models, analytics that matter, repurposing across platforms."),
    # ---- sales (new) ----
    ("sales-fundamentals", "Sales fundamentals", "sales", 30, "Selling: consultative vs transactional, discovery and qualifying (BANT/MEDDIC conceptually), features vs value, handling objections, the buying process, building rapport and trust, asking for the close, follow-up discipline."),
    ("prospecting-lead-gen", "Prospecting & lead gen", "sales", 20, "Filling the pipeline: ideal customer profile, outbound vs inbound, cold outreach that works, personalization at scale, multi-channel sequences, qualifying vs disqualifying fast, referral generation, activity vs outcome metrics."),
    ("negotiation-closing", "Negotiation & closing", "sales", 20, "Closing deals: recognizing buying signals, trial closes, handling price objections, concessions and trade-offs, creating urgency honestly, multi-stakeholder deals, avoiding discounting reflexively, win-win framing."),
    ("account-management", "Account management", "sales", 20, "Growing accounts: onboarding for retention, QBRs, upsell and cross-sell timing, relationship mapping, churn signals, advocacy and references, expansion vs acquisition economics, being a trusted advisor."),
    ("sales-crm-process", "Sales process & CRM", "sales", 20, "Sales operations: pipeline stages and hygiene, forecasting honestly, conversion rates by stage, sales cycle length, CRM discipline, activity metrics vs results, deal reviews, why 'commit vs best case' matters."),
    # ---- customer-experience (new) ----
    ("customer-support-fundamentals", "Customer support", "customer-experience", 20, "Support craft: empathy and de-escalation, first-response vs resolution time, tone in writing, troubleshooting method, knowing when to escalate, documentation and knowledge base, handling angry customers, CSAT drivers."),
    ("customer-success-management", "Customer success", "customer-experience", 20, "CS discipline: onboarding to value, health scores, proactive vs reactive, churn prediction and rescue, expansion signals, QBRs, advocacy, aligning customer outcomes with renewals, CS vs support vs account management."),
    ("support-metrics-ops", "Support metrics & operations", "customer-experience", 20, "Support ops: CSAT vs NPS vs CES, first-contact resolution, ticket deflection, SLA management, staffing to volume (Erlang intuition), quality assurance, self-service ROI, avoiding vanity metrics."),
    ("voice-of-customer", "Voice of the customer", "customer-experience", 20, "Listening at scale: survey design for feedback, closing the loop, sentiment analysis limits, categorizing feedback, prioritizing what to act on, quantifying qualitative signals, feedback vs feature requests, communicating changes."),
    # ---- real-estate (new) ----
    ("real-estate-fundamentals", "Real estate fundamentals", "real-estate", 20, "Property basics: residential vs commercial, how valuation works (comps, income, cost approaches), the transaction process, agency and representation, mortgages and financing basics, closing costs, location factors."),
    ("real-estate-investing", "Real estate investing", "real-estate", 20, "Property investment: cap rate and cash-on-cash return, NOI, leverage effects, the 1% rule and its limits, appreciation vs cash flow, financing and refinancing, property management tradeoffs, risk factors."),
    ("property-management", "Property management", "real-estate", 20, "Managing property: tenant screening, leases and terms, maintenance vs capex, vacancy and turnover costs, rent setting, legal obligations (habitability), evictions basics conceptually, operating expense ratios."),
    ("mortgage-lending", "Mortgage & lending", "real-estate", 20, "Home financing: fixed vs adjustable rates, amortization, LTV and down payments, PMI, points, DTI and underwriting, pre-approval vs pre-qualification, refinancing math, closing the loan."),
    # ---- hospitality-tourism (new) ----
    ("hospitality-management", "Hospitality management", "hospitality-tourism", 20, "Running hospitality: guest experience and service recovery, revenue management and RevPAR, front vs back of house, upselling, online reviews impact, staffing to occupancy, brand standards, the moments that matter."),
    ("restaurant-operations", "Restaurant operations", "hospitality-tourism", 20, "F&B operations: food cost percentage, menu engineering, labor cost control, table turnover, inventory and waste, health and safety (HACCP conceptually), the guest journey, prime cost management."),
    ("tourism-travel", "Tourism & travel", "hospitality-tourism", 20, "Travel industry: destination marketing, seasonality management, the OTA vs direct booking tension, sustainable tourism, customer segments, travel distribution, experience design, overtourism tradeoffs."),
    ("event-management", "Event management", "hospitality-tourism", 20, "Running events: planning timelines and critical path, budgeting and contingency, vendor coordination, venue and capacity, risk and contingency planning, run-of-show, attendee experience, measuring success."),
    # ---- manufacturing (new) ----
    ("lean-manufacturing", "Lean manufacturing", "manufacturing", 20, "Lean production: the seven wastes, value stream mapping, just-in-time, kaizen, poka-yoke, takt time, 5S, pull systems, continuous flow, why inventory hides problems."),
    ("production-planning", "Production planning", "manufacturing", 20, "Planning production: MRP logic, capacity planning, bill of materials, lead times and buffers, make-to-stock vs make-to-order, scheduling and sequencing, bottleneck (theory of constraints), demand-supply balancing."),
    ("quality-control-manufacturing", "Quality control", "manufacturing", 20, "Manufacturing quality: SPC and control charts, tolerances and specifications, inspection sampling (AQL), defect rates and PPM, root cause analysis, cost of quality, first-pass yield, supplier quality."),
    ("industrial-safety", "Industrial safety", "manufacturing", 20, "Workplace safety: hazard identification, lockout/tagout, PPE, risk assessment, the hierarchy of controls, incident reporting and near-misses, ergonomics, safety culture vs compliance-only."),
    # ---- public-policy (new) ----
    ("public-policy-analysis", "Public policy analysis", "public-policy", 20, "Policy work: problem definition, cost-benefit analysis, stakeholder analysis, unintended consequences, evidence-based policy, implementation gaps, evaluation methods, the politics-vs-analysis tension."),
    ("political-science-basics", "Political science", "public-policy", 20, "Government and politics: branches and separation of powers, electoral systems, federalism, interest groups, public opinion, comparative government forms, checks and balances, collective action problems."),
    ("urban-planning", "Urban planning", "public-policy", 20, "Cities: zoning and land use, density and transit, housing supply and affordability, walkability, induced demand, public space, gentrification tradeoffs, infrastructure and growth."),
    ("nonprofit-management", "Nonprofit management", "public-policy", 20, "Nonprofits: mission vs sustainability, funding models and grants, board governance, program vs overhead honestly, theory of change, impact measurement, volunteer management, the overhead myth."),
    ("grant-writing-fundraising", "Grant writing & fundraising", "public-policy", 20, "Raising money: the grant lifecycle, needs statements, logic models, budgets, funder alignment, donor cultivation and stewardship, major gifts vs annual giving, measuring fundraising ROI."),
    # ---- languages-linguistics (new) ----
    ("linguistics-fundamentals", "Linguistics fundamentals", "languages-linguistics", 20, "How language works: phonetics vs phonology, morphemes, syntax basics, semantics vs pragmatics, descriptive vs prescriptive grammar, language change, universals, why translation is hard."),
    ("second-language-learning", "Language learning methods", "languages-linguistics", 20, "Learning languages: comprehensible input, spaced repetition for vocabulary, the role of grammar study, speaking vs comprehension, immersion, plateaus, false cognates, realistic timelines and CEFR levels."),
    ("english-esl", "English & ESL essentials", "languages-linguistics", 20, "English as a second language: articles (a/an/the), verb tenses and aspect, phrasal verbs, prepositions, count vs mass nouns, common learner errors, register and formality, pronunciation challenges."),
    ("translation-localization", "Translation & localization", "languages-linguistics", 20, "Adapting content: translation vs localization, cultural adaptation, idioms and untranslatables, tone preservation, localization of dates/numbers/currency, translation memory tools, machine translation limits, quality assurance."),
    # ---- architecture-construction (new) ----
    ("architecture-fundamentals", "Architecture fundamentals", "architecture-construction", 20, "Building design: form and function, program and spatial planning, structural vs architectural, light and circulation, sustainability in design, building codes conceptually, the design-build process, scale and proportion."),
    ("construction-management", "Construction management", "architecture-construction", 20, "Building projects: project phases, scheduling and critical path, cost estimating, the general contractor role, RFIs and change orders, safety on site, quality inspections, managing subcontractors."),
    ("building-systems-mep", "Building systems (MEP)", "architecture-construction", 20, "Building services: HVAC principles, electrical and lighting, plumbing basics, energy efficiency and insulation, ventilation and air quality, system coordination, commissioning, why MEP drives cost."),
    ("sustainable-building", "Sustainable building", "architecture-construction", 20, "Green building: LEED concepts, passive design, embodied vs operational carbon, insulation and envelope, renewable integration, water efficiency, daylighting, lifecycle thinking in construction."),
    # ---- agriculture-food (new) ----
    ("agriculture-fundamentals", "Agriculture fundamentals", "agriculture-food", 20, "Farming basics: soil health and nutrients, crop rotation, irrigation methods, pest management (IPM), yields and inputs, sustainable vs conventional, seasonality, the economics of farming."),
    ("food-science", "Food science", "agriculture-food", 20, "Food science: macronutrients and preservation, spoilage and microbiology, fermentation, the Maillard reaction, food safety (temperature danger zone), additives and their roles, processing effects, shelf life."),
    ("food-safety-haccp", "Food safety (HACCP)", "agriculture-food", 20, "Food safety systems: hazard types (biological/chemical/physical), critical control points, temperature control, cross-contamination, cleaning vs sanitizing, allergen management, traceability, foodborne illness prevention."),
    ("sustainable-agriculture", "Sustainable agriculture", "agriculture-food", 20, "Sustainable food systems: regenerative practices, soil carbon, water use, monoculture risks, food miles and local debate, agricultural emissions, precision agriculture, feeding a growing population tradeoffs."),
    # ---- deepen finance ----
    ("financial-planning", "Financial planning (CFP)", "finance", 20, "Financial planning: goal-based planning, retirement projections, tax-advantaged accounts, asset allocation by life stage, insurance needs analysis, estate basics, the planning process, fiduciary vs suitability."),
    ("banking-fundamentals", "Banking & credit", "finance", 20, "Banking: how banks make money (net interest margin), credit scores and reports, secured vs unsecured lending, interest calculation, fractional reserve conceptually, payment systems, fraud protection, good vs bad debt."),
    ("insurance-fundamentals", "Insurance", "finance", 20, "Insurance: risk pooling and premiums, deductibles/copays/coverage limits, adverse selection and moral hazard, underwriting, term vs whole life, when to insure vs self-insure, common coverage gaps."),
    ("financial-modeling", "Financial modeling", "finance", 20, "Building models: the three-statement model links, assumptions and drivers, sensitivity and scenario analysis, DCF construction, avoiding circular references, model hygiene, garbage-in-garbage-out, presenting model outputs."),
    # ---- deepen business ----
    ("negotiation-business", "Business negotiation", "business", 20, "Deal-making: interests vs positions, BATNA leverage, value creation vs claiming, anchoring, multi-issue tradeoffs, negotiating with partners vs adversaries, cultural factors, closing and documenting."),
    ("business-model-design", "Business models", "business", 20, "How businesses make money: revenue models (subscription/marketplace/transactional/ads), the business model canvas, network effects, moats, unit economics by model, platform vs pipe, monetization timing."),
    ("go-to-market", "Go-to-market strategy", "business", 20, "Launching and growing: market segmentation and targeting, positioning, channel strategy, product-led vs sales-led growth, pricing at launch, the chasm, GTM motions, measuring launch success."),
    ("competitive-strategy", "Competitive strategy", "business", 20, "Winning markets: sources of competitive advantage, first-mover myths, switching costs, differentiation vs cost leadership, competitive response, disruption theory, defensibility, when to compete vs avoid."),
    # ---- deepen product ----
    ("product-analytics", "Product analytics", "product", 20, "Measuring products: activation/retention/engagement metrics, funnels and drop-off, cohort retention curves, event tracking design, north-star metrics, feature adoption, A/B testing for product, avoiding vanity metrics."),
    ("product-strategy", "Product strategy", "product", 20, "Product direction: vision vs strategy vs roadmap, jobs-to-be-done, build vs buy vs partner, platform vs point solution, prioritization frameworks, saying no, portfolio thinking, aligning product to business goals."),
    ("growth-product", "Growth & experimentation", "product", 20, "Product growth: the growth loop vs funnel, acquisition/activation/retention/referral/revenue, experiment velocity, north-star and input metrics, viral coefficient, onboarding optimization, retention as the foundation."),
    ("service-design", "Service design", "product", 20, "Designing services: service blueprints, front vs backstage, touchpoints and the customer journey, moments of truth, cross-channel consistency, operationalizing experience, measuring service quality."),
    # ---- deepen communication ----
    ("public-speaking", "Public speaking", "communication", 20, "Speaking to groups: managing nerves, structure and signposting, vocal variety and pacing, body language, audience connection, handling questions, storytelling in talks, rehearsal and recovery from mistakes."),
    ("facilitation-meetings", "Facilitation & meetings", "communication", 20, "Running meetings: agendas and outcomes, facilitation techniques, decision-making methods, managing dominant and quiet voices, timeboxing, async vs sync, when NOT to meet, action items and follow-through."),
    ("conflict-resolution", "Conflict resolution", "communication", 20, "Handling conflict: interests beneath positions, active listening, de-escalation, mediation basics, difficult conversations, giving hard feedback, repair after rupture, conflict styles and when each fits."),
    ("cross-cultural-communication", "Cross-cultural communication", "communication", 20, "Communicating across cultures: high vs low context, directness norms, hierarchy and face, time orientation, nonverbal differences, avoiding stereotypes, building trust across cultures, global team dynamics."),
    # ---- deepen hr-people ----
    ("learning-development", "Learning & development", "hr-people", 20, "Growing people: training needs analysis, the 70-20-10 model, measuring training ROI (Kirkpatrick), skill gap analysis, career pathing, mentoring vs coaching, upskilling vs reskilling, transfer of training."),
    ("diversity-inclusion", "Diversity, equity & inclusion", "hr-people", 20, "DEI at work: bias in hiring and promotion, inclusive practices, belonging vs diversity, measuring DEI honestly, pay equity, accessibility, allyship, moving beyond performative efforts."),
    ("employee-engagement", "Employee engagement", "hr-people", 20, "Engagement: drivers of engagement, engagement vs satisfaction, survey design and action, manager's role, recognition, burnout prevention, turnover cost, the engagement-performance link."),
    ("change-management", "Change management", "hr-people", 20, "Leading change: why change fails, Kotter and ADKAR conceptually, the change curve, stakeholder resistance, communication during change, quick wins, sustaining change, change fatigue."),
    # ---- deepen math ----
    ("statistics-math", "Statistics (mathematical)", "math", 20, "Mathematical statistics: probability distributions, expectation and variance, the law of large numbers, maximum likelihood conceptually, hypothesis testing mechanics, estimators and bias, sampling distributions."),
    ("mathematical-modeling", "Mathematical modeling", "math", 20, "Modeling with math: translating problems to equations, assumptions and simplification, dimensional analysis, growth models (linear/exponential/logistic), differential equations intuition, model validation, when models mislead."),
    ("number-theory-basics", "Number theory", "math", 20, "Numbers: primes and factorization, modular arithmetic, GCD and Euclid's algorithm, divisibility rules, congruences, applications to cryptography, why primes matter, common proof techniques."),
    ("geometry-trigonometry", "Geometry & trigonometry", "math", 20, "Shapes and angles: triangles and the Pythagorean theorem, similar triangles, circles, sine/cosine/tangent meaning, the unit circle, radians vs degrees, area and volume, coordinate geometry basics."),
    # ---- deepen psychology ----
    ("behavioral-psychology", "Behavioral psychology", "psychology", 20, "Behavior science: classical vs operant conditioning, reinforcement schedules, extinction, shaping, applied behavior analysis, habit formation, why punishment often backfires, behavior vs attitude."),
    ("cognitive-psychology", "Cognitive psychology", "psychology", 20, "The mind: attention and its limits, working vs long-term memory, encoding and retrieval, schemas, dual-process thinking, perception and illusion, problem-solving, why memory is reconstructive."),
    ("developmental-psychology", "Developmental psychology", "psychology", 20, "Human development: nature vs nurture, attachment, cognitive stages (Piaget conceptually), adolescence, lifespan development, critical periods, resilience, common developmental myths."),
    ("positive-psychology", "Positive psychology & wellbeing", "psychology", 20, "Flourishing: wellbeing models (PERMA), flow, gratitude and its evidence, hedonic adaptation, meaning vs pleasure, resilience, the limits of positivity, evidence-based vs pop-psych claims."),
    # ---- deepen accounting ----
    ("cost-accounting", "Cost accounting", "accounting", 20, "Costing: direct vs indirect costs, cost allocation and drivers, activity-based costing, standard costing and variances, job vs process costing, overhead application, cost-volume-profit, decision-relevant costs."),
    ("financial-reporting", "Financial reporting", "accounting", 20, "Reporting: the reporting cycle, revenue recognition (five-step), leases and their treatment, impairment, consolidation basics, footnotes and disclosures, non-GAAP measures scrutiny, earnings quality."),
    ("forensic-accounting", "Forensic accounting", "accounting", 20, "Fraud detection: the fraud triangle, common fraud schemes, red flags in statements, Benford's law, revenue and expense manipulation, internal control weaknesses, investigation basics, whistleblower signals."),
    # ---- deepen economics ----
    ("development-economics", "Development economics", "economics", 20, "Growth and poverty: what drives economic growth, institutions, human capital, the poverty trap debate, foreign aid effectiveness, RCTs in development, measuring wellbeing beyond GDP, inequality."),
    ("labor-economics", "Labor economics", "economics", 20, "Work and wages: labor supply and demand, minimum wage debates, human capital, signaling vs skill, unemployment types, unions, automation and jobs, wage determination, discrimination in markets."),
    ("environmental-economics", "Environmental economics", "economics", 20, "Green economics: externalities and Pigouvian taxes, cap-and-trade vs carbon tax, the tragedy of the commons, public goods, discounting the future, cost-benefit of regulation, valuing the environment."),
    # ---- deepen healthcare ----
    ("pharmacology-basics", "Pharmacology basics", "healthcare", 20, "How drugs work: pharmacokinetics (ADME), pharmacodynamics, dose-response, half-life and dosing, drug interactions, generic vs brand, side effects vs adverse events, why adherence matters."),
    ("healthcare-analytics", "Healthcare analytics", "healthcare", 20, "Health data analysis: claims vs clinical data, risk adjustment, quality measures, readmission analysis, population health metrics, the denominator problem, survivorship in health data, privacy constraints."),
    ("medical-ethics", "Medical ethics", "healthcare", 20, "Bioethics: autonomy/beneficence/non-maleficence/justice, informed consent, confidentiality, end-of-life decisions, resource allocation, research ethics, conflicts of interest, when principles collide."),
]

# id, title, blurb, [subtopic ids]
NEW_TRACKS = [
    ("software-engineer-backend", "Backend Engineer (advanced)", "System design, databases, concurrency, and the craft behind reliable services.", ["system-design-basics", "database-design", "concurrency-parallelism", "apis-http", "clean-code-testing", "debugging-troubleshooting"]),
    ("java-developer", "Java Developer", "Core Java, OOP, testing, and the JVM ecosystem interviews probe.", ["java-fundamentals", "oop-design", "data-structures", "algorithms-basics", "clean-code-testing", "system-design-basics"]),
    ("mobile-developer", "Mobile Developer", "App architecture, JavaScript/TypeScript, and building for small screens.", ["mobile-dev-basics", "javascript-fundamentals", "typescript-essentials", "apis-http", "responsive-design", "debugging-troubleshooting"]),
    ("fullstack-developer", "Full-Stack Developer", "Front to back: React, Node, databases, and everything between.", ["react-fundamentals", "node-backend", "database-design", "apis-http", "javascript-fundamentals", "web-security-basics"]),
    ("qa-engineer", "QA / Test Engineer", "Testing strategy, code quality, and catching what others miss.", ["clean-code-testing", "debugging-troubleshooting", "apis-http", "web-security-basics", "algorithms-basics", "ci-cd"]),
    ("computer-vision-engineer", "Computer Vision Engineer", "Deep learning for images, from CNNs to deployment.", ["computer-vision", "deep-learning-basics", "ml-fundamentals", "feature-engineering-data-prep", "mlops-deployment", "python-for-data"]),
    ("nlp-engineer", "NLP / LLM Engineer", "Language models, embeddings, RAG, and agent systems.", ["nlp-basics", "llm-prompting", "embeddings-vector-search", "generative-ai", "ai-agents", "mlops-deployment"]),
    ("ai-product-manager", "AI Product Manager", "Shipping AI products: LLMs, evaluation, ethics, and the metrics.", ["llm-prompting", "generative-ai", "ml-fairness-ethics", "product-management-fundamentals", "business-metrics-kpis", "ab-testing"]),
    ("prompt-engineer", "Prompt Engineer", "Getting the most from LLMs — prompting, RAG, agents, and eval.", ["llm-prompting", "generative-ai", "embeddings-vector-search", "ai-agents", "nlp-basics", "critical-thinking"]),
    ("analytics-engineer", "Analytics Engineer", "dbt, modeling, and turning raw data into trusted marts.", ["dbt-analytics-eng", "advanced-sql", "data-modeling", "data-warehousing", "data-quality-governance", "python-for-data"]),
    ("database-administrator", "Database Administrator", "Design, performance, and reliability of the data layer.", ["database-design", "advanced-sql", "nosql-databases", "data-warehousing", "monitoring-observability", "security-fundamentals"]),
    ("sre", "Site Reliability Engineer", "Observability, incident response, and systems that stay up.", ["monitoring-observability", "kubernetes-basics", "ci-cd", "incident-response", "system-design-basics", "networking-fundamentals"]),
    ("network-engineer", "Network Engineer", "Networking, security, and the plumbing of the internet.", ["networking-fundamentals", "network-security", "cloud-security", "linux-command-line", "security-fundamentals", "monitoring-observability"]),
    ("penetration-tester", "Penetration Tester", "Offensive security, done ethically and by authorization.", ["penetration-testing", "application-security", "network-security", "web-security-basics", "cryptography-basics", "security-fundamentals"]),
    ("soc-analyst", "SOC Analyst", "Detection, triage, and response in a security operations center.", ["security-operations-siem", "incident-response", "network-security", "digital-forensics", "security-fundamentals", "identity-access-mgmt"]),
    ("grc-analyst", "GRC / Compliance Analyst", "Governance, risk, and the frameworks auditors live by.", ["security-compliance", "risk-management", "data-privacy-law", "compliance-ethics", "audit-basics", "security-fundamentals"]),
    ("technical-writer", "Technical Writer", "Docs that developers and users actually rely on.", ["technical-writing", "writing-fundamentals", "editing-proofreading", "apis-http", "ux-design-principles", "critical-thinking"]),
    ("graphic-designer", "Graphic Designer", "The visual craft: type, color, layout, and brand.", ["design-principles", "typography", "color-theory", "layout-composition", "branding-identity", "design-critique"]),
    ("motion-designer", "Motion Designer", "Animation with purpose, from micro-interactions to story.", ["motion-design", "design-principles", "video-editing", "ui-visual-design", "storytelling-narrative", "design-critique"]),
    ("content-strategist", "Content Strategist", "Writing, editing, SEO, and content that drives outcomes.", ["writing-fundamentals", "copywriting", "content-marketing", "seo-basics", "editing-proofreading", "marketing-analytics-attribution"]),
    ("copywriter", "Copywriter", "Words that persuade — copy, brand voice, and story.", ["copywriting", "writing-fundamentals", "storytelling-narrative", "brand-positioning", "grammar-usage", "email-crm-marketing"]),
    ("seo-specialist", "SEO Specialist", "Search visibility from technical to content to analytics.", ["seo-basics", "content-marketing", "marketing-analytics-attribution", "frontend-performance", "web-accessibility", "writing-fundamentals"]),
    ("social-media-manager", "Social Media Manager", "Strategy, content, community, and proving it worked.", ["social-media-marketing", "content-marketing", "brand-positioning", "marketing-analytics-attribution", "copywriting", "streaming-content-creation"]),
    ("growth-marketer", "Growth Marketer", "Experiment-driven acquisition, activation, and retention.", ["digital-marketing-fundamentals", "growth-product", "ab-testing", "marketing-analytics-attribution", "paid-ads-ppc", "email-crm-marketing"]),
    ("brand-manager", "Brand Manager", "Positioning, identity, and building brands that last.", ["brand-positioning", "branding-identity", "marketing-analytics-attribution", "content-marketing", "competitive-strategy", "presentation-skills"]),
    ("sales-representative", "Sales Representative / AE", "Prospecting to closing, and everything in the pipeline.", ["sales-fundamentals", "prospecting-lead-gen", "negotiation-closing", "sales-crm-process", "account-management", "emotional-intelligence"]),
    ("sales-engineer", "Sales Engineer", "Technical selling: demos, discovery, and translating value.", ["sales-fundamentals", "apis-http", "presentation-skills", "product-management-fundamentals", "negotiation-closing", "critical-thinking"]),
    ("customer-success-manager", "Customer Success Manager", "Onboarding to expansion — driving customer outcomes.", ["customer-success-management", "voice-of-customer", "business-metrics-kpis", "account-management", "emotional-intelligence", "presentation-skills"]),
    ("support-engineer", "Support Engineer", "Troubleshooting, empathy, and support at scale.", ["customer-support-fundamentals", "support-metrics-ops", "debugging-troubleshooting", "apis-http", "technical-writing", "emotional-intelligence"]),
    ("game-developer", "Game Developer", "Game loops, physics, design, and shipping fun.", ["game-programming", "game-design-fundamentals", "game-physics-math", "level-design", "cpp-fundamentals", "linear-algebra-basics"]),
    ("embedded-engineer", "Embedded Engineer", "Firmware, hardware, and computing at the edge.", ["embedded-systems", "digital-logic", "electronics-basics", "cpp-fundamentals", "iot-fundamentals", "control-systems"]),
    ("iot-engineer", "IoT Engineer", "Connected devices from sensor to cloud, securely.", ["iot-fundamentals", "embedded-systems", "networking-fundamentals", "cloud-security", "streaming-basics", "electronics-basics"]),
    ("mechanical-engineer", "Mechanical Engineer", "Mechanics, materials, controls, and design fundamentals.", ["mechanical-engineering-basics", "cad-engineering-drawing", "control-systems", "physics-mechanics", "physics-thermodynamics", "quality-control-manufacturing"]),
    ("electrical-engineer", "Electrical Engineer", "Circuits, electronics, and signals from theory to board.", ["electrical-engineering-basics", "electronics-basics", "digital-logic", "physics-electromagnetism", "control-systems", "embedded-systems"]),
    ("civil-engineer", "Civil Engineer", "Structures, loads, and the built environment.", ["civil-structural-basics", "cad-engineering-drawing", "physics-mechanics", "construction-management", "sustainable-building", "mathematical-modeling"]),
    ("architect", "Architect", "Design, building systems, and sustainable construction.", ["architecture-fundamentals", "building-systems-mep", "sustainable-building", "construction-management", "design-principles", "cad-engineering-drawing"]),
    ("construction-manager", "Construction Manager", "Delivering buildings on time, on budget, and safe.", ["construction-management", "project-management-fundamentals", "building-systems-mep", "industrial-safety", "risk-stakeholder-mgmt", "unit-economics"]),
    ("teacher", "Teacher / Instructor", "Pedagogy, assessment, and how people actually learn.", ["pedagogy-teaching-methods", "instructional-design", "assessment-evaluation", "learning-theory", "learning-science", "edtech-online-learning"]),
    ("instructional-designer", "Instructional Designer", "Designing learning that works, online and off.", ["instructional-design", "learning-theory", "assessment-evaluation", "edtech-online-learning", "ux-design-principles", "writing-fundamentals"]),
    ("research-scientist", "Research Scientist", "Experimental design, statistics, and rigorous inference.", ["experimental-design", "statistical-inference", "causal-inference", "statistics-math", "critical-thinking", "technical-writing"]),
    ("lab-scientist", "Lab Scientist", "Molecular and cell biology with the stats to back it.", ["molecular-biology", "cell-biology", "microbiology", "statistical-inference", "medical-ethics", "clinical-trials-basics"]),
    ("clinical-research-associate", "Clinical Research Associate", "Trials from protocol to data, ethically run.", ["clinical-trials-basics", "epidemiology", "medical-ethics", "health-data-privacy", "statistical-inference", "healthcare-analytics"]),
    ("nurse-clinical", "Clinical Foundations", "Anatomy, pharmacology, and the science behind care.", ["human-anatomy-physiology", "pharmacology-basics", "microbiology", "medical-terminology", "medical-ethics", "nutrition-science"]),
    ("financial-planner", "Financial Planner (CFP)", "Holistic planning: goals, tax, insurance, and investing.", ["financial-planning", "personal-finance", "insurance-fundamentals", "portfolio-risk-return", "tax-fundamentals", "banking-fundamentals"]),
    ("investment-banker", "Investment Banking Analyst", "Valuation, modeling, and the statements behind deals.", ["equity-valuation", "financial-modeling", "financial-statements", "corporate-finance", "time-value-of-money", "financial-reporting"]),
    ("actuary", "Actuary", "Probability, risk, and the math of insurance.", ["probability-basics", "statistics-math", "insurance-fundamentals", "risk-management", "time-value-of-money", "financial-modeling"]),
    ("auditor", "Auditor", "Evidence, controls, and the integrity of the numbers.", ["audit-basics", "double-entry-bookkeeping", "financial-reporting", "forensic-accounting", "compliance-ethics", "cost-accounting"]),
    ("tax-advisor", "Tax Advisor", "Tax rules, planning, and the statements they touch.", ["tax-fundamentals", "double-entry-bookkeeping", "financial-statements", "financial-planning", "compliance-ethics", "ifrs-gaap"]),
    ("real-estate-agent", "Real Estate Agent", "Valuation, financing, and the transaction end to end.", ["real-estate-fundamentals", "mortgage-lending", "negotiation", "sales-fundamentals", "personal-finance", "contract-law-basics"]),
    ("real-estate-investor", "Real Estate Investor", "Cash flow, leverage, and building a property portfolio.", ["real-estate-investing", "mortgage-lending", "property-management", "personal-finance", "unit-economics", "risk-management"]),
    ("restaurant-manager", "Restaurant / F&B Manager", "Ops, cost control, and the guest experience.", ["restaurant-operations", "hospitality-management", "food-safety-haccp", "inventory-logistics", "unit-economics", "leadership-management"]),
    ("hotel-manager", "Hotel / Hospitality Manager", "Revenue, service, and running the property.", ["hospitality-management", "business-metrics-kpis", "customer-success-management", "operations-management", "leadership-management", "event-management"]),
    ("supply-chain-manager", "Supply Chain Manager", "Planning, inventory, and lean flow end to end.", ["supply-chain-basics", "production-planning", "inventory-logistics", "lean-manufacturing", "forecasting-basics", "operations-management"]),
    ("manufacturing-engineer", "Manufacturing Engineer", "Lean, quality, and production that scales.", ["lean-manufacturing", "production-planning", "quality-control-manufacturing", "six-sigma-quality", "industrial-safety", "control-systems"]),
    ("policy-analyst", "Policy Analyst", "Evidence, cost-benefit, and how government works.", ["public-policy-analysis", "political-science-basics", "microeconomics", "statistical-inference", "critical-thinking", "business-writing"]),
    ("urban-planner", "Urban Planner", "Land use, transit, housing, and the shape of cities.", ["urban-planning", "public-policy-analysis", "environmental-economics", "architecture-fundamentals", "sustainable-building", "data-storytelling"]),
    ("nonprofit-leader", "Nonprofit Leader", "Mission, funding, impact, and running the organization.", ["nonprofit-management", "grant-writing-fundraising", "leadership-management", "business-metrics-kpis", "change-management", "public-policy-analysis"]),
    ("executive-assistant", "Executive Assistant / Ops", "Coordination, communication, and making leaders effective.", ["project-management-fundamentals", "business-writing", "facilitation-meetings", "emotional-intelligence", "negotiation", "critical-thinking"]),
    ("recruiter", "Recruiter / Talent", "Sourcing, structured hiring, and candidate experience.", ["recruiting-talent", "people-analytics", "negotiation", "diversity-inclusion", "workplace-law-basics", "emotional-intelligence"]),
    ("data-journalist", "Data Journalist", "Finding, checking, and telling stories with data.", ["data-storytelling", "descriptive-stats", "statistical-inference", "writing-fundamentals", "critical-thinking", "dashboards-bi"]),
    ("sustainability-manager", "Sustainability Manager", "Carbon, ESG, and driving change through the org.", ["carbon-accounting", "esg-reporting", "climate-science-basics", "change-management", "environmental-economics", "data-storytelling"]),
    ("science-communicator", "Science Communicator", "Explaining science clearly and honestly to the public.", ["writing-fundamentals", "storytelling-narrative", "critical-thinking", "statistical-inference", "presentation-skills", "climate-science-basics"]),
    ("aspiring-founder", "Aspiring Founder", "Idea to traction: models, GTM, finance, and selling.", ["entrepreneurship-basics", "business-model-design", "go-to-market", "unit-economics", "sales-fundamentals", "personal-finance"]),
]


def main():
    cat = json.loads(CATALOG.read_text())
    theme_ids = {t["id"] for t in cat["themes"]}
    for t in NEW_THEMES:
        if t["id"] not in theme_ids:
            cat["themes"].append(t)
            theme_ids.add(t["id"])

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

    cat["version"] = cat.get("version", 3) + 1
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=1))
    print(f"catalog now: {len(cat['themes'])} themes, {len(cat['subtopics'])} subtopics, {len(cat['tracks'])} tracks")


if __name__ == "__main__":
    main()
