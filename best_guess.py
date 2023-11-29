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
initial_snapshot = {"module_reference": {"x" : 1, "y" : 2, "orientation" : 90}}
rsh = pcbnew.Refresh

def module_snapshot(module_reference, snapshot):
    """
    If you want to save the positions and orientation of a switch, take a snapshot of it
    This will help you undo scripting console changes (the gui undo doesn't work)
    module snapshots are also required to move switches by self reference.
    Such as wanting to move one switch "K9" exactly 1 unit higher, you snapshot it, then move it to the
    approximate new position, then run: best_guess("K9", "K9", 10, 19.05, not ORIENT)
    This will set the origin reference module to the snapshot, and move the switch based on the snapshot.
    EXAMPLE: module_snapshot("K57")
    EXPLANATION: Record the X, Y, and orientation of module named "K57"
    """
    module = board.FindFootprintByReference(module_reference)
    if module:
        snapshot[module_reference] = {"x":module.GetPosition().x, "y":module.GetPosition().y, "orientation":module.GetOrientation()}
    else: print("Couldn't find module reference " + module_reference)

def module_snapshot_restore(module_reference, snapshot):
    """
    Restore module X, Y and orientation to previous snapshot.
    Scripting console changes are not C-Z undoable, so you need this to back out of out mistakes
    Use a list comprehension to snapshot all the relevant module names.
    EXAMPLE: module_snapshot_restore("K57", SNAPSHOT)
    EXPLANATION: Restore the X, Y, and orientation of module named "K57" to what was stored in SNAPSHOT
    """
    if module_reference in snapshot:
        module = board.FindFootprintByReference(module_reference)
        module.SetPosition(pcbnew.VECTOR2I(snapshot[module_reference]["x"], snapshot[module_reference]["y"]))
        module.SetOrientation(snapshot[module_reference]["orientation"])
        pcbnew.Refresh();
    else:
        print("ERROR: No snapshot for " +  module_reference + " snapshot!")
        print("FIX: take a snapshot of the module with this:")
        print('FIX: module_snapshot("' +  module_reference + '");')
        return 0

def best_guess(origin_mod_ref, target_mod_ref, angle_degrees, distance_mm, orient):
    """
    Place your target module (footprint) in the general area desired and run the function:
    best_guess("origin_footprint_reference_string",
               "target_footprint_reference_string", 
               angle deviation from 0 degrees,
               distance from center of origin footprint to calculate target footprint,
               whether or not to match orientation of the origin)
    NOTE: If using this function in a loop, comment out the refresh() from the end as it is
          expensive in time. Better to rsh() manually after the looping is complete.
    EXAMPLE: best_guess("K1", "K3", 10, UNIT, not ORIENT)
    EXPLANATION: Place K3 1 UNIT away from K1 in the appropriate cartesian direction given
                 a 10 degree angle of K1, and do NOT match rotation/orientation of K1
    """
    if origin_mod_ref is target_mod_ref: # it's a self refernced move, refer to snapshot
        if origin_mod_ref in SNAPSHOT:
            startx,starty = SNAPSHOT[origin_mod_ref]["x"], SNAPSHOT[origin_mod_ref]["y"]
            origin_orientation = SNAPSHOT[origin_mod_ref]["orientation"]
        else:
            print("ERROR: Cannot move by self reference without a snapshot!")
            print("FIX: Move the switch to the starting position, and make a snapshot with this:")
            print('FIX: module_snapshot("' +  origin_mod_ref + '", SNAPSHOT);')
            return 0
    else:
        origin_mod = board.FindFootprintByReference(origin_mod_ref)
        origin_orientation = origin_mod.GetOrientation()
        startx,starty = origin_mod.GetPosition().x,origin_mod.GetPosition().y
    target_mod = board.FindFootprintByReference(target_mod_ref)
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
    target_mod.SetPosition(pcbnew.VECTOR2I(int(newx),int(newy)))
    if orient: target_mod.SetOrientation(origin_orientation)
    pcbnew.Refresh();

def manual_move(mod_ref, x_move, y_move):
    """
    Move module a fixed distance from itself
    EXAMPLE: manual_move("K56", -(UNIT/3), UNIT)
    EXPLANATION: Move K56 from current x,y to new x,y one third of UNIT left, and UNIT down
    NOTE: If using this function in a loop, comment out the refresh() from the end as it is
          expensive in time. Better to rsh() manually after the looping is complete.
    """
    module = board.FindFootprintByReference(mod_ref)
    startx,starty = module.GetPosition().x,module.GetPosition().y
    newx = startx + (x_move * SCALE)
    newy = starty + (y_move * SCALE)
    module.SetPosition(pcbnew.VECTOR2I(int(newx),int(newy)))
    pcbnew.Refresh();

def align_column_from_top_down(column, angle_degrees):
    """
    Use best_guess to align 
    EXAMPLE: align_column_from_top_down(["K12","K24","K36","K64","K58"], 10)
    EXPLANATION: Based on the position of K12, run best_guess on K24 with 1 unit spacing
                 increasing unit spacing by 1 each entry in the list
    """
    origin = column.pop(0)
    spacing = 1
    for target in column:
        best_guess(origin, target, angle_degrees, UNIT*spacing, ORIENT)
        spacing+=1
    column = column.insert(0,origin)

