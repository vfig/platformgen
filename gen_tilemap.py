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
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = []
        for y in range(self.height):
            self.tiles.append([0] * self.width)

    def __getitem__(self, index):
        return self.tiles[index]

if __name__ == '__main__':
    main()
