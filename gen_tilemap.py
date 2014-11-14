#!/usr/local/bin/python
import itertools, random, time, sys
from collections import defaultdict
from color import ColorGenerator
from filters import *
from gui import *
from tilemap import *
from util import *

# Generation parameters
TILE_MAP_WIDTH = 192
TILE_MAP_HEIGHT = 64

ROOM_SPLIT_X_CHANCE = 0.5
ROOM_MINIMUM_HEIGHT = 6
ROOM_MAXIMUM_HEIGHT = 16
ROOM_MINIMUM_WIDTH = 8
ROOM_MAXIMUM_WIDTH = 20

FILLED_CHANCE = 0.25
FILLED_MAXIMUM_WIDTH = ROOM_MINIMUM_WIDTH + 2
FILLED_MAXIMUM_HEIGHT = ROOM_MINIMUM_HEIGHT

FLOOR_MINIMUM = 1
FLOOR_MAXIMUM = 5
CEILING_MINIMUM = 1
CEILING_MAXIMUM = 2
FLOOR_TO_CEILING_MINIMUM = 4

WALL_CHANCE = 0.15
WALL_MINIMUM = 1
WALL_MAXIMUM = 2
WALL_MINIMUM_DOORWAY = 3

LADDER_DENSITY = 0.1
LADDER_MINIMUM_HEIGHT = 2
LADDER_MAXIMUM_HEIGHT = 15
LADDER_HORIZONTAL_SPACE = 20
LADDER_VERTICAL_SPACE = 0

WALK_DROP_HEIGHT = 8

STAIR_CHANCE = 1
STAIR_MAXIMUM_HEIGHT = 4

# Tile types
TILE_EMPTY = 0
TILE_FLOOR = 1
TILE_CEILING = 2
TILE_WALL = 3
TILE_LADDER = 4
TILE_STAIR = 5
SOLID_TILES = set([TILE_FLOOR, TILE_CEILING, TILE_WALL, TILE_STAIR])

# seed = int(time.time())
seed = 1415535932 # Contains an area can enter but not leave
# seed = 1415878236 # Neat layout
# seed = 1415878343 # Mostly unreachable!
# seed = 1415878501 # Another neat layout
print "random seed:", seed
random.seed(seed)

def log(s):
    sys.stderr.write(s)
    sys.stderr.write('\n')
    sys.stderr.flush()

def main():
    tile_size = 8
    tile_map = TileMap(width=TILE_MAP_WIDTH, height=TILE_MAP_HEIGHT)
    log("Rooms...")
    rooms = generate_rooms(tile_map)
    log("Filled rooms...")
    for room in rooms:
        generate_filled_room(room)
    log("Floors and ceilings...")
    for room in rooms:
        generate_floor_and_ceiling(room)
    log("Random walls...")
    for room in rooms:
        generate_random_walls(room)
    log("Required walls...")
    for room in rooms:
        generate_required_walls(room, left_hand=True)
        generate_required_walls(room, left_hand=False)
    log("Stairs...")
    generate_floor_stairs(tile_map)
    log("Random ladders...")
    generate_random_ladders(tile_map)
    log("Walk graph...")
    walk_graph = calculate_walk_graph(tile_map)

    # room_index = generate_room_index(rooms)
    # calculate_walkable(rooms)

    tile_colors = {
        TILE_EMPTY: '#000000',
        TILE_FLOOR: '#333366',
        TILE_CEILING: '#663333',
        TILE_WALL: '#663366',
        TILE_LADDER: '#ff6666',
        TILE_STAIR: '#6666ff',
        None: '',
        }

    gui = TileMapGUI(tile_map, tile_size, tile_colors, rooms=rooms, walk_graph=walk_graph)
    gui.run()


