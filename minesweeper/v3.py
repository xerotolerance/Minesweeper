#  Copyright (c) 2020. Christopher J Maxwell <contact@christopherjmaxwell.com>

from typing import Dict, List, Tuple

import minesweeper
from minesweeper import open


class GameState:
    """Represents a single game of Minesweeper"""

    def __init__(self):
        self._lookup = None
        self._nrows = 0
        self._ncols = 0
        self._nmines = 0
        self._nfound = 0
        self._unknowns = None
        self._remaining_zones = None

    def _open(self, row: int, col: int) -> None:
        """
        Unveils the hint(s) of the square @ (row, col) & of any neighboring squares determined not to be mines.

        :param row: row # (starting @ 0) of square to be opened.
        :param col: column # (starting @ 0) of square to be opened.
        :return: None
        """

        this_space = self._lookup[(row, col)]

        # remove this space from unknowns
        if this_space.position in self._unknowns:
            self._unknowns.pop(this_space.position)

        # open this space
        n_hinted = open(row, col)
        this_space.hint = str(n_hinted)
        n_marked = sum(
            1 for neighbor in this_space.neighbors.values() if neighbor and self._lookup[neighbor].hint == 'x')
        this_space.num_undiscovered = n_hinted - n_marked

        # open safe neighbors
        if this_space.num_undiscovered == 0:
            safe_by_proxy = {neighbor for neighbor in this_space.neighbors.values() if
                             neighbor and self._lookup[neighbor].hint == '?'}
            for pos in safe_by_proxy:
                self._open(*pos)

        # remove this space from any zones it was in.
        for tie in this_space.ties:
            for zone in list(self._lookup[tie].zones):
                if this_space.position in zone:
                    new_zone = zone - {this_space.position}
                    freq = self._lookup[tie].zones.pop(zone)
                    if new_zone:
                        self._lookup[tie].zones[new_zone] = freq

    def _mark(self, row: int, col: int) -> None:
        """
        Marks the square @ (row, col) with an 'x' to represent the presences of a mine & decrements num_undiscovered of the neighboring squares.

        :param row: row # (starting @ 0) of square to be marked.
        :param col: column # (starting @ 0) of square to be marked.
        :return: None
        """

        this_space = self._lookup[(row, col)]

        # remove this space from unknowns
        if this_space.position in self._unknowns:
            self._unknowns.pop(this_space.position)

        # mark this space as a mine
        if this_space.hint == '?':
            this_space.hint = 'x'
            self._nfound += 1

        # alert neighbors
        for neighbor in this_space.neighbors.values():
            if neighbor and self._lookup[neighbor].num_undiscovered > 0:
                self._lookup[neighbor].num_undiscovered -= 1

        # remove this space from any zones it was in.
        for tie in this_space.ties:
            for zone in list(self._lookup[tie].zones):
                if this_space.position in zone:
                    new_zone = zone - {this_space.position}
                    freq = self._lookup[tie].zones.pop(zone)
                    if new_zone:
                        self._lookup[tie].zones[new_zone] = freq - 1 if freq > 0 else freq

    def _open_zeros(self, display: bool = False) -> None:
        """
        Unveil hints of squares neighboring a square with no surrounding mines.

        :param display: Prints board state after execution if True
        :return: None
        """

        if display:
            print('Before "Open Zeros":')
            print(repr(self), "\n")

        for pos, space in self._lookup.items():
            if space.hint == '0':
                for neighbor in space.neighbors.values():
                    if neighbor and self._lookup[neighbor].hint == '?':
                        self._open(*neighbor)
        if display:
            print('After "Open Zeros":')
            print(repr(self), "\n")

    def _mark_spaces(self, display: bool = False) -> int:
        """
        Deduce which squares are holding mines based off visible hints & mark them w/ an 'x'.

        :param display: Prints board state after execution if True
        :return: # of mines found during this invocation
        """

        nfound = 0
        for space in self._lookup.values():
            if space.hint.isnumeric():
                proximity = int(space.hint)
                if proximity > 0 and proximity == sum(
                        1 for neighbor in space.neighbors.values() if neighbor and self._lookup[neighbor].hint in 'x?'):
                    for neighbor in space.neighbors.values():
                        if neighbor and self._lookup[neighbor].hint == '?':
                            self._mark(*neighbor)
                            nfound += 1
        if display and nfound:
            print('After "Mark Spaces":')
            print(repr(self), "\n")
        return nfound

    def _open_safe_spaces(self, display: bool = False) -> bool:
        """
        Deduce which squares ARE NOT holding mines based off visible hints & 'open' them.

        :param display: Prints board state after execution if True
        :return: True if board state was altered during this invocation
        """

        space_unpacked = False
        for space in self._lookup.values():
            if space.hint.isnumeric():
                proximity = int(space.hint)
                if proximity > 0 and proximity == sum(
                        1 for neighbor in space.neighbors.values() if neighbor and self._lookup[neighbor].hint == 'x'):
                    for neighbor in space.neighbors.values():
                        if neighbor and self._lookup[neighbor].hint == '?':
                            self._open(*neighbor)
                            space_unpacked = True
        if display and space_unpacked:
            print('After "Open Safe Spaces":')
            print(repr(self), "\n")
        return space_unpacked

    def _make_ties(self) -> None:
        """
        Groups related '?'-squares into "zones" based off visible hints. Updates Gridspace.ties w/ set of related squares.

        :return: None
        """

        # get all hint spaces with adjacent '?'s
        frontier = {neighbor: self._lookup[neighbor] for pos, space in self._unknowns.items() for neighbor in
                    space.neighbors.values() if neighbor and self._lookup[neighbor].hint.isnumeric()}

        # use hints to create "zones" of '?'-squares along the frontier,
        #  detailing the # of mines left to find in each zone.
        for pos, space in frontier.items():
            local_unknowns = {coord for coord in space.neighbors.values() if coord in self._unknowns}
            for unknown in local_unknowns:
                key = frozenset(local_unknowns)
                self._lookup[unknown].zones[key] = self._lookup[unknown].zones.setdefault(key, space.num_undiscovered)
                self._lookup[unknown].zones[key] = min(space.num_undiscovered, self._lookup[unknown].zones[key])
                self._lookup[unknown].ties |= local_unknowns - {unknown}
                self._remaining_zones.update(self._lookup[unknown].zones)

        # split overlapping zones into components
        for unknown in self._unknowns.values():
            for zone, num_undiscovered in list(unknown.zones.items()):
                if zone not in unknown.zones:
                    continue
                for other_zone, other_num_undiscovered in list(unknown.zones.items()):
                    if other_zone in unknown.zones:
                        shared = zone & other_zone

                        if zone < other_zone or (shared and other_num_undiscovered > num_undiscovered):
                            # if "zone" & "other_zone" share members then
                            #  it is possible to split the zone w/ the higher # of mines
                            #   into components, "shared" & "not_shared".

                            # unknown.zones.pop(other_zone)

                            not_shared = other_zone - shared
                            unknown.zones[not_shared] = other_num_undiscovered - num_undiscovered
                        else:
                            print(end='')
        return

    """def _expand_ties(self):
        subzones = {}
        unknowns = {unknown: space for unknown, space in self._unknowns.items() if any(
            neighbor and neighbor not in self._unknowns for neighbor in space.neighbors.values())}
        while True:
            new_additions = {}
            for unknown, space in unknowns.items():
                outer = sorted(space.zones.items(), key=lambda pair: len(pair[0]))
                for zone, freq in outer:
                    inner = sorted(space.zones.items(), key=lambda pair: len(pair[0]), reverse=True)
                    for other_zone, other_freq in inner:
                        if zone != other_zone:
                            shared = zone & other_zone
                            other_exclusive = other_zone - shared
                            zone_exclusive = zone - shared
                            if zone < other_zone:
                                new_freq = other_freq - freq
                                if other_exclusive and other_exclusive not in new_additions and other_exclusive not in subzones:
                                    new_additions[other_exclusive] = new_freq
                            else:
                                shared_constraint = min(len(shared), freq, other_freq)  # max num mines in shared
                                if freq - shared_constraint == 1:
                                    if zone_exclusive and zone_exclusive not in new_additions and zone_exclusive not in subzones:
                                        new_additions[zone_exclusive] = 1
                                elif other_freq - shared_constraint == 1:
                                    if other_exclusive and other_exclusive not in new_additions and other_exclusive not in subzones:
                                        new_additions[other_exclusive] = 1

            if new_additions:
                subzones.update(new_additions)
                print(end='')
                for _ in range(len(new_additions)):
                    zone, freq = new_additions.popitem()
                    for pos in zone:
                        self._lookup[pos].zones[zone] = freq
            else:
                break
        return
"""
    def get_solution(self, display=False) -> str:
        """
        Plays a game of Minesweeper until its logical conclusion without making a guess.

        :param display: Prints board state during execution if True
        :return: The solved board as a string or a single '?'
        """

        if display:
            print()

        # Start the game
        self._open_zeros(display)

        # Find all mines or enter the fail state
        while self._nfound < self._nmines:
            self._mark_spaces(display)
            board_altered = self._open_safe_spaces(display)
            if not board_altered and len(self._unknowns):
                # Create exclusion zones
                self._make_ties()

                # self._expand_ties()

                # Find safe spaces
                safe_spaces = {pos: zone for unknown in self._unknowns.values() for zone, num_undiscovered in
                               unknown.zones.items() for pos in zone if num_undiscovered == 0}

                # Open safe spaces
                for pos, zone in safe_spaces.items():
                    self._open(*pos)
                if display and safe_spaces:
                    print('After "Logical Analysis - Safe Spaces":')
                    print(repr(self), "\n")

                # Find mines
                mines = {pos: zone for unknown in self._unknowns.values() for zone, num_undiscovered in
                         unknown.zones.items() for pos in zone if num_undiscovered == len(zone)}

                # Mark mines
                for pos, zone in mines.items():
                    self._mark(*pos)
                if display and mines:
                    print('After "Logical Analysis - Mines":')
                    print(repr(self), "\n")

                """remaining_zones = {pos: zone for unknown in self._unknowns.values() for zone, num_undiscovered in 
                                   unknown.zones.items() for pos in zone}"""

                # Enter fail state if no changes were made to the board
                if not safe_spaces and not mines:
                    if display:
                        print("> Unable to solve any further without guessing...\n")
                    return '?'

        # Open remaining '?'s
        for pos in list(self._unknowns):
            self._open(*pos)

        if display:
            print(f'Game completed. Finished board:\n{repr(self)}')
        return str(self).strip()

    @property
    def nremaining(self) -> int:
        """
        Returns the # of unmarked mines remaining on the board.

        :return: the # of mines left
        """
        return self._nmines - self._nfound

    @classmethod
    def fromboardstr(cls, board_str: str, nmines: int):
        """
        Creates a GameState object from a given string representing a rectangular grid & the # of mines hidden on in that grid.

        :param board_str: A rectangular grid of '?'s & 0's separated by spaces & newlines.
        :param nmines: # of mines that are hidden behind '?'s on the board.
        :return: A GameState object that can be used to get the solution of the provided board. (If possible)
        """

        state = GameState()
        board_2d = splitgrid(board_str)
        state._nrows = len(board_2d)
        state._ncols = len(board_2d[0])
        state._nmines = nmines
        state._lookup = boardtohashmap(board_2d)
        state._unknowns = {pos: space for pos, space in state._lookup.items() if space.hint == '?'}
        state._remaining_zones = {}
        return state

    def __str__(self):
        return hashmaptostring(self._lookup, self._nrows, self._ncols)

    def __repr__(self):
        return f'{self}\n({self.nremaining} mine(s) left. {len(self._unknowns)} space(s) left to explore.)'


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
        self.subzones = {}


    @property
    def position(self) -> Tuple[int, int]:
        """
        Get the grid position of this space.

        :return: The row & column of this space.
        """
        return self.row, self.col

    def __str__(self):
        return f'({self.row},{self.col}): {self.hint}: {self.num_undiscovered}'

    def __repr__(self):
        return f'{{Position: ({self.row},{self.col}) | ' \
               f'Hint: {self.hint} | ' \
               f'# Undiscovered mines in vicinity: {self.num_undiscovered}}}'


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
    this_game = GameState.fromboardstr(map, n)
    return this_game.get_solution(True)


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
    print(ans == res)
    assert ans == res


if __name__ == '__main__':
    main()
