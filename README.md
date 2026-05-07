# ZeroClaw Agent

**Zero-divergence agent framework. Track drift from baseline, measure divergence, participate in consensus.**

![Status](https://img.shields.io/badge/Status-Functional-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10+-blue)

When agents share a mission, they need to know when they're drifting apart. ZeroClaw tracks divergence scores — how far an agent's current state has drifted from its baseline — and provides a consensus voting mechanism to realign the fleet.

---

## Key Features

- **Divergence Scoring** — Compare any current state against a known-good baseline; score is normalized (0.0 = perfect alignment, 1.0 = complete drift)
- **Divergence History** — Every divergence event is logged with score, timestamp, and description for trend analysis
- **Fleet Consensus Voting** — Register agents, start a consensus round, collect votes, resolve by simple majority
- **Baseline Proposals** — Any registered agent can propose a baseline state; all agents track the same canonical baseline
- **Automatic Resolution** — `resolve_consensus()` returns the majority vote or `None` if no majority exists

---

## Divergence Scoring

Score = `number_of_differing_fields / baseline_size`

| Score | Meaning | Action |
|-------|---------|--------|
| `0.0` | Perfect alignment | No action needed |
| `0.0 – 0.3` | Minor drift | Monitor |
| `0.3 – 0.7` | Significant | Consider intervention |
| `> 0.7` | Critical | Fleet intervention required |

---

## Usage

### Register and Set Baseline

```python
from zeroclaw import ZeroClawConsensus

zc = ZeroClawConsensus()

# Register fleet agents
a1 = zc.register("Alpha")
a2 = zc.register("Beta")
a3 = zc.register("Gamma")

# Set shared baseline
baseline = {
    "position": "deck",
    "heading": 180,
    "speed": 12
}
zc.propose_baseline(a1, baseline)
zc.propose_baseline(a2, baseline)
zc.propose_baseline(a3, baseline)
```

### Measure Divergence

```python
# Each agent has slightly different current state
state_a1 = {"position": "deck", "heading": 180, "speed": 12}  # aligned
state_a2 = {"position": "deck", "heading": 185, "speed": 12}  # minor drift
state_a3 = {"position": "hold", "heading": 90, "speed": 8}    # major drift

print(zc.agents[a1].measure_divergence(state_a1))  # 0.00
print(zc.agents[a2].measure_divergence(state_a2))  # 0.33
print(zc.agents[a3].measure_divergence(state_a3))  # 1.00

# Report divergence event (logged to history)
event = zc.agents[a1].report_divergence(state_a1, "heading drifted 5°")
print(event.divergence_score, event.timestamp, event.description)
```

### Consensus Voting

```python
# Start a consensus round
round1 = zc.start_consensus("vote-001", [a1, a2, a3])

# Cast votes
zc.cast_vote("vote-001", a1, "hold-course")
zc.cast_vote("vote-001", a2, "hold-course")
zc.cast_vote("vote-001", a3, "adjust-heading")  # dissent

# Resolve
result = zc.resolve_consensus("vote-001")
print(result)                   # "hold-course"
print(round1.consensus_reached) # True
print(round1.decided_at)        # timestamp
```

### Full Demo

```bash
python src/zeroclaw.py
```

Output:
```
Alpha divergence: 0.00
Beta divergence: 0.33
Gamma divergence: 1.00

Consensus result: hold-course (reached: True)
```

---

## Architecture

```
src/
└── zeroclaw.py
    ├── DivergenceEvent (dataclass)
    │       agent_id, divergence_score, timestamp, description
    │
    ├── ConsensusRound (dataclass)
    │       participants, votes, consensus_reached, decided_at
    │
    ├── ZeroClawAgent
    │       ├── agent_id, name, baseline_state, divergence_history
    │       ├── set_baseline(state)
    │       ├── measure_divergence(current_state) -> float
    │       └── report_divergence(current_state, desc) -> DivergenceEvent
    │
    └── ZeroClawConsensus
            ├── agents: dict[str, ZeroClawAgent]
            ├── rounds: dict[str, ConsensusRound]
            ├── register(name) -> str
            ├── propose_baseline(agent_id, state) -> bool
            ├── start_consensus(round_id, participants) -> ConsensusRound
            ├── cast_vote(round_id, agent_id, vote) -> bool
            └── resolve_consensus(round_id) -> str | None
```

### The `.zeroclaw/` Sidecar Pattern

For persistent deployments, store baseline and divergence history alongside the agent:

```
agent-repo/
├── .zeroclaw/
│   ├── baseline.json       # canonical baseline state
│   ├── history.jsonl        # divergence events (append-only)
│   └── consensus/
│       └── active.json     # current consensus round state
└── src/
```

---

## Related Repos

- [fleet-agent](https://github.com/SuperInstance/fleet-agent) — Fleet orchestration, ZeroClaw agents run within fleet
- [superinstance](https://github.com/SuperInstance/superinstance) — Agent collective framework
- [zeroclaw-plato](https://github.com/SuperInstance/zeroclaw-plato) — 3-agent zeroclaw loop posting to PLATO rooms
- [fleet-health-monitor](https://github.com/SuperInstance/fleet-health-monitor) — Fleet health tracking
