#!/usr/local/bin/python
import collections, random, time
from color import ColorGenerator
from filters import is_tile, closest_to
from gui import TileMapGUI
from util import contains_subsequence, shortest_subsequence

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

# Tile types
TILE_EMPTY = 0
TILE_FLOOR = 1
TILE_CEILING = 2
TILE_WALL = 3
TILE_LADDER = 4
SOLID_TILES = set([TILE_FLOOR, TILE_CEILING, TILE_WALL])

# seed = int(time.time())
seed = 1415535932
print "random seed:", seed
random.seed(seed)

def main():
    tile_size = 8
    tile_map = TileMap(width=TILE_MAP_WIDTH, height=TILE_MAP_HEIGHT)
    rooms = generate_rooms(tile_map)
    for room in rooms:
        generate_filled_room(room)
    for room in rooms:
        generate_floor_and_ceiling(room)
    for room in rooms:
        generate_random_walls(room)
    for room in rooms:
        generate_required_walls(room, left_hand=True)
        generate_required_walls(room, left_hand=False)
    generate_random_ladders(tile_map)
    reachability = calculate_reachability(tile_map, rooms)

    # room_index = generate_room_index(rooms)
    # calculate_reachability(rooms)

    tile_colors = {
        TILE_EMPTY: '#000000',
        TILE_FLOOR: '#666699',
        TILE_CEILING: '#663333',
        TILE_WALL: '#666633',
        TILE_LADDER: '#ff0000',
        None: '',
        }

    gui = TileMapGUI(tile_map, tile_size, tile_colors, rooms=rooms)
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
        for y in range(room.y, room.y + room.width):
            for x in range(room.x, room.x + room.height):
                index[(x, y)] = room
    return index

def calculate_reachability(tile_map, rooms):
    reachability = {}

    # Find the top-left-most TILE_EMPTY just above a floor, use it as the seed
    empty_coords = tile_map.find(is_tile(TILE_EMPTY))
    start_coord = reduce(closest_to(0, 0), empty_coords)
    # vslice = tile_map[


    print "Top-lef-most TILE_EMPTY is at:", start_coord
    return None

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
    if (room.x + edge) == storage_edge:
        # Always have a wall at the edge
        wall = True
    else:
        # Always have a wall if not enough space for a doorway
        inside_slice = room.subview(edge, 0, 1, room.height).linearize()
        outside_slice = room.subview(edge + direction, 0, 1, room.height).linearize()
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


def generate_random_ladders(tile_map):
    """Place random ladders."""

    def can_place_ladder(x, y):
        """Return (ladder_start, ladder_end) if can place a ladder at (x, y), where
        ladder_start and ladder end are both coordinate pairs of the actual ladder.

        Searches for:
            [empty empty empty]
            [solid solid solid]+
            [empty empty empty]{2,}
            [solid solid solid]

        Choose ladders randomly, ensuring they aren't chosen too close together.
        """
        ladder_start = (x + 1, y)
        # Make sure there's enough space
        if x >= tile_map.width - 3: return False
        # First line must be empty
        if y >= tile_map.height: return False
        line = tile_map[x:x+3,y]; y += 1
        if TILE_WALL in line or TILE_FLOOR in line or TILE_CEILING in line or TILE_LADDER in line:
            return False
        # Second line must be all solid
        if y >= tile_map.height: return False
        line = tile_map[x:x+3,y]; y += 1
        if TILE_EMPTY in line or TILE_LADDER in line:
            return False
        # Subsequent lines must be all solid or all empty
        solid_height = 1
        empty_height = 0
        solid = True
        while solid:
            if y >= tile_map.height: return False
            line = tile_map[x:x+3,y]; y += 1
            found_empty = found_solid = False
            if TILE_EMPTY in line or TILE_LADDER in line:
                found_empty = True
            if TILE_WALL in line or TILE_FLOOR in line or TILE_CEILING in line or TILE_LADDER in line:
                found_solid = True
            if found_empty and not found_solid:
                empty_height += 1
                solid = False
            elif found_solid and not found_empty:
                solid_height += 1
            else:
                return False
        # Then there must be at least LADDER_MINIMUM_HEIGHT clear lines before a solid floor
        while not solid:
            if y >= tile_map.height: return False
            line = tile_map[x:x+3,y]; y += 1
            found_empty = found_solid = False
            if TILE_EMPTY in line or TILE_LADDER in line:
                found_empty = True
            if TILE_WALL in line or TILE_FLOOR in line or TILE_CEILING in line or TILE_LADDER in line:
                found_solid = True
            if found_empty and not found_solid:
                empty_height += 1
            elif found_solid and not found_empty:
                solid = True
            else:
                return False
        if empty_height < LADDER_MINIMUM_HEIGHT: return False
        if empty_height + solid_height + 1 > LADDER_MAXIMUM_HEIGHT: return False
        ladder_end = (ladder_start[0] + 1 , ladder_start[1] + solid_height + empty_height + 1)
        return (ladder_start, ladder_end)

    ladders = []
    for y in range(tile_map.height):
        for x in range(tile_map.width):
            ladder = can_place_ladder(x, y)
            if not ladder: continue
            ladders.append(ladder)

    ladder_count = int(round(float(len(ladders)) * LADDER_DENSITY))
    #10th ladder and 1st ladder
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

