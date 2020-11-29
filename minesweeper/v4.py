#  Copyright (c) 2020. Christopher J Maxwell <contact@christopherjmaxwell.com>
from typing import Any, Dict, FrozenSet, Generator, List, Set, Tuple

import minesweeper
from minesweeper import open


def solve_mine(map: str, n: int) -> str:
    """
    Plays a game of Minesweeper until its logical end without guessing.

    :param map: The start state of the board
    :param n: The # of mines are hidden on the board
    :return: The solved board or a single '?' if solution could not be found.
    """

    def get_board_str() -> str:
        """
        Returns a string representation of the board state.

        :return: The current board state as a string.
        """

        return "\n".join(" ".join(row) for row in board)

    board = [line.split(' ') for line in map.splitlines()]
    nrows, ncols = len(board), len(board[0])
    unknowns = {(rnum, cnum) for rnum in range(nrows) for cnum in range(ncols) if board[rnum][cnum] == '?'}
    frontier = None
    result = '?'
    nmines_remaining = n
    num_unknown = -1
    heuristics = [basic_analysis, inclusive_deduction, exclusive_deduction, numerical_deduction]

    print("\nSolving board...")

    # Analysis Loop:
    #   - Loops until board is solved or until all heuristics have failed.
    idx = 0
    while idx < len(heuristics):
        if idx == 0:
            # Find hint squares with adjacent ?s
            frontier = {(rnum, cnum) for pos in unknowns for rnum, cnum in get_neighbors(*pos, board) if
                        board[rnum][cnum].isnumeric()}
            num_unknown = len(unknowns)
            print(get_board_str(), '\n')

        # Perform heuristic
        nmines_remaining = heuristics[idx](board, frontier, nmines_remaining, unknowns)

        # Check if board was altered
        if len(unknowns) < num_unknown:
            if not unknowns:
                # Solution was found
                result = get_board_str()
                break
            else:
                # Repeat evaluation from first heuristic
                idx = 0
        else:
            # Try the next heuristic
            idx += 1

    message = "No changes detected... giving up..." if result == '?' else "Solution Found!"
    print(get_board_str(), message, sep='\n')
    return result


# Utility Functions
def get_neighbors(rnum: int, cnum: int, board: List[List[str]]) -> Generator[Tuple[int, int], Any, None]:
    """
    Yields the co-ordinates of all squares surrounding the square @ (rnum, cnum).

    :param rnum: Row # of target square.
    :param cnum: Column # of target square.
    :param board: The current board state.
    :return: A generator that yields the positions of squares neighboring (rnum, cnum).
    """

    nrows, ncols = len(board), len(board[0])
    return (
        (rnum + roffset, cnum + coffset)
        for roffset in range(-1, 2) for coffset in range(-1, 2)
        if (roffset or coffset) and (-1 < rnum + roffset < nrows) and (-1 < cnum + coffset < ncols)
    )


def get_groups(board: List[List[str]], frontier: Set[Tuple[int, int]], unknowns: Set[Tuple[int, int]]) -> Dict[
    FrozenSet[Tuple[int, int]], int]:
    """
    Returns a dictionary of grouped ?s squares & the # of mines contained in each group.

    :param board: a 2d list representing the current board for a game of minesweeper.
    :param frontier: a set of co-ordinate pairs representing the outer-most ring of known hint squares.
    :param unknowns: a set containing co-ordinate pairs for all ?s on the board.
    :return: a dictionary that has Frozensets of frontier-adjacent ?s as keys & the # of mines per set as values
    """

    groups = {
        # key: A hashable set of ?s surrounding a given pos on the frontier
        # value: The # of mines hidden in that set
        frozenset(neighbor for neighbor in get_neighbors(*pos, board) if neighbor in unknowns)
        : count_remaining_mines(pos, board) for pos in frontier
    }
    return groups


def flag(*args, **kwargs) -> str:
    """
    Returns the string representation of a mine.

    :return: a single 'x'
    """
    return 'x'


def count_remaining_mines(pos: Tuple[int, int], board: List[List[str]]) -> int:
    """
    Returns the # of mines yet to be flagged around a given position on the board.

    :param pos: (x,y) co-ordinates of the spot on the board to examine. [(0,0) is top-leftmost]
    :param board: a 2d list representing the current board for a game of minesweeper
    :return: the # of mines still hidden around the specified space.
    """
    return int(board[pos[0]][pos[1]]) - sum(1 for npos in get_neighbors(*pos, board) if board[npos[0]][npos[1]] == 'x')


