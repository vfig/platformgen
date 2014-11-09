__all__ = ('ColorGenerator', 'random_color')

import random

def random_color():
    import colorsys
    h = random.random()
    s = 0.5 + random.random() * 0.5
    v = 0.25 + random.random() * 0.75
    (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    return '#%02x%02x%02x' % (r, g, b)

class ColorGenerator(object):
    def __init__(self):
        self.existing_colors = set()

    def __iter__(self):
        return self

    def next(self):
        if len(self.existing_colors) >= 1000000:
            raise StopIteration
        color = random_color()
        while color in self.existing_colors:
            color = random_color()
        self.existing_colors.add(color)
        return color