def generate_rooms(tile_map):
    # Recursively partition the tile map
    final_rooms = []
    current_rooms = [Room.clone(tile_map)]
    def room_needs_split(room):
        return (room.width > ROOM_MAXIMUM_WIDTH or room.height > ROOM_MAXIMUM_HEIGHT)
    while current_rooms:
        new_rooms = []
        for room in current_rooms:
            if not room_needs_split(room):
                final_rooms.append(room)
            else:
                split_x = (random.random() < ROOM_SPLIT_X_CHANCE)
                if not split_x and room.height >= 2 * ROOM_MINIMUM_HEIGHT:
                    # Split into top and bottom halves
                    split_start = ROOM_MINIMUM_HEIGHT
                    split_end = room.height - ROOM_MINIMUM_HEIGHT + 1
                    y = random.randrange(split_start, split_end)
                    new_rooms += list(room.split_y(y))
                elif split_x and room.width >= 2 * ROOM_MINIMUM_WIDTH:
                    # Split into left and right halves
                    split_start = ROOM_MINIMUM_WIDTH
                    split_end = room.width - ROOM_MINIMUM_WIDTH + 1
                    x = random.randrange(split_start, split_end)
                    new_rooms += list(room.split_x(x))
                else:
                    # Don't split this time
                    new_rooms.append(room)
        current_rooms = new_rooms
    return final_rooms


def generate_room_index(rooms):
    index = {}
    for room in rooms:
        for coord in Coord.range(room.tl, room.br):
            index[coord] = room
    return index


def calculate_walk_graph(tile_map):
    def find_top_left_empty():
        empty_coords = tile_map.find(is_tile(TILE_EMPTY))
        empty_coords = (coord for (coord, __) in empty_coords)
        return reduce(closest_to(0, 0), empty_coords)
    def is_solid(coord):
        return (tile_map.get(coord) in SOLID_TILES)
    def is_ladder(coord):
        return (tile_map.get(coord) == TILE_LADDER)
    def is_empty(coord):
        return (tile_map.get(coord) == TILE_EMPTY)
    def is_stair(coord):
        return (tile_map.get(coord) == TILE_STAIR)

    def find_floor(coord):
        return tile_map.cast_until(coord, Coord(0, 1), is_tile(*SOLID_TILES))

    # For each coord, store a boolean if it can be walked on
    coord_is_walkable = defaultdict(lambda: False)
    for coord in Coord.range((0, 0), (tile_map.width, tile_map.height)):
        """A coord is walkable if it is above a floor/stair or on a ladder."""
        up =  coord - Coord.Y
        down = coord + Coord.Y
        left = coord - Coord.X
        right = coord + Coord.X

        down_is_floor = is_solid(down)
        down_is_ladder = is_ladder(down)
        down_is_stair = is_stair(down)
        up_is_empty = is_empty(up)
        up_is_ladder = is_ladder(up)
        tile_is_empty = is_empty(coord)
        tile_is_ladder = is_ladder(coord)
        coord_is_walkable[coord] = (
            (up_is_empty
                and tile_is_empty
                and (down_is_floor or down_is_stair))
            or ((up_is_empty or up_is_ladder)
                and tile_is_ladder
                and (down_is_ladder or down_is_floor)))

    # For each coord, store a list of the coords you can walk to
    coord_reachability = defaultdict(list)
    # Start at the top left, just above the floor
    start_coord = find_floor(find_top_left_empty()) - Coord(0, 1)
    to_search = [start_coord]
    while to_search:
        coord = to_search.pop()
        if not coord_is_walkable[coord]: continue
        if coord in coord_reachability: continue
        reachable = coord_reachability[coord]

        up =  coord - Coord.Y
        down = coord + Coord.Y
        left = coord - Coord.X
        right = coord + Coord.X

        # Can always walk to neighbouring walkable coords
        if coord_is_walkable[up]:
            reachable.append(up)
            to_search.append(up)
        if coord_is_walkable[down]:
            reachable.append(down)
            to_search.append(down)
        if coord_is_walkable[left]:
            reachable.append(left)
            to_search.append(left)
        elif (is_stair(left) and coord_is_walkable[left - Coord.Y]):
            reachable.append(left - Coord.Y)
            to_search.append(left - Coord.Y)
        else:
            # Check if we can drop off an edge here
            if is_empty(left) and is_empty(left + (0, 1)):
                drop_to_coord = find_floor(left) - (0, 1)
                if Coord.height(left, drop_to_coord) <= WALK_DROP_HEIGHT:
                    reachable.append(drop_to_coord)
                    to_search.append(drop_to_coord)
        if coord_is_walkable[right]:
            reachable.append(right)
            to_search.append(right)
        elif (is_stair(right) and coord_is_walkable[right - Coord.Y]):
            reachable.append(right - Coord.Y)
            to_search.append(right - Coord.Y)
        else:
            # Check if we can drop off an edge here
            if is_empty(right) and is_empty(right + (0, 1)):
                drop_to_coord = find_floor(right) - (0, 1)
                if Coord.height(right, drop_to_coord) <= WALK_DROP_HEIGHT:
                    reachable.append(drop_to_coord)
                    to_search.append(drop_to_coord)

    return coord_reachability

