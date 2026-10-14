"""
Traffic Flow Simulation Engine
Accurately models queue backlog, Webster cycle delay, and vehicle throughput.
"""

import random
from optimizer import compute_dynamic_splits, compute_fixed_splits, YELLOW_TIME

def run_simulation(scenario_name="Peak Morning", cycles=10, arrival_rates=None):
    arms = ["North", "South", "East", "West"]
    
    # Arrival rates (vehicles per second) during peak hour
    if not arrival_rates:
        arrival_rates = {
            "North": 0.12,  # Campus core road
            "South": 0.50,  # Heavy expressway inbound
            "East":  0.08,  # Staff quarters
            "West":  0.30   # Expressway outbound
        }

    DISCHARGE_RATE = 0.5  # ~1 vehicle discharges every 2 seconds of green

    def simulate_mode(mode="DYNAMIC"):
        total_delay = 0.0
        total_vehicles_arrived = 0
        total_vehicles_serviced = 0
        queues = {arm: 0 for arm in arms}
        queue_samples = []

        for cycle in range(cycles):
            cycle_time = 120

            # 1. Determine green splits
            if mode == "FIXED":
                splits = compute_fixed_splits(arms, total_cycle=cycle_time)
            else:
                demand = {
                    arm: {
                        "count": int(queues[arm] + (arrival_rates[arm] * cycle_time)),
                        "queue": queues[arm] * 5.0
                    }
                    for arm in arms
                }
                splits = compute_dynamic_splits(demand, total_cycle=cycle_time)

            # 2. Simulate traffic arrival and discharge
            for arm in arms:
                green_sec = splits[arm]
                red_sec = cycle_time - green_sec

                # Inbound traffic
                expected_arrivals = arrival_rates[arm] * cycle_time
                actual_arrivals = max(1, int(random.gauss(expected_arrivals, expected_arrivals * 0.10)))
                queues[arm] += actual_arrivals
                total_vehicles_arrived += actual_arrivals

                # Capacity to discharge
                capacity = int(green_sec * DISCHARGE_RATE)
                cleared = min(queues[arm], capacity)
                queues[arm] -= cleared
                total_vehicles_serviced += cleared

                # True intersection delay: uniform wait during red + queue overflow wait
                uniform_delay = (red_sec ** 2) / (2 * cycle_time)
                overflow_delay = (queues[arm] / max(capacity, 1)) * 15.0
                arm_delay = actual_arrivals * (uniform_delay + overflow_delay)
                total_delay += arm_delay

                queue_samples.append(queues[arm])

        avg_delay = round(total_delay / max(total_vehicles_arrived, 1), 2)
        avg_queue = round(sum(queue_samples) / max(len(queue_samples), 1), 2)
        throughput = round((total_vehicles_serviced / (cycles * 120)) * 3600, 1)

        return {
            "mode": mode,
            "total_arrived": total_vehicles_arrived,
            "total_serviced": total_vehicles_serviced,
            "avg_delay_sec": avg_delay,
            "avg_queue_vehicles": avg_queue,
            "throughput_vph": throughput
        }

    fixed_res = simulate_mode("FIXED")
    dynamic_res = simulate_mode("DYNAMIC")

    delay_reduction = round(((fixed_res["avg_delay_sec"] - dynamic_res["avg_delay_sec"]) / fixed_res["avg_delay_sec"]) * 100, 1)
    queue_reduction = round(((fixed_res["avg_queue_vehicles"] - dynamic_res["avg_queue_vehicles"]) / fixed_res["avg_queue_vehicles"]) * 100, 1)
    throughput_gain = round(((dynamic_res["throughput_vph"] - fixed_res["throughput_vph"]) / fixed_res["throughput_vph"]) * 100, 1)

    return {
        "scenario": scenario_name,
        "fixed": fixed_res,
        "dynamic": dynamic_res,
        "improvements": {
            "delay_reduction_pct": delay_reduction,
            "queue_reduction_pct": queue_reduction,
            "throughput_gain_pct": throughput_gain
        }
    }


if __name__ == "__main__":
    res = run_simulation()
    f, d, imp = res["fixed"], res["dynamic"], res["improvements"]
    print(f"Delay: {f['avg_delay_sec']}s vs {d['avg_delay_sec']}s ({imp['delay_reduction_pct']}% reduction)")
    print(f"Queue: {f['avg_queue_vehicles']} vs {d['avg_queue_vehicles']} ({imp['queue_reduction_pct']}% reduction)")
    print(f"Throughput: {f['throughput_vph']} vs {d['throughput_vph']} (+{imp['throughput_gain_pct']}%)")
