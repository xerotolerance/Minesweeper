#  Copyright (c) 2020. Christopher J Maxwell <contact@christopherjmaxwell.com>

from os import name, system
from random import shuffle
from time import sleep
from typing import List

key = None


def clearscreen(enabled=False):
    if enabled:
        system('cls' if name == 'nt' else 'clear')
        sleep(.01)


def open(row: int, column: int) -> int:
    _key: List[List[str]] = [[c for c in _row.split()] for _row in key.splitlines()]
    res: str = _key[row][column]
    assert res != 'x'
    return int(res)


def gen_board(rows: int, columns: int, nmines: int = None):
    def update_left_right(r, c):
        # Update Left
        if c and board[r][c - 1] != 'x':
            board[r][c - 1] += 1

        # Update Right
        if c < columns - 1 and board[r][c + 1] != 'x':
            board[r][c + 1] += 1

    def make_string(hidden=False):
        return "\n".join((' '.join(('?' if hidden and c != 0 else str(c) for c in row)) for row in board)) + "\n"

    if nmines is None:
        nmines = int((rows * columns) * (1 / 5))
    assert nmines < rows * columns

    board, key = "", ""
    # only return a board with at least one '0' in it
    while '0' not in key:
        board = [0 for _ in range(rows * columns)]  # create empty board in 1 dimension
        board[:nmines] = ['x' for _ in range(nmines)]  # populate the first few spaces with mines
        shuffle(board)  # mix up the board
        board = [board[n * columns: (n + 1) * columns] for n in range(rows)]  # translate board into 2 dimensions
        mine_spots = [(r, c) for r in range(rows) for c in range(columns) if board[r][c] == 'x']  # find the mines

        # For each mine:
        for _ in range(len(mine_spots)):
            row_num, col_num = mine_spots.pop()
            # Update counts in squares left & right of mine
            update_left_right(row_num, col_num)

            # Update squares in row above
            if row_num:
                if board[row_num - 1][col_num] != 'x':
                    board[row_num - 1][col_num] += 1
                update_left_right(row_num - 1, col_num)

            # Update squares in row below
            if row_num < rows - 1:
                if board[row_num + 1][col_num] != 'x':
                    board[row_num + 1][col_num] += 1
                update_left_right(row_num + 1, col_num)
        board, key = make_string(hidden=True), make_string()
    return board, key


if __name__ == '__main__':
    board, key = gen_board(10, 10)
    print(f'board:\n{board}\n\nkey:\n{key}')