def generate_filled_room(room):
    if room.width > FILLED_MAXIMUM_WIDTH or room.height > FILLED_MAXIMUM_HEIGHT:
        return
    fill = (random.random() < FILLED_CHANCE)
    if not fill:
        return
    room.fill(TILE_WALL)


def generate_floor_and_ceiling(room):
    """Find a random height for the floor that still allows the minimum walkable space."""
    if room.is_filled():
        return

    floor_max = min(room.height - CEILING_MINIMUM - FLOOR_TO_CEILING_MINIMUM, FLOOR_MAXIMUM)
    ceiling_max = min(room.height - FLOOR_MINIMUM - FLOOR_TO_CEILING_MINIMUM, CEILING_MAXIMUM)

    while True:
        floor_height = random.randrange(FLOOR_MINIMUM, floor_max + 1)
        ceiling_height = random.randrange(CEILING_MINIMUM, ceiling_max + 1)
        if room.height - ceiling_height - floor_height >= FLOOR_TO_CEILING_MINIMUM:
            break
    room.floor_height = floor_height
    room.ceiling_height = ceiling_height
    room.floor_subview().fill(TILE_FLOOR)
    room.ceiling_subview().fill(TILE_CEILING)


def generate_random_walls(room):
    """Decide whether to place walls."""
    if room.is_filled():
        return

    wall = (random.random() < WALL_CHANCE)
    left_hand = (random.random() < 0.5)

    # Determine wall size
    other_wall_width = (room.right_wall_width if left_hand else room.left_wall_width)
    max_width = min(room.width - WALL_MINIMUM - other_wall_width, WALL_MAXIMUM)
    wall_width = random.randrange(WALL_MINIMUM, max_width)

    # Create the wall (if there isn't one already)
    if wall:
        if left_hand and room.left_wall_width == 0:
            room[:wall_width,:] = TILE_WALL
            room.left_wall_width = wall_width
        elif not left_hand and room.right_wall_width == 0:
            room[room.width - wall_width:,:] = TILE_WALL
            room.right_wall_width = wall_width


def generate_required_walls(room, left_hand=False):
    """Place required walls."""
    if room.is_filled():
        return

    wall = False

    # Determine wall size
    other_wall_width = (room.right_wall_width if left_hand else room.left_wall_width)
    max_width = min(room.width - WALL_MINIMUM - other_wall_width, WALL_MAXIMUM)
    wall_width = random.randrange(WALL_MINIMUM, max_width)

    # Check if a wall should be forced
    edge = (0 if left_hand else room.width - 1)
    direction = (-1 if left_hand else +1)
    storage_edge = (0 if left_hand else room.storage.width - 1)
    if (room.tl.x + edge) == storage_edge:
        # Always have a wall at the edge
        wall = True
    else:
        # Always have a wall if not enough space for a doorway
        inside_slice = room.subview(tl=Coord(edge, 0), br=Coord(edge + 1, room.height)).linearize()
        outside_slice = room.subview(tl=Coord(edge + direction, 0), br=Coord(edge + direction + 1, room.height)).linearize()
        slices = zip(inside_slice, outside_slice)
        smallest_gap = shortest_subsequence(slices, (0, 0))
        if 0 < smallest_gap < WALL_MINIMUM_DOORWAY:
            wall = True

    # Create the wall (if there isn't one already)
    if wall:
        if left_hand and room.left_wall_width == 0:
            room[:wall_width,:] = TILE_WALL
            room.left_wall_width = wall_width
        elif not left_hand and room.right_wall_width == 0:
            room[room.width - wall_width:,:] = TILE_WALL
            room.right_wall_width = wall_width

