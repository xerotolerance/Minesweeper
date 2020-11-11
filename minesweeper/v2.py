#  Copyright (c) 2020. Christopher J Maxwell <contact@christopherjmaxwell.com>

from typing import Dict, FrozenSet, List, Optional, Tuple

import minesweeper
from minesweeper import clearscreen, open


class Gridspace:
    """Represents a space on the board which is aware of its neighbors & the # of mines around it."""

    def __init__(self, r: int, c: int, hint: str, nrows: int, ncols: int):
        self.row = r
        self.col = c
        self.hint = hint
        self.ties = set()
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
        self.num_undiscovered = -1
        self.zones = {}

    @property
    def position(self) -> Tuple:
        """
        Get the grid position of this space.

        :return: The row & column of this space.
        """
        return self.row, self.col

    def __str__(self):
        return f'({self.row},{self.col}): {self.hint}: {self.num_undiscovered}'

    def __repr__(self):
        return f'Position: ({self.row},{self.col})' \
               f'Hint: {self.hint}' \
               f'# Undiscovered mines in vicinity: {self.num_undiscovered}'


def boardtohashmap(board_2d: List[List[str]]) -> Dict[Tuple[int, int], Gridspace]:
    """
    Creates a dictionary that represent the evolving gameboard during play.

    :param board_2d: a list of lists representing the 2d-board
    :return: a dictionary that represent the evolving gameboard during play.
    """

    nrows, ncols = len(board_2d), len(board_2d[0])
    return {
        (r, c): Gridspace(r, c, board_2d[r][c], nrows, len(board_2d[r]))
        for r in range(nrows) for c in range(len(board_2d[r]))
    }


def hashmaptostring(hashmap: Dict[Tuple[int, int], Gridspace], nrows: int, ncols: int) -> str:
    """
    Get a string representation of the 2d-board state during play.

    :param hashmap: a dictionary representing the 2d-board during play
    :param nrows: # of rows in the 2d-board
    :param ncols: # of columns in the 2d-board
    :return: a string representation of the 2d-board state during play
    """

    return "\n".join(" ".join(hashmap[(r, c)].hint for c in range(ncols)) for r in range(nrows))


def splitgrid(gridstr: str) -> List[List[str]]:
    """
    Splits a string representation of a 2d-board into a 2d-list. (splits on whitespace & newlines)

    :param gridstr: a string representation of a 2d-board
    :return: a 2d-list representing a 2d-board
    """

    return [row.split() for row in gridstr.splitlines()]