# Heuristic Functions
def basic_analysis(board: List[List[str]], frontier: Set[Tuple[int, int]], nmines_remaining: int,
                   unknowns: Set[Tuple[int, int]]) -> int:
    """
    Deduces & opens safe spaces, flags suspected mines using the exposed hint squares on the board.

    :param board: a 2d list representing the current board for a game of minesweeper.
    :param frontier: a set of co-ordinate pairs representing the outer-most ring of known hint squares.
    :param nmines_remaining: # of mines still hidden on the board.
    :param unknowns: a set containing co-ordinate pairs for all ?s on the board.
    :return: The # of mines still hidden after execution.
    """

    print("Basic analysis:")
    # For each square on the frontier,
    for rnum, cnum in frontier:
        hint = int(board[rnum][cnum])
        local_unknowns, local_mines = set(), set()

        # Group neighboring squares into sets of local_mines & local_unknowns
        for pos in get_neighbors(rnum, cnum, board):
            if board[pos[0]][pos[1]] == 'x':
                local_mines.add(pos)
            elif board[pos[0]][pos[1]] == '?':
                local_unknowns.add(pos)

        # If all mines around this square have been found
        #   then open all neighboring unknown squares.
        if hint <= len(local_mines):
            for pos in local_unknowns:
                if pos in unknowns:
                    unknowns.remove(pos)
                    board[pos[0]][pos[1]] = str(open(*pos))

        # If the number of remaining mines around this square
        #   equals the number of unknowns around this square
        #   then flag those unknowns as mines.
        elif hint == len(local_mines) + len(local_unknowns):
            for pos in local_unknowns:
                if pos in unknowns:
                    unknowns.remove(pos)
                    board[pos[0]][pos[1]] = str(flag(*pos))
                    nmines_remaining -= 1
    return nmines_remaining


def inclusive_deduction(board: List[List[str]], frontier: Set[Tuple[int, int]], nmines_remaining: int,
                        unknowns: Set[Tuple[int, int]]) -> int:
    """
    Deduces & opens safe spaces, flags suspected mines using set deductions on supersets of eclipsed subsets.

    :param board: a 2d list representing the current board for a game of minesweeper.
    :param frontier: a set of co-ordinate pairs representing the outer-most ring of known hint squares.
    :param nmines_remaining: # of mines still hidden on the board.
    :param unknowns: a set containing co-ordinate pairs for all ?s on the board.
    :return: The # of mines still hidden after execution.
    """

    print("No changes detected... attempting Advanced Analysis: Inclusive Deduction...\n")
    print("Advanced analysis - inclusive deduction:")
    groups = get_groups(board, frontier, unknowns)

    new_groups = {}  # newly derived groups & the # of mines in them
    parents = {}  # source groups for the derived groups & the sets of their children

    # Note: As it is not possible to add/remove element pairs to/from the parents dictionary during iteration,
    new_children = {}  # new_children is used to hold intended updates and is merged w/ parents after iteration.

    # Find the groups which exist entirely inside larger groups
    for group, nmines in groups.items():
        for other, other_nmines in groups.items():
            if group < other:
                # Break the larger group into its components:
                # (1. Elements shared between both groups
                # & 2. Elements unique to the larger group)
                same = group & other
                other_remaining = other - group

                # Save the component groups & the # of mines in them
                #   (Note same == group therefore the # of mines in same == # mines in group)
                new_groups[same] = nmines
                new_groups[other_remaining] = other_nmines - nmines

                # Track the sources of the component groups
                parents[other] = parents.setdefault(other, set())
                parents[other].add(same)
                parents[other].add(other_remaining)

    for parent, children in parents.items():
        for child in children:
            for other_child in children:
                if child.isdisjoint(other_child):
                    # Make new child sets from the parent
                    # by excluding elements which belong to
                    # DISJOINT existing children.
                    new_child = parent - child - other_child
                    if new_child:
                        # Treat the new child as a "component group" & save it as such
                        new_groups[new_child] = groups[parent] - new_groups[child] - new_groups[other_child]

                        """# Track the source of this new "component group" in a temporary collection
                        # (we will merge this collection with "parents" when iteration is complete)
                        new_children[parent] = new_children.setdefault(parent, set())
                        new_children[parent].add(new_child)

    # Merge temporary collection with "parents"
    for _ in range(len(new_children)):
        parent, children = new_children.popitem()
        parents[parent] |= children"""

    # Update the board with the results of analysis
    for group, nmines in new_groups.items():
        # if a group is found to contain only mines
        #   mark every spot in that group as a mine.
        if len(group) == nmines:
            for pos in group:
                if pos in unknowns:
                    unknowns.remove(pos)
                    board[pos[0]][pos[1]] = str(flag(*pos))
                    nmines_remaining -= 1

        # if a group is found not to contain any mines
        #   open every spot in that group.
        elif not nmines:
            for pos in group:
                if pos in unknowns:
                    unknowns.remove(pos)
                    board[pos[0]][pos[1]] = str(open(*pos))
    return nmines_remaining