def generate_floor_stairs(tile_map):
    """Place stairs to join uneven floor levels."""
    SOLID_EXCEPT_STAIRS = SOLID_TILES - set([TILE_STAIR])
    def is_solid(coord):
        return (tile_map.get(coord) in SOLID_EXCEPT_STAIRS)
    def is_empty(coord):
        return (tile_map.get(coord) == TILE_EMPTY)
    def is_empty_above(coord, height):
        for y in range(1, height + 1):
            if not is_empty(coord - (0, y)):
                return False
        return True
    def to_floor(coord):
        return tile_map.cast_until(coord, Coord(0, 1), is_tile(*SOLID_EXCEPT_STAIRS))
    def height_above_floor(coord):
        return Coord.height(coord, to_floor(coord))
    def wall_height(coord):
        try:
            bottom_coord = tile_map.cast_until(coord, Coord(0, 1), is_not(is_tile(*SOLID_EXCEPT_STAIRS)))
        except ValueError:
            bottom_coord = Coord(coord.x, tile_map.height)
        return Coord.height(coord, bottom_coord)
    def get_stair_direction(coord):
        left = coord - Coord.X
        right = coord + Coord.X
        if is_solid(left) and is_empty(right):
            return Coord.X
        elif is_empty(left) and is_solid(right):
            return -Coord.X
        else:
            return None

    def is_stair_location(tile_map, stair_start):
        """A stair location is one like:

          - E E E - -     E: empty
          - E E E E -     W: wall/floor
          = W[s]E E -     s: stair location, initially empty
          = W f s E -     f: backfill for stair, initially empty
          = W W W[W]=     =/-: don't care

        stair_start is `[s]`, stair_end is `[W]`.

        Return `stair_end` coordinate if can place a stair starting
        at `coord`, or False if not.
        """
        if not is_empty(stair_start): return False
        if not is_empty_above(stair_start, 2): return False
        stair_direction = get_stair_direction(stair_start)
        if stair_direction is None: return False
        wall_direction = -stair_direction
        wall_coord = stair_start + wall_direction

        # Ensure the stair is not too high
        stair_height = height_above_floor(stair_start)
        if stair_height > STAIR_MAXIMUM_HEIGHT: return False
        # Ensure there is standing room above the wall
        if not is_empty_above(wall_coord, 2): return False
        # Ensure there is wall all the way down
        if wall_height(wall_coord) < stair_height: return False
        # Then, moving diagonally down and right until hit floor:
        height = stair_height
        step_coord = stair_start
        while height > 1:
            height -= 1
            step_coord += (stair_direction + (0, 1))
            # Ensure the spot is empty
            if not is_empty(step_coord): return False
            # Ensure there is standing room + 1 above
            if not is_empty_above(step_coord, 3): return False
            # Ensure there is space - n below before a floor
            if height_above_floor(step_coord) != height: return False
        stair_end = step_coord + (stair_direction + (0, 1))
        # Check the floor where the stair ends
        if not is_solid(stair_end): return False
        if not is_empty_above(stair_end, 3): return False
        return stair_end

    stairs = []
    for stair_start, stair_end in tile_map.find(is_stair_location):
        should_make_stair = (random.random() < STAIR_CHANCE)
        if not should_make_stair: continue

        step = Coord(
            1 if (stair_end.x > stair_start.x) else -1,
            1 if (stair_end.y > stair_start.y) else -1)
        coord = stair_start
        while is_empty(coord):
            floor_coord = to_floor(coord)
            tile_map[coord:(floor_coord + Coord.X)] = TILE_FLOOR
            tile_map[coord] = TILE_STAIR
            coord += step

