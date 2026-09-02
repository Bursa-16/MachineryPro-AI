"""Deterministic machining calculations: turning, milling, drilling, grinding.

Cutting speed/feed/depth-of-cut relations, MRR, machining time and the
rotational power/torque relationship. All formulas are deterministic,
unit-explicit and fail-closed. No empirical machining constants, no
material-specific data, no manufacturer recommendations - only mathematically
derived values from explicit engineering inputs.
"""

from backend.machining.exceptions import MachiningMathError
from backend.machining.formulas import (
    cutting_speed_from_spindle_speed,
    feed_per_rev_from_feed_rate,
    feed_per_tooth_from_feed_rate,
    feed_rate_from_rpm_feed_per_rev,
    feed_rate_from_rpm_tooth_feed,
    machining_time_from_distance_feed_rate,
    milling_material_removal_rate,
    power_from_torque_rpm,
    spindle_speed_from_cutting_speed,
    spindle_speed_from_feed_rate_feed_per_rev,
    spindle_speed_from_feed_rate_tooth_feed,
    tooth_count_from_feed_rate,
    torque_from_power_rpm,
)
from backend.machining.rules import (
    CuttingSpeedFromSpindleSpeedRule,
    FeedRateFromRpmFeedPerRevRule,
    FeedRateFromRpmToothFeedRule,
    MachiningTimeRule,
    MillingMaterialRemovalRateRule,
    PowerFromTorqueRule,
    SpindleSpeedFromCuttingSpeedRule,
    TorqueFromPowerRule,
    foundational_machining_rules,
)

__all__ = [
    # exceptions
    'MachiningMathError',
    # formulas
    'cutting_speed_from_spindle_speed',
    'feed_per_rev_from_feed_rate',
    'feed_rate_from_rpm_feed_per_rev',
    'feed_rate_from_rpm_tooth_feed',
    'feed_per_tooth_from_feed_rate',
    'machining_time_from_distance_feed_rate',
    'milling_material_removal_rate',
    'power_from_torque_rpm',
    'spindle_speed_from_cutting_speed',
    'spindle_speed_from_feed_rate_feed_per_rev',
    'spindle_speed_from_feed_rate_tooth_feed',
    'tooth_count_from_feed_rate',
    'torque_from_power_rpm',
    # rules
    'CuttingSpeedFromSpindleSpeedRule',
    'FeedRateFromRpmFeedPerRevRule',
    'FeedRateFromRpmToothFeedRule',
    'MachiningTimeRule',
    'MillingMaterialRemovalRateRule',
    'PowerFromTorqueRule',
    'SpindleSpeedFromCuttingSpeedRule',
    'TorqueFromPowerRule',
    'foundational_machining_rules',
]