def solve_mine(map: str, n: int) -> str:
    """
    Plays a game of Minesweeper as far as possible without making a guess. (Kata mandated entry point for program.)

    :param map: a string representation of the 2d-board
    :param n: # of mines on the gameboard
    :return: a string representation of the solved 2d-board or a single '?' if board is unsolvable.
    """

    def get_frontier() -> Dict[Tuple[int, int], Gridspace]:
        """
        Get '?'-adjacent hint spaces

        :return: a dictionary of coordinates pairs & Gridspace objects identifying spaces w/ a neighboring '?'
        """

        return {pos: space for pos, space in lookup.items() if space.hint.isnumeric() and any(
            lookup[neighbor].hint == '?' for neighbor in space.neighbors.values() if neighbor)}

    def get_exclusion_zones(frontier: Dict[Tuple[int, int], Gridspace]) -> Dict[
        FrozenSet[Optional[Tuple[int, int]]], int]:
        """
        Group the frontier-adjacent '?' spaces into pairs of "zone, frequency", where 'zone' is a group of spaces & 'frequency' is the # of mines hiding in zone.

        :param frontier: a dictionary representing the squares immediately surrounded by '?'s
        :return: a dictionary of zones & the # of mines within those zones
        """

        exclusion_zones = {}
        for pos, space in frontier.items():
            nunkown = int(space.hint) - sum(
                1 for neighbor in space.neighbors.values() if neighbor and lookup[neighbor].hint == 'x')
            exclusion_zones.update(
                {frozenset(neighbor for neighbor in space.neighbors.values() if
                           neighbor and lookup[neighbor].hint == '?'): nunkown})
        return exclusion_zones

    def group_by_coord(exclusion_zones: Dict[FrozenSet[Optional[Tuple[int, int]]], int]):
        """
        Get a nested dictionary tracking which squares are in which zones.

        :param exclusion_zones: a dictionary of zones & the # of mines within those zones
        :return: Nested dictionary as such, {(row, col): {frequency: {zone0, zone1, ...}}}
        """
        by_coord = {}
        for zone in exclusion_zones:
            freq = exclusion_zones[zone]
            for spot in zone:
                by_coord[spot] = by_coord.setdefault(spot, dict())
                by_coord[spot][freq] = by_coord[spot].setdefault(freq, set())
                by_coord[spot][freq].add(zone)
        return by_coord

    def update_zones(exclusion_zones: Dict[FrozenSet[Optional[Tuple[int, int]]], int]) -> Tuple[bool, bool]:
        """
        Deduces additional exclusion zones from visible hints & known zones. (May also find & mark mines).

        :param exclusion_zones: a dictionary of zones & the # of mines within those zones
        :return: Whether any additional zones were discovered + whether any mines were discovered. (Side-effect: updates solve_mine.lookup)
        """

        if len(exclusion_zones) == 3:
            print(end='')

        by_coord = group_by_coord(exclusion_zones)
        mine_found, zone_added = False, False

        for coord, zones_by_frequency in by_coord.items():
            for freq, zones in zones_by_frequency.items():
                for other_freq, other_zones in zones_by_frequency.items():
                    for zone in zones:
                        for other_zone in other_zones:
                            if freq == other_freq:
                                new_zone = zone ^ other_zone
                                if new_zone and new_zone not in exclusion_zones:
                                    exclusion_zones[new_zone] = 1
                                    zone_added = True
                            else:
                                new_zone = zone - other_zone if freq > other_freq else other_zone - zone
                                if len(new_zone) > 1:
                                    exclusion_zones[new_zone] = abs(freq - other_freq)
                                else:
                                    lookup[set(new_zone).pop()].hint = 'x'
                                    mine_found = True
                                    if display:
                                        clearscreen()
                                        print(hashmaptostring(lookup, nrows, ncols))
                                        print()
                                    return mine_found, mine_found
        return zone_added, mine_found

    def find_by_exclusion_zone(exclusion_zones: Dict[FrozenSet[Optional[Tuple[int, int]]], int],
                               display: bool = False) -> bool:
        """
        Find & open safe-spaces by comparing zones of mutual exclusivity based off exposed hints.

        :param exclusion_zones: a dictionary of zones & the # of mines within those zones
        :param display: Prints board state after execution if True
        :return: True if board state was altered. (Updates param exclusion_zones & solve_mine.lookup by side-effect)
        """

        opened = set()
        updated = False
        # Check for zones which are entirely within a different, larger zone
        for zone, level in sorted(list(exclusion_zones.items()), key=lambda pair: len(pair[0]), reverse=False):
            for other, other_level in sorted(list(exclusion_zones.items()), key=lambda pair: len(pair[0]),
                                             reverse=True):
                if len(zone) > len(other):
                    # Only perform check when zone is small enough
                    #  to fit inside other
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
                            if lookup[pos].hint == '?':
                                lookup[pos].hint = f'{open(*pos)}'
                                opened.add(pos)
                                updated = True
                                if display:
                                    clearscreen()
                                    print(hashmaptostring(lookup, nrows, ncols))
                                    print()

        for zone, freq in list(exclusion_zones.items()):
            new_zone = zone - opened
            exclusion_zones.pop(zone)
            if new_zone:
                exclusion_zones[new_zone] = freq

        if display:
            clearscreen()
            print(hashmaptostring(lookup, nrows, ncols))
            print()
        return updated

    def open_zeros(display: bool = False) -> None:
        """
        Unveil hints of squares neighboring a square with no surrounding mines.

        :param display: Prints board state after execution if True
        :return: None
        """

        if display:
            print(hashmaptostring(lookup, nrows, ncols), '\n')
        for pos, space in lookup.items():
            if space.hint == '0':
                for neighbor in space.neighbors.values():
                    if neighbor and lookup[neighbor].hint == '?':
                        lookup[neighbor].hint = f"{open(*neighbor)}"
        if display:
            clearscreen()
            print(hashmaptostring(lookup, nrows, ncols))
            print()

    def mark_spaces(display: bool = False) -> int:
        """
        Deduce which squares are holding mines based off visible hints & mark them w/ an 'x'.

        :param display: Prints board state after execution if True
        :return: # of mines found during this invocation
        """

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
            clearscreen()
            print(hashmaptostring(lookup, nrows, ncols))
            print()
        return nfound

    def open_safe_spaces(display: bool = False) -> bool:
        """
        Deduce which squares ARE NOT holding mines based off visible hints & 'open' them.

        :param display: Prints board state after execution if True
        :return: True if board state was altered during this invocation
        """

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
            clearscreen()
            print(hashmaptostring(lookup, nrows, ncols))
            print()
        return space_unpacked

    def find_safe_spaces(display: bool = False) -> Tuple[bool, int]:
        """
        Use set operations to further deduce which squares ARE NOT holding mines based off visible hints & 'open' them.

        :param display: Prints board state after execution if True
        :return: True if board state was altered + the # of mines marked during this invocation
        """

        zone_found = True
        mine_found = False
        updated = False

        frontier = get_frontier()
        exclusion_zones = get_exclusion_zones(frontier)

        """while not updated:
            updated |= find_by_exclusion_zone(exclusion_zones, display)
            if not updated:
                updated, mine_found = update_zones(exclusion_zones)
                if not updated:
                    break"""
        while zone_found:
            updated |= find_by_exclusion_zone(exclusion_zones, display)
            if len(exclusion_zones) == 3:
                print(end='')
            old_zones = exclusion_zones
            zone_found, mine_found = update_zones(exclusion_zones)
            if old_zones == exclusion_zones:
                print(end='')
            updated |= mine_found
        return updated, mine_found

    board_2d = splitgrid(map)
    nrows, ncols = len(board_2d), len(board_2d[0])
    lookup = boardtohashmap(board_2d)
    nfound = 0
    display = True

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
            if nfound == 82:
                print(end='')
            space_updated, mine_found = find_safe_spaces(display)
            nfound += mine_found
            if space_updated:
                continue

            if display:
                clearscreen()
                print(hashmaptostring(lookup, nrows, ncols))
                print()
            return '?'

    # All mines found; Open all remaining '?'s
    for pos, space in lookup.items():
        if space.hint == '?':
            space.hint = f'{open(*pos)}'

    if display:
        clearscreen()
        print(hashmaptostring(lookup, nrows, ncols))
        print()
    return hashmaptostring(lookup, nrows, ncols)


