import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple

class Judgement(Enum):
    PERFECT = auto() # 100%
    GREAT = auto()   # 50% ~ 99%
    GOOD = auto()    # 1% ~ 49%
    BAD = auto()     # 0% (Combo Break)

class NoteType(Enum):
    TAP = auto()
    HOLD = auto()

@dataclass
class TimingConfig:
    # DJMAX Standard: ±41.6ms
    # 이 시간 안(±W)에 들어오면 Perfect
    window_perfect: float = 41.6 
    
    # 점수 삭감 기준
    excess_max: float = 83.2 
    
    # 점수 커트라인 (Great 기준)
    cut_great: float = 50.0  

@dataclass
class ComboConfig:
    # 콤보 보너스 공식: BaseScore * (a * (Combo ^ p))
    growth_a: float = 0.01
    growth_p: float = 1.2
    bonus_cap_multiplier: float = 2.0   

@dataclass
class FeverConfig:
    fill_perfect: int = 4
    fill_great: int = 2
    fill_good: int = 1
    fill_bad: int = 0
    
    # 게이지가 100이 될 경우 20개의 notes 동안 점수 2배 
    gauge_max: int = 100
    fever_duration_notes: int = 20
    score_multiplier: float = 2.0

@dataclass
class SpatialConfig:
    # 노트 반경 (픽셀 단위)
    target_radius: float = 100.0

@dataclass
class NoteEvent:
    note_type: NoteType
    target_start: float  # 노트 시작 시간 (0 기준점)
    target_end: float    # 노트 끝 시간
    target_x: float
    target_y: float

    # 사용자 입력
    actual_entry: float  # 실제 들어온 시간
    actual_exit: float   # 실제 나간 시간
    min_dist: float      # 중심과의 거리

@dataclass
class PlayState:
    total_score: float = 0.0
    max_possible_score: float = 0.0
    current_combo: int = 0
    max_combo: int = 0
    fever_gauge: int = 0
    fever_active_notes: int = 0

    def is_fever_active(self) -> bool:
        return self.fever_active_notes > 0

def calc_excess(diff_ms: float, window: float) -> float:
    """
    윈도우(41.6)를 벗어난 초과분을 계산
    """
    if diff_ms < -window:
        return abs(diff_ms) - window 
    elif diff_ms > window:
        return diff_ms - window      
    return 0.0

def get_excess_ratio(excess_ms: float, max_excess: float) -> float:
    return min(excess_ms / max_excess, 1.0)

def calculate_base_score(
    note: NoteEvent, 
    t_cfg: TimingConfig,
    s_cfg: SpatialConfig
) -> Tuple[float, Judgement]:
    
    # 위치 판정
    if note.min_dist > s_cfg.target_radius:
        return 0.0, Judgement.BAD

    # 시간 판정
    d_in = note.actual_entry - note.target_start
    d_out = note.actual_exit - note.target_end
    
    W = t_cfg.window_perfect # 41.6ms

    # 상태 확인
    is_in_early = d_in < -W
    is_in_late  = d_in > W
    is_in_ok    = not (is_in_early or is_in_late)

    is_out_early = d_out < -W
    is_out_late  = d_out > W
    is_out_ok    = not (is_out_early or is_out_late)

    if is_in_ok and is_out_ok:
        return 100.0, Judgement.PERFECT
    
    # Late In Early Out -> Perfect
    if is_in_late and is_out_early:
        return 100.0, Judgement.PERFECT

    excess_in = calc_excess(d_in, W)
    excess_out = calc_excess(d_out, W)
    
    ratio_in = get_excess_ratio(excess_in, t_cfg.excess_max)
    ratio_out = get_excess_ratio(excess_out, t_cfg.excess_max)

    total_penalty_ratio = 0.0

    # Early In Late Out
    # -> 양쪽 초과분 합산
    if is_in_early and is_out_late:
        total_penalty_ratio = ratio_in + ratio_out

    # Early In
    # -> 초과분 계산
    elif is_in_early:
        total_penalty_ratio = ratio_in

    # Late Out
    # -> 초과분 계산
    elif is_out_late:
        total_penalty_ratio = ratio_out

    # 그 외
    # 둘 중 큰 페널티 적용
    else:
        total_penalty_ratio = max(ratio_in, ratio_out)
    
    # 감점 적용
    if total_penalty_ratio >= 1.0:
        return 0.0, Judgement.BAD

    score = 100.0 * (1.0 - total_penalty_ratio)

    # 등급 판정
    # 0 이하 -> BAD
    if score <= 0.0:
        return 0.0, Judgement.BAD
    # 50 이상 -> GREAT
    elif score >= t_cfg.cut_great:
        return score, Judgement.GREAT
    # 나머지 (0 < score < 50) -> GOOD
    else:
        return score, Judgement.GOOD


