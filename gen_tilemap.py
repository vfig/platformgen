#!/usr/local/bin/python
import colorsys, random, time
from gui import TileMapGUI

ROOM_SPLIT_X_CHANCE = 0.25
ROOM_MINIMUM_HEIGHT = 4
ROOM_MAXIMUM_HEIGHT = 12
ROOM_MINIMUM_WIDTH = 6
ROOM_MAXIMUM_WIDTH = 20

# seed = int(time.time())
seed = 1415535932
print "random seed:", seed
random.seed(seed)

def main():
    tile_size = 16
    tile_map = TileMap(256, 128)

    # Recursively partition the tile map
    final_rooms = []
    current_rooms = [tile_map.view()]
    def room_needs_split(room):
        return (room.width > ROOM_MAXIMUM_WIDTH or room.height > ROOM_MAXIMUM_HEIGHT)
    while any(room_needs_split(room) for room in current_rooms):
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

    # Fill in the views
    for i, room in enumerate(final_rooms, start=1):
        room.fill(i)

    # Generate colors
    existing_colors = set()
    def random_color():
        h = random.random()
        s = 0.75 + random.random() * 0.25
        v = 0.5 + random.random() * 0.5
        (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        return '#%02x%02x%02x' % (r, g, b)
    def new_color():
        color = random_color()
        while color in existing_colors:
            color = random_color()
        return color
    tile_colors = {
        0: '',
        None: '',
        }
    for i, room in enumerate(final_rooms, start=1):
        tile_colors[i] = new_color()

    gui = TileMapGUI(tile_map, tile_size, tile_colors)
    gui.run()





# choose a random direction : horizontal or vertical splitting
# choose a random position (x for vertical, y for horizontal)
# split the dungeon into two sub-dungeons

class TileMap(object):
    class RowView(object):
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

    class View(object):
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
                return RowView(self.tile_map, y)
            else:
                raise IndexError(y)

        def fill(self, value):
            for y in range(self.y, self.y + self.height):
                for x in range(self.x, self.x + self.width):
                    self.tile_map._tiles[y][x] = value

        def split_x(self, x):
            """Return a pair of views that are the halves of the tile map split vertically at `x`."""
            return (
                TileMap.View(self.tile_map, self.x, self.y, x, self.height),
                TileMap.View(self.tile_map, self.x + x, self.y, self.width - x, self.height)
                )

        def split_y(self, y):
            """Return a pair of views that are the halves of the tile map split horizontally at `y`."""
            return (
                TileMap.View(self.tile_map, self.x, self.y, self.width, y),
                TileMap.View(self.tile_map, self.x, self.y + y, self.width, self.height - y)
                )

    # TileMap
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._tiles = []
        for y in range(self.height):
            self._tiles.append([0] * self.width)

    def __getitem__(self, index):
        return TileMap.RowView(self, 0, index, self.width)

    def view(self):
        return TileMap.View(self, 0, 0, self.width, self.height)

if __name__ == '__main__':
    main()
