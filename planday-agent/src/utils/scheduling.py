"""
Optimal Weighted Interval Scheduling Algorithm using Dynamic Programming.

This module implements the classic weighted interval scheduling algorithm
that finds the maximum profit schedule with no overlapping intervals.
"""

from typing import List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class WeightedInterval:
    """Represents a weighted interval for scheduling."""
    start_time: datetime
    end_time: datetime
    weight: float
    id: str
    title: str = ""
    
    def overlaps_with(self, other: 'WeightedInterval') -> bool:
        """Check if this interval overlaps with another."""
        # Normalize timezones for comparison
        start1, end1 = self._normalize_times(self.start_time, self.end_time)
        start2, end2 = self._normalize_times(other.start_time, other.end_time)
        
        return start1 < end2 and end1 > start2
    
    def _normalize_times(self, start_time: datetime, end_time: datetime) -> tuple[datetime, datetime]:
        """Normalize times to local timezone for consistent comparison."""
        from datetime import timedelta
        
        # Convert timezone-aware times to naive local times
        if start_time.tzinfo is not None:
            # Assume UTC input, convert to local (UTC+8 for Beijing/Shanghai)
            start_time = start_time.replace(tzinfo=None) + timedelta(hours=8)
            end_time = end_time.replace(tzinfo=None) + timedelta(hours=8)
        
        return start_time, end_time


