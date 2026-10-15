"""Shared numeric rules for proportional motion retargeting."""
import math
import statistics

LIMBS=(('lleg1','lleg2'),('lleg2','lfoot1'),('rleg1','rleg2'),('rleg2','rfoot1'),('larm1','larm2'),('rarm1','rarm2'))

def movement_scale(source_heads, target_heads):
    ratios=[]
    for parent,child in LIMBS:
        if not all(n in source_heads and n in target_heads for n in (parent,child)):continue
        source=math.dist(source_heads[parent],source_heads[child])
        target=math.dist(target_heads[parent],target_heads[child])
        if source>1e-6 and target>1e-6:ratios.append(target/source)
    if not ratios:raise ValueError('No matching limb segments for motion scale calibration.')
    scale=statistics.median(ratios)
    if not math.isfinite(scale) or not .01<scale<1000:raise ValueError('Invalid character motion scale.')
    return scale

def floor_correction(current_toes, bind_toes, source_toes, scale):
    # AMM posed toe heights are already in the game's ground coordinate system.
    # Preserve that clearance, including jumps, rather than pinning every pose to zero.
    desired=min(bind_toes)+min(source_toes)*scale
    return min(current_toes)-desired

def continuous_euler(values, previous):
    if previous is None:return tuple(values)
    return tuple(p+(v-p+math.pi)%(2*math.pi)-math.pi for v,p in zip(values,previous))