def process_note_result(
    note: NoteEvent,
    state: PlayState,
    t_cfg: TimingConfig = TimingConfig(),
    s_cfg: SpatialConfig = SpatialConfig(),
    c_cfg: ComboConfig = ComboConfig(),
    f_cfg: FeverConfig = FeverConfig()
) -> dict:
    
    base_score, judgement = calculate_base_score(note, t_cfg, s_cfg)
    
    if judgement == Judgement.BAD:
        state.current_combo = 0
        final_score = 0.0
    else:
        state.current_combo += 1
        state.max_combo = max(state.max_combo, state.current_combo)
        
        bonus_ratio = c_cfg.growth_a * (state.current_combo ** c_cfg.growth_p)
        bonus_score = base_score * bonus_ratio
        max_bonus = base_score * c_cfg.bonus_cap_multiplier
        bonus_score = min(bonus_score, max_bonus)
        
        current_note_total = base_score + bonus_score
        
        if state.is_fever_active():
            state.fever_active_notes -= 1
            current_note_total *= f_cfg.score_multiplier
        
        final_score = current_note_total

    # 피버 게이지 충전
    if not state.is_fever_active():
        fill_amt = {
            Judgement.PERFECT: f_cfg.fill_perfect,
            Judgement.GREAT: f_cfg.fill_great,
            Judgement.GOOD: f_cfg.fill_good,
            Judgement.BAD: f_cfg.fill_bad
        }.get(judgement, 0)
        
        state.fever_gauge += fill_amt
        if state.fever_gauge >= f_cfg.gauge_max:
            state.fever_gauge = 0
            state.fever_active_notes = f_cfg.fever_duration_notes

    state.total_score += final_score

    # Max Score Simulation
    simulated_max_combo = state.max_combo + 1 if judgement == Judgement.BAD else state.current_combo
    max_base = 100.0
    max_bonus_ratio = c_cfg.growth_a * (simulated_max_combo ** c_cfg.growth_p)
    max_bonus_val = min(max_base * max_bonus_ratio, max_base * c_cfg.bonus_cap_multiplier)
    
    possible_score = max_base + max_bonus_val
    
    state.max_possible_score += possible_score
    
    rank_ratio = (state.total_score / state.max_possible_score) if state.max_possible_score > 0 else 0.0
    rank = "F"
    if rank_ratio >= 0.95: rank = "S"
    elif rank_ratio >= 0.90: rank = "A"
    elif rank_ratio >= 0.80: rank = "B"
    elif rank_ratio >= 0.70: rank = "C"

    return {
        "judgement": judgement.name,
        "base_score": round(base_score, 1),
        "final_score": round(final_score, 1),
        "combo": state.current_combo,
        "fever_active": state.is_fever_active(),
        
        "fever_gauge": state.fever_gauge,
        "fever_max": f_cfg.gauge_max,
        "fever_active_notes": state.fever_active_notes,
        "fever_duration": f_cfg.fever_duration_notes,
        
        "total_score": round(state.total_score, 1),
        "rank": rank,
        "debug_in": f"{note.actual_entry - note.target_start:.1f}",
        "debug_out": f"{note.actual_exit - note.target_end:.1f}"
    }