def exclusive_deduction(board: List[List[str]], frontier: Set[Tuple[int, int]], nmines_remaining: int,
                        unknowns: Set[Tuple[int, int]]) -> int:
    """
    Identifies & flags the next mine using set deductions on overlapping (but not eclipsing) sets.

    :param board: a 2d list representing the current board for a game of minesweeper.
    :param frontier: a set of co-ordinate pairs representing the outer-most ring of known hint squares.
    :param nmines_remaining: # of mines still hidden on the board.
    :param unknowns: a set containing co-ordinate pairs for all ?s on the board.
    :return: The # of mines still hidden after execution.
    """

    print("No changes detected... attempting Advanced Analysis - Exclusive Deduction...\n")
    print("Advanced analysis - exclusive deduction:")
    groups = get_groups(board, frontier, unknowns)

    # Find the groups which exist entirely inside larger groups
    for group, nmines in groups.items():
        for other, other_nmines in groups.items():
            same = group & other
            if same and group != other:
                group_remaining = group - same
                other_remaining = other - same

                # Find the min # of mines that must exist
                #  in the overlap of group & other
                min_allowed_in_same = max(nmines - len(group_remaining), other_nmines - len(other_remaining), 0)

                if min_allowed_in_same:
                    if nmines - min_allowed_in_same == len(group_remaining):
                        target = group_remaining
                    elif other_nmines - min_allowed_in_same == len(other_remaining):
                        target = other_remaining
                    else:
                        continue

                    for pos in target:
                        if pos in unknowns:
                            unknowns.remove(pos)
                            board[pos[0]][pos[1]] = str(flag(*pos))
                            nmines_remaining -= 1
                    return nmines_remaining
    return nmines_remaining


def numerical_deduction(board: List[List[str]], frontier: Set[Tuple[int, int]], nmines_remaining: int,
                        unknowns: Set[Tuple[int, int]]) -> int:
    # TODO: implement Advanced Analysis based of counting # of mines remaining vs # of unknowns
    print("No changes detected... attempting Advanced Analysis - Numerical Deduction...\n")
    print("Advanced analysis - numerical deduction:")

    print(nmines_remaining)
    return nmines_remaining


if __name__ == '__main__':
    board = """0 0 0 ? ? ? ? ? ? 0 0 0 0 0 ? ? ? 0 0 ? ? ? ? ? ? ? ?
? ? 0 ? ? ? ? ? ? 0 0 0 0 0 ? ? ? ? ? ? ? ? ? ? ? ? ?
? ? ? ? 0 0 0 0 0 0 ? ? ? 0 ? ? ? ? ? ? 0 ? ? ? ? ? ?
? ? ? ? 0 0 0 0 0 0 ? ? ? 0 0 0 0 ? ? ? 0 ? ? ? ? ? ?
0 ? ? ? 0 0 0 0 0 0 ? ? ? 0 0 0 0 0 0 0 0 ? ? ? ? ? ?
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 ? ? ? ? 0"""

    minesweeper.key = """0 0 0 1 x 1 1 x 1 0 0 0 0 0 1 1 1 0 0 1 x 3 x 3 1 2 1
1 1 0 1 1 1 1 1 1 0 0 0 0 0 1 x 1 1 1 2 1 3 x 3 x 2 x
x 2 1 1 0 0 0 0 0 0 1 1 1 0 1 1 1 1 x 1 0 2 2 3 1 3 2
1 2 x 1 0 0 0 0 0 0 1 x 1 0 0 0 0 1 1 1 0 1 x 2 1 2 x
0 1 1 1 0 0 0 0 0 0 1 1 1 0 0 0 0 0 0 0 0 1 2 3 x 2 1
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 x 2 1 0"""
    print("Solving board...\n", board, '\n', sep='')
    res = solve_mine(board, minesweeper.key.count('x'))
    print(res)