def generate_random_ladders(tile_map):
    """Place random ladders."""

    def can_place_ladder(tile_map, ladder_start):
        """Return a `ladder_end` coordinate if a ladder can be placed
        starting at `coord`, or `False` if it cannot.

              ladder_start
                    |
                    V
            [empty empty empty]
            [solid solid solid]+
            [empty empty empty]{2,}
            [solid solid solid]
                           ^
                           |
                       ladder_end
        """
        if ladder_start.x < 1 or ladder_start.x >= tile_map.width - 2: return False
        if ladder_start.y < 0 or ladder_start.y >= tile_map.height - 1: return False

        tl = Coord(ladder_start.x - 1, ladder_start.y)
        br = Coord(ladder_start.x + 2, tile_map.height)
        subview = tile_map[tl:br]

        def is_empty_line(y):
            if y >= subview.height: return False
            for x in range(subview.width):
                if subview[x, y] != TILE_EMPTY:
                    return False
            return True
        def is_solid_line(y):
            if y >= subview.height: return False
            for x in range(subview.width):
                if subview[x, y] not in (TILE_WALL, TILE_FLOOR, TILE_CEILING):
                    return False
            return True

        empty_lines_above = 0
        solid_lines_above = 0
        empty_lines_below = 0
        solid_lines_below = 0
        y = 0
        while is_empty_line(y):
            empty_lines_above += 1
            y += 1
        if empty_lines_above != 1: return False
        while is_solid_line(y):
            solid_lines_above += 1
            y += 1
        if solid_lines_above < 1: return False
        while is_empty_line(y):
            empty_lines_below += 1
            y += 1
        if empty_lines_below < LADDER_MINIMUM_HEIGHT: return False
        if is_solid_line(y):
            solid_lines_below += 1
        if solid_lines_below != 1: return False

        ladder_end = Coord(subview.width - 1, y)
        ladder_end = subview.to_other(ladder_end, tile_map)
        if Coord.height(ladder_start, ladder_end) > LADDER_MAXIMUM_HEIGHT: return False

        return ladder_end

    ladders = list(tile_map.find(can_place_ladder))
    ladder_count = int(round(float(len(ladders)) * LADDER_DENSITY))

    while ladder_count and ladders:
        # Find a ladder position and build it
        ladder = random.choice(ladders)
        ladder_start, ladder_end = ladder
        tile_map[ladder_start:ladder_end] = TILE_LADDER
        # Remove all overlapping ladder positions
        def does_not_overlap(other_ladder):
            overlaps = (ladder_start[0] - LADDER_HORIZONTAL_SPACE < other_ladder[1][0]
                and ladder_end[0] + LADDER_HORIZONTAL_SPACE > other_ladder[0][0]
                and ladder_start[1] - LADDER_VERTICAL_SPACE < other_ladder[1][1]
                and ladder_end[1] + LADDER_VERTICAL_SPACE > other_ladder[0][1])
            return not overlaps

        ladders = filter(does_not_overlap, ladders)
        ladder_count -= 1


class Room(TileMap):
    def __init__(self, *args, **kwargs):
        super(Room, self).__init__(*args, **kwargs)
        self.floor_height = 0
        self.ceiling_height = 0
        self.left_wall_width = 0
        self.right_wall_width = 0

    def floor_subview(self):
        return self[:,(self.height - self.floor_height):]

    def ceiling_subview(self):
        return self[:,:self.ceiling_height]

    def is_filled(self):
        for coord, __ in self.find(is_not(is_tile(*SOLID_TILES))):
            return False
        return True

if __name__ == '__main__':
    main()