class TileMapStorage(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = []
        for y in range(self.height):
            self.tiles.append([0] * self.width)

    def copy(self):
        storage = self.__class__(width=self.width, height=self.height)
        storage.tiles = []
        for y in range(self.height):
            storage.tiles.append(list(self.tiles[y]))
        return storage

Coord = collections.namedtuple('Coord', ['x', 'y'])

class TileMap(object):
    """Subscriptable, editable view onto a TileMap."""

    def __init__(self, x=0, y=0, width=0, height=0, storage=None):
        assert x >= 0
        assert y >= 0
        if storage:
            assert (x + width) <= storage.width
            assert (y + height) <= storage.height
        self.storage = storage or TileMapStorage(width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @classmethod
    def clone(cls, tile_map):
        return cls(x=tile_map.x, y=tile_map.y,
            width=tile_map.width, height=tile_map.height,
            storage=tile_map.storage)

    def _parse_subscript(self, subscript):
        if isinstance(subscript, slice):
            assert isinstance(subscript.start, tuple)
            assert len(subscript.start) == 2
            assert isinstance(subscript.stop, tuple)
            assert len(subscript.stop) == 2
            subscript = (
                slice(subscript.start[0], subscript.stop[0]),
                slice(subscript.start[1], subscript.stop[1]),
                )
        assert isinstance(subscript, tuple)
        assert len(subscript) == 2

        x, y = subscript
        width, height = (1, 1)

        if isinstance(x, slice):
            start, stop, step = x.start, x.stop, x.step
            if start is None: start = 0
            if stop is None: stop = self.width
            if step is None: step = 1
            assert step == 1
            width = stop - start
            x = start

        if isinstance(y, slice):
            start, stop, step = y.start, y.stop, y.step
            if start is None: start = 0
            if stop is None: stop = self.height
            if step is None: step = 1
            assert step == 1
            height = stop - start
            y = start

        if x < 0 or x + width > self.width or \
            y < 0 or y + height > self.height or \
            width == 0 or height == 0:
            raise IndexError(subscript)

        return (x, y, width, height)

    def __str__(self):
        lines = ['']
        for y in range(self.y, self.y + self.height):
            line = []
            for x in range(self.x, self.x + self.width):
                line.append('%3s' % repr(self.storage.tiles[y][x]))
            lines.append(' '.join(line))
        return '\n    '.join(lines)

    def __getitem__(self, subscript):
        """Return the value at (x, y), or a subview of the range (if either x or y is a slice)."""
        x, y, width, height = self._parse_subscript(subscript)
        if width == 1 and height == 1:
            return self.storage.tiles[self.y + y][self.x + x]
        else:
            return self.subview(x, y, width, height)

    def __setitem__(self, subscript, value):
        """Set the value at (x, y), or fill the range (if either x or y is a slice) with the value."""
        x, y, width, height = self._parse_subscript(subscript)
        if isinstance(value, TileMap):
            for j in range(height):
                for i in range(width):
                    if j < value.height and i < value.width:
                        other_value = value.storage.tiles[value.y + j][value.x + i]
                    else:
                        other_value = 0
                    self.storage.tiles[self.y + j][self.x + i] = other_value
        else:
            if width == 1 and height == 1:
                self.storage.tiles[self.y + y][self.x + x] = value
            else:
                self.subview(x, y, width, height).fill(value)

    def __contains__(self, value):
        if isinstance(value, TileMap):
            raise TypeError("__contains__ does not support TileMaps yet.")
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                if self.storage.tiles[y][x] == value:
                    return True
        return False

    def get(self, subscript):
        try:
            return self[subscript]
        except IndexError:
            return None

    def find(self, predicate):
        """
        Return an iterable of all `(x, y)` coordinates for which
        `predicate(tile_map, x, y)` returns True.
        """
        for y in range(self.height):
            for x in range(self.width):
                tile = self.storage.tiles[self.y + y][self.x + x]
                arg = Coord(x, y)
                if predicate(self, *arg):
                    yield arg

    def copy(self):
        subview = self.subview()
        subview.storage = self.storage.copy()
        return subview

    def fill(self, value):
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                self.storage.tiles[y][x] = value

    def subview(self, x=None, y=None, width=None, height=None):
        """Return a subview at the given location (default top left) and size (default maximum)."""
        if x is None: x = 0
        if y is None: y = 0
        if width is None: width = self.width 
        if height is None: height = self.height
        return self.__class__(
            x=(self.x + x), y=(self.y + y),
            width=width, height=height,
            storage=self.storage)

    def linearize(self):
        """Return a linear sequence of all values in this tile map."""
        values = []
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                values.append(self.storage.tiles[y][x])
        return values

    def split_x(self, x):
        """Return a pair of views that are the halves of the tile map split vertically at `x`."""
        return (
            self.subview(0, 0, x, self.height),
            self.subview(x, 0, self.width - x, self.height)
            )

    def split_y(self, y):
        """Return a pair of views that are the halves of the tile map split horizontally at `y`."""
        return (
            self.subview(0, 0, self.width, y),
            self.subview(0, y, self.width, self.height - y)
            )

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
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                if self.storage.tiles[y][x] not in SOLID_TILES:
                    return False
        return True

if __name__ == '__main__':
    main()
