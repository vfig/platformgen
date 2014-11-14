__all__ = ('Coord', 'TileMap')

from collections import defaultdict, namedtuple
from filters import is_tile

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

class Coord(namedtuple('Coord', ['x', 'y'])):
    @classmethod
    def from_tuple(cls, tup):
        if isinstance(tup, cls):
            return tup
        else:
            return cls(tup[0], tup[1])

    @classmethod
    def range(cls, c1, c2):
        for y in range(c1[1], c2[1]):
            for x in range(c1[0], c2[0]):
                yield Coord(x, y)

    @classmethod
    def width(cls, c1, c2):
        return abs(c1[0] - c2[0])

    @classmethod
    def height(cls, c1, c2):
        return abs(c1[1] - c2[1])

    def __add__(self, other):
        return self.__class__(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other):
        return self.__class__(self[0] - other[0], self[1] - other[1])

    def __mul__(self, scalar):
        return self.__class__(self[0] * scalar, self[1] * scalar)

    def __neg__(self):
        return self.__class__(-self[0], -self[1])

Coord.X = Coord(1, 0)
Coord.Y = Coord(0, 1)


class TileMap(object):
    """Subscriptable, editable view onto a TileMap."""

    def __init__(self, tl=None, br=None, width=0, height=0, storage=None):
        if tl is None:
            tl = Coord(0, 0)
        else:
            tl = Coord.from_tuple(tl)

        if br is None:
            br = Coord(tl.x + width, tl.y + height)
        else:
            br = Coord.from_tuple(br)

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
        return Coord.width(self.tl, self.br)

    @property
    def height(self):
        return Coord.height(self.tl, self.br)

    @classmethod
    def clone(cls, tile_map):
        return cls(tl=tile_map.tl, br=tile_map.br, storage=tile_map.storage)

    def to_other(self, coord, other):
        return Coord(coord.x + self.tl.x - other.tl.x,
            coord.y + self.tl.y - other.tl.y)

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
        if Coord.width(tl, br) == 1 and Coord.height(tl, br) == 1:
            tl = self._local_to_storage(tl)
            return self.storage[tl]
        else:
            return self.subview(tl=tl, br=br)

    def __setitem__(self, subscript, value):
        """Set the value at (x, y), or fill the range (if either x or y is a slice) with the value."""
        tl, br = self._parse_subscript(subscript)
        if isinstance(value, TileMap):
            for coord in Coord.range(tl, br):
                coord = self._local_to_storage(coord)
                other_coord = Coord(coord.x - tl.x, coord.y - tl.y)
                other_coord = value._local_to_storage(other_coord)
                self.storage[coord] = value.storage[other_coord]
        else:
            if Coord.width(tl, br) == 1 and Coord.height(tl, br) == 1:
                tl = self._local_to_storage(tl)
                self.storage[tl] = value
            else:
                self.subview(tl=tl, br=br).fill(value)

    def __contains__(self, value):
        if isinstance(value, TileMap):
            raise TypeError("__contains__ does not support TileMaps yet.")
        for coord, __ in self.find(is_tile(value)):
            return True
        return False

    def get(self, subscript):
        try:
            return self[subscript]
        except IndexError:
            return None

    def find(self, predicate):
        """
        Return an iterable of `(coordinate, data)` for which
        `predicate(tile_map, coord)` returns a not False `data`.
        """
        for coord in Coord.range(self.tl, self.br):
            tile = self.storage[coord]
            arg = self._storage_to_local(coord)
            data = predicate(self, arg)
            if data:
                yield (arg, data)

    def cast_until(self, start, increment, predicate):
        """
        Return the first coordinate from `start` in steps
        of `increment` where `predicate(tile_map, coord)` returns True.

        Raises ValueError if the predicate never returned True.
        """
        coord = start
        end = self._storage_to_local(self.br)
        def in_range(coord):
            return (coord.x < end.x and coord.y < end.y)
        while in_range(coord) and not predicate(self, coord):
            coord += increment
        if in_range(coord):
            return coord
        else:
            raise ValueError("Coordinate matching predicate not found.")

    def copy(self):
        subview = self.subview()
        subview.storage = self.storage.copy()
        return subview

    def fill(self, value):
        for coord in Coord.range(self.tl, self.br):
            self.storage[coord] = value

    def subview(self, tl=None, br=None):
        """Return a subview at the given location (default top left) and size (default maximum)."""
        if tl is None:
            tl = Coord(0, 0)
        else:
            tl = Coord.from_tuple(tl)
        if br is None:
            br = Coord(self.width, self.height)
        else:
            br = Coord.from_tuple(br)
        tl = self._local_to_storage(tl)
        br = self._local_to_storage(br)
        return self.__class__(tl=tl, br=br, storage=self.storage)

    def linearize(self):
        """Return a linear iterable of all values in this tile map."""
        return (self.storage[coord] for coord in Coord.range(self.tl, self.br))

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