def consecutive_module_mover(home_module_ref, name_prefix, num_begin, num_end, move_dir_x, move_dir_y):
    """
    Move consecutive modules matching a naming convention of modules consecutively in x,y direction
    Place key footprints in a row at fixed interval
    EXAMPLE: consecutive_module_mover("K18", "K", 19, 29, UNIT, 0)
    EXPLANATION: From K18, move modules named "K" numbered 19 through 29 1 UNIT per module right, and 0 UNITs down
                 This places switches K18 through K29 in a horizontal row 1 UNIT apart.
    """
    home_module = board.FindFootprintByReference(home_module_ref)
    for next_module_num in range(num_begin,num_end+1):
        next_module_ref = name_prefix + str(next_module_num)
        next_module = board.FindFootprintByReference(next_module_ref)
        startx,starty = home_module.GetPosition().x,home_module.GetPosition().y
        newx = startx + (move_dir_x * SCALE)
        newy = starty + (move_dir_y * SCALE)
        next_module.SetPosition(pcbnew.VECTOR2I(int(newx),int(newy)))
        home_module = next_module

def diode_displacer(origin_name_prefix, target_name_prefix, num_begin, num_end, move_dir_x, move_dir_y):
    """
    Place footprints at XY offset based on matching number module reference of alternate prefix
    Place matching diodes near their keyswitches
    EXAMPLE: diode_displacer("K", "D", 1, 91, 0, 9.525)
    EXPLANATION: For footprints matching K1 through K91, place D1 through D91 at the same X coordinate
                 as the K module, and 9.525 lower than the Y coordinate of the K module
    """
    for module_num in range(num_begin,num_end+1):
        origin_module_ref = origin_name_prefix + str(module_num)
        target_module_ref = target_name_prefix + str(module_num)
        origin_module = board.FindFootprintByReference(origin_module_ref)
        target_module = board.FindFootprintByReference(target_module_ref)
        startx,starty = origin_module.GetPosition().x,origin_module.GetPosition().y
        newx = startx + (move_dir_x * SCALE)
        newy = starty + (move_dir_y * SCALE)
        target_module.SetPosition(pcbnew.VECTOR2I(int(newx),int(newy)))

def diode_tracer(layer, switch_name_prefix, num_begin, num_end, startx, starty, endx, endy):
    """
    This isn't for diodes, it places copies of trace segments around each module of prefix
    allowing you to _stamp_ traces around each instance of modules of a certain prefix.
    Layer reference is the layer object; use pcbnew.F_Cu or pcbnew.B_Cu (NOT strings)
    Switch name prefix is what preceeds the module id number (usually "K")
    num begin/end are module numbers to start increment till end (inclusive)
    startx/y are trace start position AS DELTA OF switch origin. Press space on switch origin,
      then point to the start pad, and record the dx and dy
    end x/y are same as start, delta of switch origin where the trace segment ends
    Trace will be a straight line between these two points. Build complex traces as segments
    EXAMPLE: diode_tracer(pcbnew.F_Cu, "K", 1, 91, -3.81, -2.54, -3.81, 9.525)
    EXPLANATION: Starting from K1's footprint position (K1x,K1y) create a trace segment
                 beginning at point (K1x+-3.81,K1y+-2.54) and ending at (K1x+-3.81,K1y+9.525)
                 Continue making copies of this trace based on the footprints of K2-K91.
    """
    board = pcbnew.GetBoard()
    for module_num in range(num_begin,num_end+1):
        switch_module = board.FindFootprintByReference(switch_name_prefix + str(module_num))
        switchx,switchy = switch_module.GetPosition().x,switch_module.GetPosition().y
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(pcbnew.VECTOR2I(switchx + int(startx * SCALE),switchy + int(starty * SCALE)))
        track.SetEnd(pcbnew.VECTOR2I(switchx + int(endx * SCALE),switchy + int(endy * SCALE)))
        track.SetWidth(int(0.25 * SCALE))
        track.SetLayer(layer)
        board.Add(track)

def add_track(startx, starty, endx, endy, layer):
    """
    Add a single track programatically. Best used with a metacode generator.
    Technically, this can add any graphical line segment to an appropriate layer
    Layer reference is the layer object; use pcbnew.F_Cu or pcbnew.B_Cu (NOT strings)
    EXAMPLE: add_track(101.25, 19.05, 101.25, 38.1 pcbnew.F_Cu)
    EXPLANATION: Create a track segment on the front copper layer.
    """
    board = pcbnew.GetBoard()
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I(int(startx * SCALE),int(starty * SCALE)))
    track.SetEnd(pcbnew.VECTOR2I(int(endx * SCALE),int(endy * SCALE)))
    track.SetWidth(int(0.25 * scale))
    track.SetLayer(layer)
    board.Add(track)
