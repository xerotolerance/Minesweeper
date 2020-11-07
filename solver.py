from typing import Union, List

from gamebuilder import gen_board


def open(row: int, column: int) -> Union[bool, int]:
    assert 'board' in globals()
    _key: List[List[str]] = [[c for c in _row.split()] for _row in key.splitlines()]
    res: str = _key[row][column]
    assert res != 'x'
    return int(res)


def solve_mine(map, n):
    # coding and coding...
    def unpack_zeros(zeros):
        wave = 0
        print(f'Wave: {wave}')
        wave += 1
        for row in board:
            print(row)
        print()
        frontier = set()
        while zeros:
            for _ in range(len(zeros)):
                row, col = zeros.pop()
                for row_offset in range(-1, 2):
                    target_row = row + row_offset
                    if -1 < target_row < len(board):
                        for col_offset in range(-1, 2):
                            target_col = col + col_offset
                            if -1 < target_col < len(board[row + row_offset]) and board[target_row][target_col] == '?':
                                board[target_row][target_col] = str(open(target_row, target_col))
                                if board[target_row][target_col] == '0':
                                    zeros.add((target_row, target_col))
                                else:
                                    frontier.add((target_row, target_col))
            print(f'Wave: {wave}')
            wave += 1
            for row in board:
                print(row)
            print()
        return frontier

    def gather_unknowns(row, col):
        unknowns = set()
        for roff in range(row-1, row+2):
            if -1 < roff < len(board):
                for coff in range(col-1, col+2):
                    if -1 < coff < len(board[roff]) and board[roff][coff] == '?':
                        unknowns.add((roff, coff))
        return unknowns

    board = [row.split(' ') for row in map.splitlines()]
    zeros = {(r, c) for r in range(len(board)) for c in range(len(board[r])) if board[r][c] == '0'}
    frontier = unpack_zeros(zeros)
    print(f'frontier: {frontier}')
    for row, col in frontier:
        unknowns = gather_unknowns(row, col)
        """if len(unknowns) <= int(board[row][col]):
            for _ in range(len(unknowns)):
                r, c = unknowns.pop()
                board[r][c] = 'x'"""
    for row in board:
        print(row)
    print()
    print()



def test_open():
    print(board)
    try:
        while True:
            s = input('Enter row, col [ Press Enter to exit ]: ')
            if not s:
                break
            try:
                row, col = [int(num.strip()) for num in s.split(',')]
            except ValueError:
                print(f'> invalid input "{s}".')
                continue
            print(open(row, col))
    except EOFError:
        print('\n', key)


if __name__ == '__main__':
    nmines = 5*5//5
    board, key = gen_board(5, 5, nmines)
    solve_mine(board, nmines)

