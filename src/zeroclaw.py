"""Zero-divergence agent framework with tracking and consensus."""
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

@dataclass
class DivergenceEvent:
    agent_id: str
    divergence_score: float
    timestamp: float
    description: str

@dataclass
class ConsensusRound:
    participants: list[str]
    votes: dict[str, str] = field(default_factory=dict)
    consensus_reached: bool = False
    decided_at: Optional[float] = None

class ZeroClawAgent:
    """Agent that tracks divergence and participates in consensus."""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.divergence_history: list[DivergenceEvent] = []
        self.baseline_state: Optional[dict] = None
    
    def set_baseline(self, state: dict):
        self.baseline_state = state.copy()
    
    def measure_divergence(self, current_state: dict) -> float:
        """Measure how far current state has drifted from baseline."""
        if not self.baseline_state:
            return 0.0
        
        score = 0.0
        for key in self.baseline_state:
            if key in current_state:
                if self.baseline_state[key] != current_state[key]:
                    score += 1.0
        
        # Normalize by baseline size
        if self.baseline_state:
            return score / max(1, len(self.baseline_state))
        return 0.0
    
    def report_divergence(self, current_state: dict, description: str = "") -> DivergenceEvent:
        score = self.measure_divergence(current_state)
        event = DivergenceEvent(
            agent_id=self.agent_id,
            divergence_score=score,
            timestamp=time.time(),
            description=description
        )
        self.divergence_history.append(event)
        return event

class ZeroClawConsensus:
    """Consensus mechanism for agents to agree on state."""
    
    def __init__(self):
        self.agents: dict[str, ZeroClawAgent] = {}
        self.rounds: dict[str, ConsensusRound] = {}
    
    def register(self, name: str) -> str:
        agent_id = str(uuid.uuid4())[:8]
        self.agents[agent_id] = ZeroClawAgent(agent_id, name)
        return agent_id
    
    def propose_baseline(self, agent_id: str, state: dict) -> bool:
        if agent_id in self.agents:
            self.agents[agent_id].set_baseline(state)
            return True
        return False
    
    def start_consensus(self, round_id: str, participant_ids: list[str]) -> ConsensusRound:
        self.rounds[round_id] = ConsensusRound(participants=participant_ids)
        return self.rounds[round_id]
    
    def cast_vote(self, round_id: str, agent_id: str, vote: str) -> bool:
        if round_id not in self.rounds:
            return False
        self.rounds[round_id].votes[agent_id] = vote
        return True
    
    def resolve_consensus(self, round_id: str) -> Optional[str]:
        if round_id not in self.rounds:
            return None
        
        round_obj = self.rounds[round_id]
        votes = list(round_obj.votes.values())
        
        if not votes:
            return None
        
        # Simple majority
        consensus = max(set(votes), key=votes.count)
        count = votes.count(consensus)
        
        if count > len(votes) // 2:
            round_obj.consensus_reached = True
            round_obj.decided_at = time.time()
            return consensus
        
        return None

if __name__ == "__main__":
    zc = ZeroClawConsensus()
    
    # Register 3 agents
    a1 = zc.register("Alpha")
    a2 = zc.register("Beta")
    a3 = zc.register("Gamma")
    
    # Set baselines
    baseline = {"position": "deck", "heading": 180, "speed": 12}
    zc.propose_baseline(a1, baseline)
    zc.propose_baseline(a2, baseline)
    zc.propose_baseline(a3, baseline)
    
    # Measure divergence
    state_a1 = {"position": "deck", "heading": 180, "speed": 12}  # no change
    state_a2 = {"position": "deck", "heading": 185, "speed": 12}  # slight drift
    state_a3 = {"position": "hold", "heading": 90, "speed": 8}     # major drift
    
    print(f"Alpha divergence: {zc.agents[a1].measure_divergence(state_a1):.2f}")
    print(f"Beta divergence: {zc.agents[a2].measure_divergence(state_a2):.2f}")
    print(f"Gamma divergence: {zc.agents[a3].measure_divergence(state_a3):.2f}")
    
    # Consensus round
    round1 = zc.start_consensus("vote-001", [a1, a2, a3])
    zc.cast_vote("vote-001", a1, "hold-course")
    zc.cast_vote("vote-001", a2, "hold-course")
    zc.cast_vote("vote-001", a3, "adjust-heading")  # dissent
    
    result = zc.resolve_consensus("vote-001")
    print(f"\nConsensus result: {result} (reached: {round1.consensus_reached})")