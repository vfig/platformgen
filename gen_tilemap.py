#!/usr/local/bin/python
import random, time
from color import ColorGenerator
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

# Tile types
TILE_EMPTY = 0
TILE_FLOOR = 1
TILE_CEILING = 2
TILE_WALL = 3

# seed = int(time.time())
seed = 1415535932
print "random seed:", seed
random.seed(seed)

def main():
    tile_size = 32
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

    tile_colors = {
        TILE_EMPTY: '#000000',
        TILE_FLOOR: '#666699',
        TILE_CEILING: '#663333',
        TILE_WALL: '#666633',
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


def generate_filled_room(room):
    if room.width > FILLED_MAXIMUM_WIDTH or room.height > FILLED_MAXIMUM_HEIGHT:
        return
    fill = (random.random() < FILLED_CHANCE)
    if not fill:
        return
    room[:,:] = TILE_WALL
    room.filled = True


def generate_floor_and_ceiling(room):
    """Find a random height for the floor that still allows the minimum walkable space."""
    if room.filled:
        return

    floor_max = min(room.height - CEILING_MINIMUM - FLOOR_TO_CEILING_MINIMUM, FLOOR_MAXIMUM)
    ceiling_max = min(room.height - FLOOR_MINIMUM - FLOOR_TO_CEILING_MINIMUM, CEILING_MAXIMUM)

    while True:
        floor_height = random.randrange(FLOOR_MINIMUM, floor_max + 1)
        ceiling_height = random.randrange(CEILING_MINIMUM, ceiling_max + 1)
        if room.height - ceiling_height - floor_height >= FLOOR_TO_CEILING_MINIMUM:
            break
    room[:,(room.height - floor_height):] = TILE_FLOOR
    room[:,:ceiling_height] = TILE_CEILING
    room.floor_height = floor_height
    room.ceiling_height = ceiling_height


def generate_random_walls(room):
    """Decide whether to place walls."""
    if room.filled:
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
    if room.filled:
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
            y < 0 or y + height > self.height:
            raise IndexError(subscript)

        return (x, y, width, height)

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
        self.filled = False
        self.floor_height = 0
        self.ceiling_height = 0
        self.left_wall_width = 0
        self.right_wall_width = 0

if __name__ == '__main__':
    main()
