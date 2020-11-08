from typing import *

from gamebuilder import *


def open(row: int, column: int) -> Union[bool, int]:
    assert 'board' in globals()
    _key: List[List[str]] = [[c for c in _row.split()] for _row in key.splitlines()]
    res: str = _key[row][column]
    assert res != 'x'
    return int(res)


class Gridspace:
    def __init__(self, r, c, hint, nrows, ncols):
        self.row = r
        self.col = c
        self.hint = hint
        self.neighbors = {
            'up': (r - 1, c) if r - 1 > -1 else None,
            'left': (r, c - 1) if c - 1 > -1 else None,
            'down': (r + 1, c) if r + 1 < nrows else None,
            'right': (r, c + 1) if c + 1 < ncols else None,
            'top_left': (r - 1, c - 1) if r - 1 > -1 and c - 1 > -1 else None,
            'bottom_left': (r + 1, c - 1) if r + 1 < nrows and c - 1 > -1 else None,
            'top_right': (r - 1, c + 1) if r - 1 > -1 and c + 1 < ncols else None,
            'bottom_right': (r + 1, c + 1) if r + 1 < nrows and c + 1 < ncols else None
        }

    def __repr__(self):
        return f'({self.row},{self.col}: {self.hint})'


def splitgrid(gridstr):
    return [row.split() for row in gridstr.splitlines()]


def hashmaptostring(hashmap, nrows, ncols):
    return "\n".join(" ".join(hashmap[(r, c)].hint for c in range(ncols)) for r in range(nrows)) + "\n"


def boardtohashmap(board_2d):
    return {
        (r, c): Gridspace(r, c, board_2d[r][c], len(board_2d), len(board_2d[r]))
        for r in range(len(board_2d)) for c in range(len(board_2d[r]))
    }


def solve_mine(map, n):

    def open_zeros(display=False):
        """Open Zeros"""
        print(hashmaptostring(lookup, len(board_2d), len(board_2d[0])))
        for pos, space in lookup.items():
            if space.hint == '0':
                for neighbor in space.neighbors.values():
                    if neighbor and lookup[neighbor].hint == '?':
                        lookup[neighbor].hint = f"{open(*neighbor)}"
        if display:
            print(hashmaptostring(lookup, len(board_2d), len(board_2d[0])))
            print()

    def mark_spaces(display=False):
        """Mark discernible mines"""
        nfound = 0
        for space in lookup.values():
            if space.hint.isnumeric():
                proximity = int(space.hint)
                if proximity > 0 and proximity == sum(
                        1 for neighbor in space.neighbors.values() if neighbor and lookup[neighbor].hint in 'x?'):
                    for neighbor in space.neighbors.values():
                        if neighbor and lookup[neighbor].hint == '?':
                            lookup[neighbor].hint = 'x'
                            nfound += 1
        if display and nfound:
            print(hashmaptostring(lookup, len(board_2d), len(board_2d[0])))
            print()
        return nfound

    def open_safe_spaces(display=False):
        """Open discernible safe spaces"""
        space_unpacked = False
        for space in lookup.values():
            if space.hint.isnumeric():
                proximity = int(space.hint)
                if proximity > 0 and proximity == sum(
                        1 for neighbor in space.neighbors.values() if neighbor and lookup[neighbor].hint == 'x'):
                    for neighbor in space.neighbors.values():
                        if neighbor and lookup[neighbor].hint == '?':
                            lookup[neighbor].hint = f"{open(*neighbor)}"
                            space_unpacked = True
        if display and space_unpacked:
            print(hashmaptostring(lookup, len(board_2d), len(board_2d[0])))
            print()
        return space_unpacked

    def find_safe_spaces(display=False):
        """Find & open additional safe spaces using set operations"""

        updated = False

        # Get '?'-adjacent hint spaces
        frontier = {pos: space for pos, space in lookup.items() if
                    space.hint.isnumeric() and any(lookup[n].hint == '?' for n in space.neighbors.values() if n)}

        # Group the frontier-adjacent '?' spaces into pairs of "zone, frequency"
        #   where 'zone' is a group of spaces & 'frequency' is the # of mines hiding in zone.
        exclusion_zones = {}
        for pos, space in frontier.items():
            nunkown = int(space.hint) - sum(1 for n in space.neighbors.values() if n and lookup[n].hint == 'x')
            exclusion_zones.update(
                {frozenset(n for n in space.neighbors.values() if n and lookup[n].hint == '?'): nunkown})

        # Check for zones which are entirely within a bigger zone
        for zone, level in sorted(list(exclusion_zones.items()), key=lambda pair: len(pair[0]), reverse=False):
            for other, other_level in sorted(list(exclusion_zones.items()), key=lambda pair: len(pair[0]),
                                             reverse=True):
                if len(zone) > len(other):
                    # other can't contain zone if zone has more items
                    break
                elif zone < other:  # set operation: 'Proper-subset' (aka. "zone.issubset(other) and zone != other")
                    exclusion_zones.pop(other)  # Pull out larger group for modification
                    new_zone = frozenset(other - zone)  # Remove smaller group from larger group

                    if other_level - level > 0:
                        # Update # of mines in 'larger' group after removing smaller group;
                        #  Put back modified 'larger' group
                        exclusion_zones[new_zone] = other_level - level
                    else:
                        # OR,
                        #   If the # of mines in the modified group is 0,
                        #   we can safely open all spaces in that group, instead
                        for pos in new_zone:
                            lookup[pos].hint = f'{open(*pos)}'
                            updated = True
        if display and updated:
            print(hashmaptostring(lookup, len(board_2d), len(board_2d[0])))
            print()
        return updated

    board_2d = splitgrid(map)
    lookup = boardtohashmap(board_2d)
    nfound = 0
    display = False

    # Start by opening all spaces around those marked '0'
    open_zeros(display)

    while nfound < n:
        updated = False

        # Mark discernible mines
        nmarked = mark_spaces(display)
        updated |= nmarked
        nfound += nmarked

        # Open discernible safe spaces
        updated |= open_safe_spaces(display)

        if not updated:
            # Find & open additional safe spaces using set operations
            if find_safe_spaces(display):
                continue

            if display:
                print(hashmaptostring(lookup, len(board_2d), len(board_2d[0])))
                print()
            return '?'

    # All mines found; Open all remaining '?'s
    for pos, space in lookup.items():
        if space.hint == '?':
            space.hint = f'{open(*pos)}'

    if display:
        print(hashmaptostring(lookup, len(board_2d), len(board_2d[0])))
        print()
    return hashmaptostring(lookup, len(board_2d), len(board_2d[0]))


def main():
    global board, key
    nrows = 10
    ncols = 10
    nmines = nrows * ncols // 5
    board, key = gen_board(nrows, ncols, nmines)

    key = """1 x 1 1 x 1
2 2 2 1 2 2
2 x 2 0 1 x
2 x 2 1 2 2
1 1 1 1 x 1
0 0 0 1 1 1
"""

    board = """? ? ? ? ? ?
? ? ? ? ? ?
? ? ? 0 ? ?
? ? ? ? ? ?
? ? ? ? ? ?
0 0 0 ? ? ?
"""
    nmines = 6

    res = solve_mine(board, nmines)
    assert key == res


if __name__ == '__main__':
    board = None
    main()