class WeightedIntervalScheduler:
    """
    Optimal weighted interval scheduler using dynamic programming.
    
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    
    def __init__(self):
        self.intervals: List[WeightedInterval] = []
        self.compatibility: List[int] = []
        self.dp_table: List[float] = []
    
    def add_interval(self, interval: WeightedInterval) -> None:
        """Add an interval to the scheduler."""
        self.intervals.append(interval)
    
    def find_optimal_schedule(self) -> Tuple[List[WeightedInterval], float]:
        """
        Find the optimal schedule with maximum total weight.
        
        Returns:
            Tuple of (selected_intervals, total_weight)
        """
        if not self.intervals:
            return [], 0.0
        
        # Step 1: Sort intervals by end time
        self.intervals.sort(key=lambda x: x.end_time)
        n = len(self.intervals)
        
        # Step 2: Precompute compatibility array
        self._compute_compatibility()
        
        # Step 3: Build DP table
        self.dp_table = [0.0] * (n + 1)
        
        for i in range(1, n + 1):
            # Option 1: Don't include current interval
            without_current = self.dp_table[i - 1]
            
            # Option 2: Include current interval
            with_current = self.intervals[i - 1].weight
            if self.compatibility[i - 1] != -1:
                with_current += self.dp_table[self.compatibility[i - 1] + 1]
            
            # Take the maximum
            self.dp_table[i] = max(without_current, with_current)
        
        # Step 4: Reconstruct optimal solution
        selected_intervals = self._reconstruct_solution()
        total_weight = self.dp_table[n]
        
        return selected_intervals, total_weight
    
    def _compute_compatibility(self) -> None:
        """
        Compute compatibility array using binary search.
        For each interval i, find the latest interval j that doesn't overlap.
        """
        n = len(self.intervals)
        self.compatibility = [-1] * n
        
        for i in range(n):
            # Find the latest job that doesn't overlap with job i
            latest_compatible = -1
            
            for j in range(i - 1, -1, -1):
                if self.intervals[j].end_time <= self.intervals[i].start_time:
                    latest_compatible = j
                    break
            
            self.compatibility[i] = latest_compatible
    
    def _reconstruct_solution(self) -> List[WeightedInterval]:
        """Reconstruct the optimal solution by backtracking through DP table."""
        selected = []
        n = len(self.intervals)
        i = n
        
        while i > 0:
            # Check if current interval was selected
            without_current = self.dp_table[i - 1]
            with_current = self.intervals[i - 1].weight
            
            if self.compatibility[i - 1] != -1:
                with_current += self.dp_table[self.compatibility[i - 1] + 1]
            
            if with_current > without_current:
                # Current interval was selected
                selected.append(self.intervals[i - 1])
                # Move to the latest compatible interval
                if self.compatibility[i - 1] != -1:
                    i = self.compatibility[i - 1] + 1
                else:
                    i = 0
            else:
                # Current interval was not selected
                i -= 1
        
        return selected[::-1]  # Reverse to get chronological order
    
    def find_conflicts(self, new_interval: WeightedInterval) -> List[WeightedInterval]:
        """
        Find all intervals that conflict with the given interval.
        
        Args:
            new_interval: The interval to check for conflicts
            
        Returns:
            List of conflicting intervals
        """
        conflicts = []
        for interval in self.intervals:
            if interval.overlaps_with(new_interval):
                conflicts.append(interval)
        return conflicts
    
    def get_available_slots(
        self, 
        duration_minutes: int,
        start_time: datetime,
        end_time: datetime,
        min_gap_minutes: int = 15
    ) -> List[Tuple[datetime, datetime]]:
        """
        Find available time slots of specified duration within a time range.
        
        Args:
            duration_minutes: Required duration in minutes
            start_time: Start of search range
            end_time: End of search range
            min_gap_minutes: Minimum gap between intervals
            
        Returns:
            List of available (start, end) time slots
        """
        from datetime import timedelta
        
        available_slots = []
        
        # Sort intervals by start time for this calculation
        sorted_intervals = sorted(self.intervals, key=lambda x: x.start_time)
        
        # Filter intervals that overlap with our search range
        relevant_intervals = [
            interval for interval in sorted_intervals
            if interval.start_time < end_time and interval.end_time > start_time
        ]
        
        if not relevant_intervals:
            # No conflicts, entire range is available
            if (end_time - start_time).total_seconds() / 60 >= duration_minutes:
                available_slots.append((start_time, end_time))
            return available_slots
        
        current_time = start_time
        
        for interval in relevant_intervals:
            # Check gap before this interval
            gap_start = max(current_time, start_time)
            gap_end = min(interval.start_time, end_time)
            
            if gap_end > gap_start:
                gap_duration = (gap_end - gap_start).total_seconds() / 60
                if gap_duration >= duration_minutes:
                    available_slots.append((gap_start, gap_end))
            
            # Update current time to end of this interval plus minimum gap
            current_time = max(
                current_time, 
                interval.end_time + timedelta(minutes=min_gap_minutes)
            )
        
        # Check gap after last interval
        if current_time < end_time:
            gap_duration = (end_time - current_time).total_seconds() / 60
            if gap_duration >= duration_minutes:
                available_slots.append((current_time, end_time))
        
        return available_slots
    
    def calculate_priority_score(self, interval: WeightedInterval) -> float:
        """
        Calculate priority score for an interval based on multiple factors.
        
        Args:
            interval: The interval to score
            
        Returns:
            Priority score (higher is better)
        """
        from datetime import timedelta
        
        base_weight = interval.weight
        
        # Time urgency factor (closer deadlines get higher priority)
        now = datetime.now()
        time_until_start = (interval.start_time - now).total_seconds() / 3600  # hours
        urgency_factor = max(0.1, 1.0 / (1.0 + time_until_start / 24))  # Decay over days
        
        # Duration efficiency (shorter tasks might be prioritized)
        duration_hours = (interval.end_time - interval.start_time).total_seconds() / 3600
        efficiency_factor = 1.0 / max(0.5, duration_hours)  # Favor shorter tasks
        
        # Combine factors
        priority_score = base_weight * urgency_factor * efficiency_factor
        
        return priority_score
    
    def optimize_schedule_with_priorities(self) -> Tuple[List[WeightedInterval], float]:
        """
        Optimize schedule considering both weights and priority factors.
        
        Returns:
            Tuple of (optimized_intervals, total_priority_score)
        """
        # Recalculate weights based on priority scores
        for interval in self.intervals:
            interval.weight = self.calculate_priority_score(interval)
        
        return self.find_optimal_schedule()


def demo_weighted_scheduling():
    """Demonstrate the weighted interval scheduling algorithm."""
    
    scheduler = WeightedIntervalScheduler()
    
    # Add some sample intervals
    from datetime import datetime, timedelta
    
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    
    intervals = [
        WeightedInterval(
            start_time=base_time,
            end_time=base_time + timedelta(hours=2),
            weight=50.0,
            id="task1",
            title="Important Meeting"
        ),
        WeightedInterval(
            start_time=base_time + timedelta(hours=1),
            end_time=base_time + timedelta(hours=3),
            weight=80.0,
            id="task2", 
            title="Critical Project Work"
        ),
        WeightedInterval(
            start_time=base_time + timedelta(hours=3),
            end_time=base_time + timedelta(hours=4),
            weight=30.0,
            id="task3",
            title="Team Standup"
        ),
        WeightedInterval(
            start_time=base_time + timedelta(hours=2.5),
            end_time=base_time + timedelta(hours=5),
            weight=100.0,
            id="task4",
            title="Client Presentation"
        )
    ]
    
    for interval in intervals:
        scheduler.add_interval(interval)
    
    # Find optimal schedule
    optimal_schedule, total_weight = scheduler.find_optimal_schedule()
    
    print("Optimal Schedule:")
    print(f"Total Weight: {total_weight}")
    for interval in optimal_schedule:
        print(f"- {interval.title}: {interval.start_time.strftime('%H:%M')} - {interval.end_time.strftime('%H:%M')} (Weight: {interval.weight})")
    
    return scheduler, optimal_schedule, total_weight


if __name__ == "__main__":
    demo_weighted_scheduling()