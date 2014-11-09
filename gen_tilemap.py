#!/usr/local/bin/python
from gui import TileMapGUI

def main():
    tile_size = 32
    tile_map = TileMap(128, 128)
    tile_map[1][1] = 1
    tile_map[1][2] = 2
    tile_map[1][3] = 3
    tile_colors = {
        0: '',
        1: 'red',
        2: 'blue',
        None: '#ffff33',
        }
    gui = TileMapGUI(tile_map, tile_size, tile_colors)
    gui.run()

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

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._tiles = []
        for y in range(self.height):
            self._tiles.append([0] * self.width)

    def __getitem__(self, index):
        return TileMap.RowView(self, 0, index, self.width)

if __name__ == '__main__':
    main()
