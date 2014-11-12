#!/usr/local/bin/python
import collections, random, time
from color import ColorGenerator
from filters import is_not, is_tile, closest_to
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
SOLID_TILES = [TILE_FLOOR, TILE_CEILING, TILE_WALL]

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
    # reachability = calculate_reachability(tile_map, rooms)

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
        for coord in coord_range(room.tl, room.br):
            index[coord] = room
    return index

def calculate_reachability(tile_map, rooms):
    reachable = {}
    # searched = set()
    to_search = []

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

    def __getitem__(self, subscript):
        assert isinstance(subscript, Coord)
        return self.tiles[subscript.y][subscript.x]

    def __setitem__(self, subscript, value):
        assert isinstance(subscript, Coord)
        self.tiles[subscript.y][subscript.x] = value

    def copy(self):
        storage = self.__class__(width=self.width, height=self.height)
        storage.tiles = []
        for y in range(self.height):
            storage.tiles.append(list(self.tiles[y]))
        return storage

Coord = collections.namedtuple('Coord', ['x', 'y'])

def make_coord(tup):
    return Coord(tup[0], tup[1])
def coord_width(c1, c2):
    return (c2.x - c1.x)
def coord_height(c1, c2):
    return (c2.y - c1.y)
def coord_add(c1, c2):
    return Coord(c1.x + c2.x, c1.y + c2.y)
def coord_sub(c1, c2):
    return Coord(c1.x - c2.x, c1.y - c2.y)
def coord_range(c1, c2):
    for y in range(c1.y, c2.y):
        for x in range(c1.x, c2.x):
            yield Coord(x, y)


class TileMap(object):
    """Subscriptable, editable view onto a TileMap."""

    def __init__(self, tl=None, br=None, width=0, height=0, storage=None):
        if tl is None:
            tl = Coord(0, 0)
        else:
            tl = make_coord(tl)

        if br is None:
            br = Coord(tl.x + width, tl.y + height)
        else:
            br = make_coord(br)

        if storage is None:
            storage = TileMapStorage(width, height)

        assert isinstance(storage, TileMapStorage)
        assert tl.x >= 0
        assert tl.y >= 0
        assert tl.x < br.x
        assert tl.y < br.y
        assert br.x <= storage.width
        assert br.y <= storage.height

        self.storage = storage
        self.tl = tl
        self.br = br

    @property
    def width(self):
        return coord_width(self.tl, self.br)

    @property
    def height(self):
        return coord_height(self.tl, self.br)

    @classmethod
    def clone(cls, tile_map):
        return cls(tl=tile_map.tl, br=tile_map.br, storage=tile_map.storage)

    def _local_to_storage(self, coord):
        return Coord(coord.x + self.tl.x, coord.y + self.tl.y)

    def _storage_to_local(self, coord):
        return Coord(coord.x - self.tl.x, coord.y - self.tl.y)

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

        return Coord(x, y), Coord(x + width, y + height)

    def __str__(self):
        lines = ['']
        for y in range(self.tl.y, self.br.y):
            line = []
            for x in range(self.tl.x, self.br.x):
                line.append('%3s' % repr(self.storage[Coord(x, y)]))
            lines.append(' '.join(line))
        return '\n    '.join(lines)

    def __getitem__(self, subscript):
        """Return the value at (x, y), or a subview of the range (if either x or y is a slice)."""
        tl, br = self._parse_subscript(subscript)
        if coord_width(tl, br) == 1 and coord_height(tl, br) == 1:
            tl = self._local_to_storage(tl)
            return self.storage[tl]
        else:
            return self.subview(tl=tl, br=br)

    def __setitem__(self, subscript, value):
        """Set the value at (x, y), or fill the range (if either x or y is a slice) with the value."""
        tl, br = self._parse_subscript(subscript)
        if isinstance(value, TileMap):
            for coord in coord_range(tl, br):
                coord = self._local_to_storage(coord)
                other_coord = Coord(coord.x - tl.x, coord.y - tl.y)
                other_coord = value._local_to_storage(other_coord)
                self.storage[coord] = value.storage[other_coord]
        else:
            if coord_width(tl, br) == 1 and coord_height(tl, br) == 1:
                tl = self._local_to_storage(tl)
                self.storage[tl] = value
            else:
                self.subview(tl=tl, br=br).fill(value)

    def __contains__(self, value):
        if isinstance(value, TileMap):
            raise TypeError("__contains__ does not support TileMaps yet.")
        for coord in self.find(is_tile(value)):
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
        for coord in coord_range(self.tl, self.br):
            tile = self.storage[coord]
            arg = self._storage_to_local(coord)
            if predicate(self, *arg):
                yield arg

    def copy(self):
        subview = self.subview()
        subview.storage = self.storage.copy()
        return subview

    def fill(self, value):
        for coord in coord_range(self.tl, self.br):
            self.storage[coord] = value

    def subview(self, tl=None, br=None):
        """Return a subview at the given location (default top left) and size (default maximum)."""
        if tl is None:
            tl = Coord(0, 0)
        else:
            tl = make_coord(tl)
        if br is None:
            br = Coord(self.width, self.height)
        else:
            br = make_coord(br)
        tl = self._local_to_storage(tl)
        br = self._local_to_storage(br)
        return self.__class__(tl=tl, br=br, storage=self.storage)

    def linearize(self):
        """Return a linear iterable of all values in this tile map."""
        return (self.storage[coord] for coord in coord_range(self.tl, self.br))

    def split_x(self, x):
        """Return a pair of views that are the halves of the tile map split vertically at `x`."""
        assert 0 <= x < self.width
        return (
            self.subview(tl=Coord(0, 0), br=Coord(x, self.height)),
            self.subview(tl=Coord(x, 0), br=Coord(self.width, self.height))
            )

    def split_y(self, y):
        """Return a pair of views that are the halves of the tile map split horizontally at `y`."""
        assert 0 <= y < self.height
        return (
            self.subview(tl=Coord(0, 0), br=Coord(self.width, y)),
            self.subview(tl=Coord(0, y), br=Coord(self.width, self.height))
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
        for coord in self.find(is_not(is_tile(*SOLID_TILES))):
            return False
        return True

if __name__ == '__main__':
    main()
