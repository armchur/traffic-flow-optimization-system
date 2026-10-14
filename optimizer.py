"""
Traffic Flow Optimization Engine
Implements dynamic green-time allocation based on real-time vehicle density
and queue length constraints.
"""

MIN_GREEN = 10   # Minimum green time in seconds (safety baseline)
MAX_GREEN = 60   # Maximum green time in seconds (prevents starvation)
YELLOW_TIME = 3  # Yellow clearance interval per phase

def calculate_density(vehicle_count, queue_length_m, alpha=0.6, beta=0.4):
    """
    Computes weighted traffic demand score.
    alpha: weight for moving vehicle volume
    beta: weight for waiting queue backlog
    """
    return (alpha * vehicle_count) + (beta * (queue_length_m / 5.0))

def compute_dynamic_splits(demand_dict, total_cycle=120):
    """
    demand_dict: {'North': {'count': 45, 'queue': 30}, 'South': {...}, ...}
    Allocates available green time across 4 phases proportionally to demand.
    """
    # 4 phases each have yellow clearance time
    total_yellow = YELLOW_TIME * len(demand_dict)
    available_green = total_cycle - total_yellow

    densities = {}
    for arm, data in demand_dict.items():
        densities[arm] = calculate_density(data.get("count", 0), data.get("queue", 0))

    total_density = sum(densities.values())

    splits = {}
    if total_density == 0:
        # Equal split if junction is empty
        equal_green = available_green // len(demand_dict)
        for arm in demand_dict:
            splits[arm] = equal_green
        return splits

    # First pass: proportional allocation
    raw_allocations = {}
    for arm, d in densities.items():
        proportion = d / total_density
        raw_allocations[arm] = proportion * available_green

    # Second pass: enforce MIN_GREEN and MAX_GREEN bounds
    bounded = {}
    remaining_green = available_green
    unconstrained_arms = []

    for arm, raw in raw_allocations.items():
        if raw < MIN_GREEN:
            bounded[arm] = MIN_GREEN
            remaining_green -= MIN_GREEN
        elif raw > MAX_GREEN:
            bounded[arm] = MAX_GREEN
            remaining_green -= MAX_GREEN
        else:
            unconstrained_arms.append(arm)

    # Distribute remaining green to unconstrained arms
    if unconstrained_arms:
        sub_density_sum = sum(densities[a] for a in unconstrained_arms)
        for arm in unconstrained_arms:
            if sub_density_sum > 0:
                share = (densities[arm] / sub_density_sum) * remaining_green
            else:
                share = remaining_green / len(unconstrained_arms)
            bounded[arm] = int(round(share))
    else:
        # If all were clamped, adjust to fit available_green
        scale = available_green / sum(bounded.values())
        for arm in bounded:
            bounded[arm] = int(round(bounded[arm] * scale))

    # Adjust rounding discrepancy to match total available green
    diff = available_green - sum(bounded.values())
    if diff != 0:
        target = max(bounded, key=lambda k: densities[k])
        bounded[target] += diff

    return bounded

def compute_fixed_splits(arms=["North", "South", "East", "West"], total_cycle=120):
    """Conventional fixed-time baseline: equal green time on all arms."""
    total_yellow = YELLOW_TIME * len(arms)
    green_per_arm = (total_cycle - total_yellow) // len(arms)
    return {arm: green_per_arm for arm in arms}


if __name__ == "__main__":
    # Test run with sample peak-hour traffic at MAU Yola junction
    test_traffic = {
        "North": {"count": 12, "queue": 15},   # Sangere campus road
        "South": {"count": 78, "queue": 85},   # Yola-Mubi Expressway Inbound (Heavy)
        "East":  {"count": 8,  "queue": 10},   # Staff Quarters (Light)
        "West":  {"count": 52, "queue": 60}    # Yola-Mubi Expressway Outbound (Moderate)
    }

    dynamic = compute_dynamic_splits(test_traffic, total_cycle=120)
    fixed = compute_fixed_splits(list(test_traffic.keys()), total_cycle=120)

    print("--- Fixed-Time Timing (Baseline) ---")
    for arm, sec in fixed.items():
        print(f"  {arm}: {sec}s green")

    print("\n--- Dynamic Timing (Optimized) ---")
    for arm, sec in dynamic.items():
        print(f"  {arm}: {sec}s green")
