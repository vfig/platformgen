
## Filtering ################################################################

def is_not(predicate):
    def not_predicate(*args):
        return not predicate(*args)
    return not_predicate

def is_tile(*tiles):
    """Return a predicate function for `find()` that will
    find all coordinates containing one of `tiles`."""
    tiles = set(tiles)
    def predicate(tile_map, x, y):
        tile = tile_map[(x, y)]
        return (tile in tiles)
    return predicate


## Reduction ################################################################

def closest_to(ref_x, ref_y):
    """Return a function for `reduce()` that will return
    the coordinator closest to `(ref_x, ref_y)`."""
    def reducer(min_coord, coord):
        x, y = coord
        min_x, min_y = min_coord
        distance = ((x - ref_x) ** 2 + (y - ref_y) ** 2)
        min_distance = ((min_x - ref_x) ** 2 + (min_y - ref_y) ** 2)
        if distance < min_distance:
            return coord
        else:
            return min_coord
    return reducer
