import pcbnew
import math

board = pcbnew.GetBoard()
SCALE = 1000000.0
UNIT = 19.05
HALFUNIT = 19.05/2
ORIENT = True

def best_guess(origin_mod_ref, target_mod_ref, angle_degrees, distance_mm, orient):
    """
    Place your target module (footprint) in the general area and run the function:
    best_guess("origin_footprint_reference_string",
               "target_footprint_reference_string", 
               angle deviation from 0 degrees,
               distance from center of origin footprint to calculate target footprint,
               whether or not to match orientation of the origin)
    EXAMPLE: best_guess("K1", "K3", 10, 19.05, not ORIENT)
    EXPLANATION: Place K30 1 unit away from K1 in appropriate direction and do not match rotation/orientation.
    """
    SCALE = 1000000.0
    origin_mod = board.FindModuleByReference(origin_mod_ref)
    origin_orientation = origin_mod.GetOrientation()
    startx,starty = origin_mod.GetPosition().x,origin_mod.GetPosition().y
    target_mod = board.FindModuleByReference(target_mod_ref)
    opposite = (math.sin(math.radians(angle_degrees))*distance_mm)*SCALE;
    adjacent = (math.cos(math.radians(angle_degrees))*distance_mm)*SCALE;
    if abs(startx - target_mod.GetPosition().x) > abs(starty - target_mod.GetPosition().y):
        x_companion = adjacent
        y_companion = opposite
    else:
        x_companion = opposite
        y_companion = adjacent
    if target_mod.GetPosition().x < startx: x_companion *= -1
    if target_mod.GetPosition().y < starty: y_companion *= -1
    newx = startx + x_companion
    newy = starty + y_companion
    target_mod.SetPosition(pcbnew.wxPoint(newx,newy))
    if orient: target_mod.SetOrientation(origin_orientation)
    pcbnew.Refresh();
