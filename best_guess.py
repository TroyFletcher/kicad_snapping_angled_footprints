import pcbnew
import math

"""
Snapshot feature for switch self reference
"""

board = pcbnew.GetBoard()
SCALE = 1000000.0
UNIT = 19.05
HALFUNIT = 19.05/2
ORIENT = True
SNAPSHOT = {"module_reference": {"x" : 1, "y" : 2, "orientation" : 90}}

def module_snapshot(module_reference):
    """
    If you want to save the positions and orientation of a switch, take a snapshot of it
    This will help you undo scripting console changes (the gui undo doesn't work)
    module snapshots are also required to move switches by self reference.
    Such as wanting to move one switch "K9" exactly 1 unit higher, you snapshot it, then move it to the
    approximate new position, then run: best_guess("K9", "K9", 10, 19.05, not ORIENT)
    This will set the origin reference module to the snapshot, and move the switch based on the snapshot.
    """
    module = board.FindModuleByReference(module_reference)
    SNAPSHOT[module_reference] = {"x":module.GetPosition().x, "y":module.GetPosition().y, "orientation":module.GetOrientation()}

def snapshot_restore(module_reference):
    """
    If you want to save the positions and orientation of a switch, take a snapshot of it
    This will help you undo moves/changes
    """
    if module_reference in SNAPSHOT:
        module = board.FindModuleByReference(module_reference)
        module.SetPosition(pcbnew.wxPoint(SNAPSHOT[module_reference]["x"], SNAPSHOT[module_reference]["y"]))
        module.SetOrientation(SNAPSHOT[module_reference]["orientation"])
        pcbnew.Refresh();
    else:
        print("ERROR: No snapshot for " +  module_reference + " snapshot!")
        print("FIX: take a snapshot of the module with this:")
        print('FIX: module_snapshot("' +  module_reference + '");')
        return 0

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
    if origin_mod_ref is target_mod_ref: # it's a self refernced move, refer to snapshot
        if origin_mod_ref in SNAPSHOT:
            startx,starty = SNAPSHOT[origin_mod_ref]["x"], SNAPSHOT[origin_mod_ref]["y"]
            origin_orientation = SNAPSHOT[origin_mod_ref]["orientation"]
        else:
            print("ERROR: Cannot move by self reference without a snapshot!")
            print("FIX: Move the switch to the starting position, and make a snapshot with this:")
            print('FIX: module_snapshot("' +  origin_mod_ref + '");')
            return 0
    else:
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
