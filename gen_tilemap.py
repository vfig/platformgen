#!/usr/local/bin/python
import random, time
from gui import TileMapGUI

# Generation parameters
ROOM_SPLIT_X_CHANCE = 0.5
ROOM_MINIMUM_HEIGHT = 6
ROOM_MAXIMUM_HEIGHT = 16
ROOM_MINIMUM_WIDTH = 8
ROOM_MAXIMUM_WIDTH = 20

# Tile types
TILE_EMPTY = 0

# seed = int(time.time())
seed = 1415535932
print "random seed:", seed
random.seed(seed)

def generate_rooms(tile_map):
    # Recursively partition the tile map
    final_rooms = []
    current_rooms = [TileMapView(tile_map, 0, 0, tile_map.width, tile_map.height)]
    def room_needs_split(room):
        return (room.width > ROOM_MAXIMUM_WIDTH or room.height > ROOM_MAXIMUM_HEIGHT)
    while current_rooms:
        new_rooms = []
        for room in current_rooms:
            if not room_needs_split(room):
                final_rooms.append(room)
            else:
                split_x = (random.random() < ROOM_SPLIT_X_CHANCE)
                if not split_x and room.height > 2 * ROOM_MINIMUM_HEIGHT:
                    # Split into top and bottom halves
                    split_start = ROOM_MINIMUM_HEIGHT
                    split_end = room.height - ROOM_MINIMUM_HEIGHT
                    y = random.randrange(split_start, split_end)
                    new_rooms += list(room.split_y(y))
                elif split_x and room.width > 2 * ROOM_MINIMUM_WIDTH:
                    # Split into left and right halves
                    split_start = ROOM_MINIMUM_WIDTH
                    split_end = room.width - ROOM_MINIMUM_WIDTH
                    x = random.randrange(split_start, split_end)
                    new_rooms += list(room.split_x(x))
                else:
                    # Don't split this time
                    new_rooms.append(room)
        current_rooms = new_rooms
    return final_rooms

def main():
    tile_size = 16
    tile_map = TileMap(256, 128)
    rooms = generate_rooms(tile_map)

    # # Fill in the views
    # for i, room in enumerate(rooms, start=1):
    #     room.fill(i)

    tile_colors = {
        TILE_EMPTY: '#000000',
        None: '',
        }
    # colors = ColorGenerator()
    # for i, room in enumerate(rooms, start=1):
    #     tile_colors[i] = next(colors)

    gui = TileMapGUI(tile_map, tile_size, tile_colors, rooms=rooms)
    gui.run()





# choose a random direction : horizontal or vertical splitting
# choose a random position (x for vertical, y for horizontal)
# split the dungeon into two sub-dungeons

class TileMap(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._tiles = []
        for y in range(self.height):
            self._tiles.append([0] * self.width)

    def __getitem__(self, index):
        return TileMapRowView(self, 0, index, self.width)

class TileMapRowView(object):
    def __init__(self, tile_map, x, y, width):
        assert x >= 0
        assert y >= 0
        assert (x + width) <= tile_map.width
        self.tile_map = tile_map
        self.x = x
        self.y = y
        self.width = width

    def __getitem__(self, x):
        if x >= self.x and x < self.x + self.width:
            return self.tile_map._tiles[self.y][x]
        else:
            raise IndexError(x)

    def __setitem__(self, x, value):
        if x >= self.x and x < self.x + self.width:
            self.tile_map._tiles[self.y][x] = value
        else:
            raise IndexError(x)

class TileMapView(object):
    def __init__(self, tile_map, x, y, width, height):
        assert x >= 0
        assert y >= 0
        assert (x + width) <= tile_map.width
        assert (y + height) <= tile_map.height
        self.tile_map = tile_map
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __getitem__(self, y):
        if y >= self.y and y < self.y + self.height:
            return TileMapRowView(self.tile_map, y)
        else:
            raise IndexError(y)

    def fill(self, value):
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                self.tile_map._tiles[y][x] = value

    def subview(self, x=None, y=None, width=None, height=None):
        """Return a subview at the given location (default top left) and size (default maximum)."""
        if x is None: x = self.x
        if y is None: y = self.y
        if width is None: width = self.width - x
        if height is None: height = self.height - y
        return self.__class__(tile_map=self.tile_map, x=x, y=y, width=width, height=height)

    def split_x(self, x):
        """Return a pair of views that are the halves of the tile map split vertically at `x`."""
        return (
            self.subview(self.x, self.y, x, self.height),
            self.subview(self.x + x, self.y, self.width - x, self.height)
            )

    def split_y(self, y):
        """Return a pair of views that are the halves of the tile map split horizontally at `y`."""
        return (
            self.subview(self.x, self.y, self.width, y),
            self.subview(self.x, self.y + y, self.width, self.height - y)
            )

if __name__ == '__main__':
    main()
