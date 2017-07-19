import math

from gcode import GCode, E, S, W, N, NE, NW, SE, SW

import utils

gcode = GCode()

# hw configs
PEEK = "PEEK-PRO-12"
PTFE = "PTFE-PRO-12"
E3DV6 = "PTFE-EV6"

HW_CONFIGS = [PTFE, E3DV6, PEEK]


class SwitchTower:

    def __init__(self, start_pos_x, start_pos_y, logger, hw_config):
        """
        Filament switc tower functionality
        :param start_pos_x: start position x coordinate
        :param start_pos_y: start position y coordinate
        :param logger: Logger object
        :param config: system configuration (PEEK, PTFE, E3Dv6)
        """

        self.log = logger

        self.width = 50
        self.height = 14 # use even values

        self.hw_config = hw_config
        if self.hw_config == E3DV6:
            self.height += 2

        self.wall_width = self.width + 2.4
        self.wall_height = self.height + 1

        self.raft_width = self.width + 4
        self.raft_height = self.height + 2
        self.angle = 0
        self.start_pos_x = start_pos_x
        self.start_pos_y = start_pos_y
        self.raft_pos_x = self.start_pos_x - 2
        self.raft_pos_y = self.start_pos_y - 1.2
        self.last_tower_z = 0

        self.flipflop_purge = False
        self.flipflop_infill = False

        # post purge line config
        self.purge_line_length = self.width + 0.6
        self.purge_lines = int(abs(self.height / 2)) -1
        if self.hw_config == E3DV6:
            self.purge_lines -= 1

        # is prepurge position positive or negative
        self.prepurge_sign = 1

        self.pre_switch_lines = {}
        self.post_switch_lines = []

        self.init_pre_switch_gcode()
        self.init_post_switch_gcode()

    def generate_purge_speeds(self, min_speed):
        """
        Initialize a list for purge speeds
        :param min_speed: minimum speed for last lines
        :return: list of print speeds
        """
        speed = min_speed
        min_speed_lines = 0
        purge_speeds = []
        for i in range(self.purge_lines):
            if i >= min_speed_lines:
                speed = 2400
            purge_speeds.insert(0, speed)
        return purge_speeds

    def init_pre_switch_gcode(self):
        # TODO: read from file
        self.pre_switch_lines[True] = []
        self.pre_switch_lines[False] = []

        if self.hw_config == PEEK:
            # flip

            prepurge_feed_rate = lambda x: x * (4.5 / 50)
            prepurge_feed_length = prepurge_feed_rate(self.width)

            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y1.4 F3000", b" Y shift"))

            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F1500" % (10, -20)).encode(), b" drip trail"))
            self.pre_switch_lines[True].append((b"G1 E-15 F1500", b" 25mm/s reshaping"))
            self.pre_switch_lines[True].append((b"G4 P2000", b" 2s cooling period"))
            self.pre_switch_lines[True].append((b"G1 E-95 F1500", b" 25mm/s long retract"))

            # flop
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y0.6 F3000", b" Y shift"))

            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F1500" % (10, -20)).encode(), b" drip trail"))
            self.pre_switch_lines[False].append((b"G1 E-15 F1500", b" 25mm/s reshaping"))
            self.pre_switch_lines[False].append((b"G4 P2000", b" 2s cooling period"))
            self.pre_switch_lines[False].append((b"G1 E-95 F1500", b" 25mm/s long retract"))

        elif self.hw_config == PTFE:

            prepurge_feed_rate = lambda x: x * (4.5 / 50)
            prepurge_feed_length = prepurge_feed_rate(self.width)

            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y1.4 F3000", b" Y shift"))

            self.pre_switch_lines[True].append((b"G1 E-20 F3000", b" rapid retract"))
            self.pre_switch_lines[True].append((b"G4 P2500", b" 2.5s cooling period"))
            self.pre_switch_lines[True].append((b"G1 E-140 F3000", b" 50mm/s long retract"))

            # flop
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y0.6 F3000", b" Y shift"))

            self.pre_switch_lines[False].append((b"G1 E-20 F3000", b" rapid retract"))
            self.pre_switch_lines[False].append((b"G4 P2500", b" 2.5s cooling period"))
            self.pre_switch_lines[False].append((b"G1 E-140 F3000", b" 50mm/s long retract"))

        elif self.hw_config == E3DV6:

            prepurge_feed_rate = lambda x: x * (4.5 / 50)
            prepurge_feed_length = prepurge_feed_rate(self.width)

            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y0.8 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[True].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[True].append((b"G1 Y1 F3000", b" Y shift"))

            self.pre_switch_lines[True].append((b"G1 E-20 F3000", b" rapid retract"))
            self.pre_switch_lines[True].append((b"G4 P2500", b" 2.5s cooling period"))
            self.pre_switch_lines[True].append((b"G1 E-140 F3000", b" 50mm/s long retract"))

            # flop
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y1.4 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (-self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y0.6 F3000", b" Y shift"))
            self.pre_switch_lines[False].append((("G1 X%.3f E%.4f F6000" % (self.width, prepurge_feed_length)).encode(), b" purge trail"))
            self.pre_switch_lines[False].append((b"G1 Y1.4 F3000", b" Y shift"))

            self.pre_switch_lines[False].append((b"G1 E-20 F3000", b" rapid retract"))
            self.pre_switch_lines[False].append((b"G4 P2500", b" 2.5s cooling period"))
            self.pre_switch_lines[False].append((b"G1 E-140 F3000", b" 50mm/s long retract"))

    def init_post_switch_gcode(self):
        # TODO: read from file
        if self.hw_config == PEEK:
            primetrail_feed_rate = lambda x: x * (1.6 / 40)
            primetrail_length = primetrail_feed_rate(self.width)

            self.post_switch_lines.append((b"G1 E125 F1500", b" 25mm/s feed"))
            self.post_switch_lines.append((("G1 X%.3f E%.4f F1500" % (self.width - 10, primetrail_length)).encode(), b" prime trail"))
            self.prepurge_sign = 1
        elif self.hw_config == PTFE:
            primetrail_feed_rate = lambda x: x * (5 / 50)
            primetrail_length = primetrail_feed_rate(self.width)

            self.post_switch_lines.append((b"G1 E100 F3000", b" 50mm/s feed"))
            self.post_switch_lines.append((b"G1 E54 F1500", b" 25mm/s feed"))
            self.post_switch_lines.append((("G1 X%.3f E%.4f F900" % (self.width, primetrail_length)).encode(), b" prime trail"))
            self.prepurge_sign = 1

        elif self.hw_config == E3DV6:
            primetrail_feed_rate = lambda x: x * (5 / 50)
            primetrail_length = primetrail_feed_rate(self.width)

            self.post_switch_lines.append((b"G1 E100 F3000", b" 50mm/s feed"))
            self.post_switch_lines.append((b"G1 E54 F1500", b" 25mm/s feed"))
            self.post_switch_lines.append((("G1 X%.3f E%.4f F900" % (-self.width, primetrail_length)).encode(), b" prime trail"))
            self.prepurge_sign = -1

    def get_raft_lines(self, first_layer, extruder, retract, xy_speed, z_speed):
        """
        G-code lines for the raft
        :param first layer: first layer
        :param extruder: first extruder object
        :param retract: to retract or not
        :return: list of cmd, comment tuples
        """
        yield None, b" TOWER RAFT START"
        if extruder.z_hop:
            z_hop = 0.2 + extruder.z_hop
            yield ("G1 Z%.3f F%s" % (z_hop, z_speed)).encode(), b" z-hop"
        yield gcode.gen_head_move(self.raft_pos_x-0.4, self.raft_pos_y-0.4, xy_speed), b" move to raft zone"
        yield ("G1 Z0.2 F%d" % z_speed).encode(), b" move z close"
        yield b"G91", b" relative positioning"

        # box
        width = self.raft_width + 0.8
        height = self.raft_height + 0.8
        speed = 2000
        yield gcode.gen_direction_move(E, width, speed, extruder), b" raft wall"
        yield gcode.gen_direction_move(N, height, speed, extruder), b" raft wall"
        yield gcode.gen_direction_move(W, width, speed, extruder), b" raft wall"
        width -= 0.4
        height -= 0.4
        yield gcode.gen_direction_move(S, height, speed, extruder), b" raft wall"
        yield gcode.gen_direction_move(E, width, speed, extruder), b" raft wall"
        height -= 0.4
        yield gcode.gen_direction_move(N, height, speed, extruder), b" raft wall"
        width -= 0.4
        height -= 0.4
        yield gcode.gen_direction_move(W, width, speed, extruder), b" raft wall"
        yield gcode.gen_direction_move(S, height, speed, extruder), b" raft wall"

        yield gcode.gen_direction_move(SE, 0.6, xy_speed), None

        feed_rate = extruder.get_feed_rate(multiplier=1.3)
        speed = 1000
        for _ in range(int(self.raft_width/2)):
            yield gcode.gen_direction_move(N, self.raft_height, speed, extruder, feed_rate), b" raft1"
            yield gcode.gen_direction_move(E, 1, speed), b" raft2"
            yield gcode.gen_direction_move(S, self.raft_height, speed, extruder, feed_rate), b" raft3"
            yield gcode.gen_direction_move(E, 1, speed), b" raft4"

        if retract:
            yield extruder.get_retract_gcode()
        yield b"G90", b" absolute positioning"
        yield None, b" TOWER RAFT END"
        self.last_tower_z = 0.2

    def _get_z_hop(self, layer, z_hop, z_speed, extruder):
        """
        Get g-code for z-hop
        :param layer: current layer
        :param z-hop position
        :param z_speed: z-axis speed
        :param extruder: current extruder
        :return: G-code for z-hop or None
        """
        if extruder.z_hop:
            new_z_hop = self.last_tower_z + extruder.z_hop
            if new_z_hop != layer.z + z_hop:
                return ("G1 Z%.3f F%.1f" % (new_z_hop, z_speed)).encode(), b" z-hop"
        return None

    def _get_retraction(self, e_pos, extruder):
        """
        Get g-code for retraction. Calculate needed retraction length from current e position
        :param e_pos: extruder position
        :param extruder: extruder object
        :return: retraction g-code
        """
        retraction = extruder.retract + e_pos
        self.log.debug("Retraction to add: %s. E position: %s" %(retraction, e_pos))
        if not utils.is_float_zero(retraction, 3):
            if retraction > extruder.retract:
                retraction = extruder.retract
            return ("G1 E%.4f F%.1f" % (-retraction, extruder.retract_speed)).encode(), b" tower retract"

    def _get_wall_position_gcode(self, flipflop, xy_speed):
        """
        Retun g-code line for positioning head for wall print
        :param flipflop: flip or flop
        :param xy_speed: xy travel speed
        :return: g-code line
        """
        x = self.start_pos_x - 1.2
        y = self.start_pos_y - 0.5
        if not flipflop:
            y += self.wall_height
        return gcode.gen_head_move(x, y, xy_speed), b" move to purge zone"

    def _get_wall_gcode(self, flipflop, extruder, wall_speed, feed_rate):
        """
        Return g-code for printing the purge tower walls
        :param flipflop: flip or flop
        :param extruder: extruder object
        :return: list of g-code lines
        """
        last_y = self.wall_height - 0.3
        if flipflop:
            yield gcode.gen_direction_move(E, self.wall_width, wall_speed, extruder, feed_rate=feed_rate), b" wall"
            yield gcode.gen_direction_move(N, self.wall_height, wall_speed, extruder, feed_rate=feed_rate), b" wall"
            yield gcode.gen_direction_move(W, self.wall_width, wall_speed, extruder, feed_rate=feed_rate), b" wall"
            yield gcode.gen_direction_move(S, last_y, wall_speed, extruder, feed_rate=feed_rate, last_line=True), b" wall"
        else:
            yield gcode.gen_direction_move(E, self.wall_width, wall_speed, extruder, feed_rate=feed_rate), b" wall"
            yield gcode.gen_direction_move(S, self.wall_height, wall_speed, extruder, feed_rate=feed_rate), b" wall"
            yield gcode.gen_direction_move(W, self.wall_width, wall_speed, extruder, feed_rate=feed_rate), b" wall"
            yield gcode.gen_direction_move(N, last_y, wall_speed, extruder, feed_rate=feed_rate, last_line=True), b" wall"

    def get_tower_lines(self, layer, e_pos, old_e, new_e, z_hop, z_speed, xy_speed):
        """
        G-code for switch tower
        :param layer: current layer
        :param e_pos: extruder position
        :param old_e: old extruder
        :param new_e: new extruder
        :param z_hop: z_hop position
        :param z_speed: z axis speed
        :return: list of cmd, comment tuples
        """
        self.log.debug("Adding purge tower")
        yield None, b" TOWER START"

        # minimum speed
        min_speed, feed_rate = layer.get_outer_perimeter_rates()

        # handle retraction
        retraction = self._get_retraction(e_pos, old_e)
        if retraction:
            yield retraction

        # handle z-hop
        hop = self._get_z_hop(layer, z_hop, z_speed, old_e)
        if hop:
            yield hop

        self.last_tower_z = self.last_tower_z + layer.height
        if self.flipflop_purge:
            yield gcode.gen_head_move(self.start_pos_x-0.6, self.start_pos_y+0.2, xy_speed), b" move to purge zone"
        else:
            yield gcode.gen_head_move(self.start_pos_x+0.6, self.start_pos_y, xy_speed), b" move to purge zone"

        yield ("G1 Z%.3f F%.1f" % (self.last_tower_z, z_speed)).encode(), b" move z close"
        yield b"G91", b" relative positioning"
        yield old_e.get_prime_gcode(change=-0.1)

        # pre-switch purge
        for line in self.pre_switch_lines[self.flipflop_purge]:
            yield line

        yield ("T%s" % new_e.tool).encode(), b" change tool"

        # feed new filament
        for line in self.post_switch_lines:
            yield line

        # post-switch purge
        purge_feed_rate = new_e.get_feed_rate(multiplier=1.2)
        # switch direction depending of prepurge orientation
        purge_length = self.purge_line_length * self.prepurge_sign

        if self.prepurge_sign == 1:
            dir_1 = W
            dir_2 = E
        else:
            dir_1 = E
            dir_2 = W

        for speed in self.generate_purge_speeds(min_speed):
            if self.flipflop_purge:
                yield gcode.gen_direction_move(N, 0.6, 3000), b" Y shift"
                yield gcode.gen_direction_move(dir_1, purge_length, speed, new_e, feed_rate=purge_feed_rate), b" purge trail"
                yield gcode.gen_direction_move(N, 0.9, 3000), b" Y shift"
                yield gcode.gen_direction_move(dir_2, purge_length, speed, new_e, feed_rate=purge_feed_rate), b" purge trail"
            else:
                yield gcode.gen_direction_move(N, 0.9, 3000), b" Y shift"
                yield gcode.gen_direction_move(dir_1, purge_length, speed, new_e, feed_rate=purge_feed_rate), b" purge trail"
                yield gcode.gen_direction_move(N, 0.6, 3000), b" Y shift"
                yield gcode.gen_direction_move(dir_2, purge_length, speed, new_e, feed_rate=purge_feed_rate), b" purge trail"

        if self.flipflop_purge:
            yield gcode.gen_direction_move(N, 0.6, 3000), b" Y shift"
        else:
            yield gcode.gen_direction_move(N, 0.9, 3000), b" Y shift"
        yield gcode.gen_direction_move(dir_1, purge_length, 2400, new_e, feed_rate=feed_rate), b" purge trail"
        direction = dir_1

        if self.hw_config == E3DV6:
            # one more purge line for E3Dv6
            if self.flipflop_purge:
                yield gcode.gen_direction_move(N, 0.9, 3000), b" Y shift"
            else:
                yield gcode.gen_direction_move(N, 0.6, 3000), b" Y shift"
            yield gcode.gen_direction_move(dir_2, purge_length, min_speed, new_e, feed_rate=feed_rate), b" purge trail"
            direction = dir_2

        # move to purge zone upper left corner
        yield b"G90", b" absolute positioning"
        yield self._get_wall_position_gcode(False, xy_speed)
        yield b"G91", b" relative positioning"

        # wall gcode
        for line in self._get_wall_gcode(False, new_e, min_speed, feed_rate):
            yield line

        yield new_e.get_retract_gcode()
        if new_e.wipe:
            yield gcode.gen_direction_move(direction + 180, new_e.wipe, 3000), b" wipe"

        yield b"G90", b" absolute positioning"
        yield b"G92 E0", b" reset extruder position"
        hop = self._get_z_hop(layer, z_hop, z_speed, old_e)
        if hop:
            yield hop
        yield None, b" TOWER END"

        # flip the flop
        self.flipflop_purge = not self.flipflop_purge

    def get_infill_lines(self, layer, e_pos, extruder, z_hop, z_speed, xy_speed):
        """
        G-code for switch tower infill
        :param layer: current layer
        :param e_pos: extruder position
        :param extruder: active extruder
        :param z_hop: z_hop position
        :param z_speed: z axis speed
        :return: list of cmd, comment tuples
        """
        self.log.debug("Adding purge tower infill")
        yield None, b" TOWER INFILL START"

        # minimum speed
        min_speed, feed_rate = layer.get_outer_perimeter_rates()

        # handle retraction
        retraction = self._get_retraction(e_pos, extruder)
        if retraction:
            yield retraction

        # handle z-hop
        hop = self._get_z_hop(layer, z_hop, z_speed, extruder)
        if hop:
            yield hop
        self.last_tower_z = self.last_tower_z + layer.height

        yield self._get_wall_position_gcode(self.flipflop_infill, xy_speed)
        yield ("G1 Z%.3f F%.1f" % (self.last_tower_z, z_speed)).encode(), b" move z close"
        yield b"G91", b" relative positioning"
        yield extruder.get_prime_gcode()

        # infill
        infill_x = self.wall_width/6
        infill_y = self.wall_height-0.3
        infill_angle = math.degrees(math.atan(infill_y/infill_x))
        infill_path_length = gcode.calculate_path_length((0,0), (infill_x, infill_y))

        # wall gcode
        for line in self._get_wall_gcode(self.flipflop_infill, extruder, 2400, feed_rate):
            yield line

        flip = self.flipflop_infill

        step = (2400-min_speed)/4
        speeds = [2400 - i * step for i in range(4)]
        speeds.extend([min_speed, min_speed])

        direction = infill_angle
        round = len(speeds)
        for speed in speeds:
            round -= 1
            if flip:
                direction = infill_angle
            else:
                direction = 360-infill_angle
            yield gcode.gen_direction_move(direction, infill_path_length, speed, extruder, feed_rate=feed_rate,
                                           last_line=round == 0), b" infill"
            flip = not flip

        yield extruder.get_retract_gcode()
        if extruder.wipe:
            yield gcode.gen_direction_move(direction + 180, extruder.wipe, 2000), b" wipe"

        yield b"G90", b" absolute positioning"
        hop = self._get_z_hop(layer, z_hop, z_speed, extruder)
        if hop:
            yield hop
        yield b"G92 E0", b" reset extruder position"
        yield None, b" TOWER INFILL END"

        # flip the flop
        self.flipflop_infill = not self.flipflop_infill

if __name__ == "__main__":
    from logger import Logger
    log = Logger(".")
    st = SwitchTower(0, 1, log, PEEK)
    print(st.generate_purge_speeds(600))