def main():
    '''nrows = 10
    ncols = 10
    nmines = nrows * ncols // 5
    board, minesweeper.key = gen_board(nrows, ncols, nmines)'''

    # FAILED
    minesweeper.key = """1 x 1 0 1 1 1 0 1 x 2 x 1 0 0 0 1 x 1 0 0 0 0 0 0 1 1 1 0 0
1 1 1 0 1 x 2 2 3 2 2 1 1 0 0 0 1 1 2 1 1 0 0 0 0 1 x 1 0 0
0 0 0 1 2 2 2 x x 2 1 1 0 0 0 0 0 0 1 x 1 0 0 0 0 1 2 2 1 0
1 1 1 1 x 1 1 2 2 2 x 1 1 1 1 0 0 0 1 1 1 0 0 0 0 0 2 x 2 0
2 x 1 1 1 1 1 1 1 1 1 1 1 x 2 1 0 0 0 1 1 1 0 0 0 0 2 x 2 0
x 2 1 0 0 0 1 x 1 0 0 0 2 3 x 1 0 0 0 1 x 1 0 0 0 0 1 1 1 0
1 1 0 0 0 0 2 2 2 0 0 0 1 x 2 1 0 0 0 1 1 1 0 0 0 1 1 1 0 0
0 0 0 0 0 0 1 x 1 0 0 0 2 2 2 0 1 1 1 0 0 0 1 1 1 1 x 1 0 0
0 0 0 0 1 1 2 1 1 0 0 0 1 x 1 0 1 x 1 1 1 2 2 x 1 1 1 1 0 0
0 0 0 0 1 x 1 0 0 0 0 0 1 1 1 0 2 2 2 2 x 3 x 2 1 0 0 0 1 1
0 0 0 0 1 1 1 0 0 0 0 1 1 1 0 0 1 x 1 2 x 4 2 2 0 1 1 1 1 x
0 1 1 1 0 0 0 0 0 0 0 1 x 1 0 0 1 2 2 2 1 2 x 1 0 1 x 1 1 1
0 1 x 2 1 2 1 1 0 0 0 1 1 1 0 0 0 1 x 1 0 1 2 2 1 1 1 1 0 0
0 1 1 2 x 2 x 3 2 1 0 1 2 2 1 0 0 1 2 2 1 0 1 x 1 0 0 0 0 0
1 1 0 1 1 2 2 x x 1 0 1 x x 1 0 0 0 1 x 1 0 1 2 2 1 0 0 0 0
x 1 0 0 0 0 2 3 3 1 0 1 2 2 1 0 0 0 1 1 1 0 0 2 x 2 0 0 0 0
1 1 0 0 0 0 1 x 1 0 0 0 0 1 1 1 0 0 0 0 0 0 0 2 x 3 1 0 0 0
0 0 0 0 0 0 1 1 1 0 0 0 0 1 x 1 0 0 0 1 1 1 0 1 2 x 1 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 0 0 0 2 x 2 0 1 2 2 1 0 0 0
1 2 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 x 2 0 1 x 1 0 1 1 1
1 x x 1 1 1 1 0 1 1 1 0 0 1 1 2 1 1 0 1 1 1 1 2 2 1 0 1 x 1
1 2 3 2 2 x 1 0 1 x 2 1 0 1 x 3 x 2 0 0 0 0 1 x 1 0 0 1 1 1
0 0 1 x 3 2 2 0 1 2 x 1 1 2 2 3 x 3 1 0 0 0 1 1 1 0 0 0 0 0
0 0 1 1 2 x 1 0 0 1 1 2 2 x 2 2 2 x 2 1 1 0 0 0 0 0 0 0 0 0
0 0 0 0 1 1 1 0 0 0 0 1 x 4 x 1 1 1 2 x 1 1 1 1 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 1 1 2 2 x 2 1 0 0 1 1 1 1 x 2 1 1 0 0 0 0
0 0 0 0 0 1 1 2 1 2 x 1 1 1 1 0 0 1 2 2 1 1 1 2 x 2 1 1 1 1
0 0 0 0 0 1 x 4 x 4 2 1 0 0 0 0 0 2 x x 2 2 2 2 3 x 2 1 x 1
0 0 0 0 0 1 2 x x x 1 0 0 0 0 0 0 2 x 3 2 x x 1 2 x 2 1 1 1"""

    board = """? ? ? 0 ? ? ? 0 ? ? ? ? ? 0 0 0 ? ? ? 0 0 0 0 0 0 ? ? ? 0 0
? ? ? 0 ? ? ? ? ? ? ? ? ? 0 0 0 ? ? ? ? ? 0 0 0 0 ? ? ? 0 0
0 0 0 ? ? ? ? ? ? ? ? ? 0 0 0 0 0 0 ? ? ? 0 0 0 0 ? ? ? ? 0
? ? ? ? ? ? ? ? ? ? ? ? ? ? ? 0 0 0 ? ? ? 0 0 0 0 0 ? ? ? 0
? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? 0 0 0 ? ? ? 0 0 0 0 ? ? ? 0
? ? ? 0 0 0 ? ? ? 0 0 0 ? ? ? ? 0 0 0 ? ? ? 0 0 0 0 ? ? ? 0
? ? 0 0 0 0 ? ? ? 0 0 0 ? ? ? ? 0 0 0 ? ? ? 0 0 0 ? ? ? 0 0
0 0 0 0 0 0 ? ? ? 0 0 0 ? ? ? 0 ? ? ? 0 0 0 ? ? ? ? ? ? 0 0
0 0 0 0 ? ? ? ? ? 0 0 0 ? ? ? 0 ? ? ? ? ? ? ? ? ? ? ? ? 0 0
0 0 0 0 ? ? ? 0 0 0 0 0 ? ? ? 0 ? ? ? ? ? ? ? ? ? 0 0 0 ? ?
0 0 0 0 ? ? ? 0 0 0 0 ? ? ? 0 0 ? ? ? ? ? ? ? ? 0 ? ? ? ? ?
0 ? ? ? 0 0 0 0 0 0 0 ? ? ? 0 0 ? ? ? ? ? ? ? ? 0 ? ? ? ? ?
0 ? ? ? ? ? ? ? 0 0 0 ? ? ? 0 0 0 ? ? ? 0 ? ? ? ? ? ? ? 0 0
0 ? ? ? ? ? ? ? ? ? 0 ? ? ? ? 0 0 ? ? ? ? 0 ? ? ? 0 0 0 0 0
? ? 0 ? ? ? ? ? ? ? 0 ? ? ? ? 0 0 0 ? ? ? 0 ? ? ? ? 0 0 0 0
? ? 0 0 0 0 ? ? ? ? 0 ? ? ? ? 0 0 0 ? ? ? 0 0 ? ? ? 0 0 0 0
? ? 0 0 0 0 ? ? ? 0 0 0 0 ? ? ? 0 0 0 0 0 0 0 ? ? ? ? 0 0 0
0 0 0 0 0 0 ? ? ? 0 0 0 0 ? ? ? 0 0 0 ? ? ? 0 ? ? ? ? 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 ? ? ? 0 0 0 ? ? ? 0 ? ? ? ? 0 0 0
? ? ? ? 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 ? ? ? 0 ? ? ? 0 ? ? ?
? ? ? ? ? ? ? 0 ? ? ? 0 0 ? ? ? ? ? 0 ? ? ? ? ? ? ? 0 ? ? ?
? ? ? ? ? ? ? 0 ? ? ? ? 0 ? ? ? ? ? 0 0 0 0 ? ? ? 0 0 ? ? ?
0 0 ? ? ? ? ? 0 ? ? ? ? ? ? ? ? ? ? ? 0 0 0 ? ? ? 0 0 0 0 0
0 0 ? ? ? ? ? 0 0 ? ? ? ? ? ? ? ? ? ? ? ? 0 0 0 0 0 0 0 0 0
0 0 0 0 ? ? ? 0 0 0 0 ? ? ? ? ? ? ? ? ? ? ? ? ? 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 ? ? ? ? ? ? ? 0 0 ? ? ? ? ? ? ? ? 0 0 0 0
0 0 0 0 0 ? ? ? ? ? ? ? ? ? ? 0 0 ? ? ? ? ? ? ? ? ? ? ? ? ?
0 0 0 0 0 ? ? ? ? ? ? ? 0 0 0 0 0 ? ? ? ? ? ? ? ? ? ? ? ? ?
0 0 0 0 0 ? ? ? ? ? ? 0 0 0 0 0 0 ? ? ? ? ? ? ? ? ? ? ? ? ?"""
    ans = minesweeper.key

    nmines = minesweeper.key.count('x')
    res = solve_mine(board, nmines)
    print(res)
    assert ans == res


if __name__ == '__main__':
    main()
