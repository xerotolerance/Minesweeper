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
    def get_adjacent(row, col):
        return {(r, c) for r in range(row - 1, row + 2) for c in range(col - 1, col + 2) if
                -1 < r < len(board) and -1 < c < len(board[r]) and (r, c) != (row, col)}

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
                expandable = {pos for pos in get_adjacent(*zeros.pop()) if board[pos[0]][pos[1]] == '?'}
                for row, col in expandable:
                    board[row][col] = str(open(row, col))
                    if board[row][col] == '0':
                        zeros.add((row, col))
                    else:
                        frontier.add((row, col))

            print(f'Wave: {wave}')
            wave += 1
            for row in board:
                print(row)
            print()
        return frontier

    def gather_unknowns(row, col):
        unknown, confirmed = set(), set()
        for r, c in get_adjacent(row, col):
            if board[r][c] == '?':
                unknown.add((r, c))
            elif board[r][c] == 'x':
                confirmed.add((r, c))
        return unknown, confirmed

    def simple_analysis(frontier):
        while frontier:
            last_gen = frontier
            print(f'frontier: {frontier}')
            for _ in range(len(frontier)):
                row_num, col_num = frontier.pop()
                hint = int(board[row_num][col_num])
                unknowns, confirmed = gather_unknowns(row_num, col_num)
                if len(unknowns) + len(confirmed) == hint:
                    for _ in range(len(unknowns)):
                        r, c = unknowns.pop()
                        board[r][c] = 'x'
                        mines_found[0] += 1
                        confirmed.add((r, c))
                        for row in board:
                            print(row)
                        print()
                if len(confirmed) == hint:
                    for r, c in {pos for pos in get_adjacent(row_num, col_num) if board[pos[0]][pos[1]] == '?'}:
                        board[r][c] = str(open(r, c))
                        frontier.add((r, c))
                else:
                    frontier.add((row_num, col_num))

            if mines_found[0] == nmines:
                for r in range(len(board)):
                    for c in range(len(board[r])):
                        if board[r][c] == '?':
                            board[r][c] = open(r, c)
                break
            elif frontier == last_gen:
                return '?'
            print()
        return frontier

    mines_found = [0]
    board = [row.split(' ') for row in map.splitlines()]
    zeros = {(r, c) for r in range(len(board)) for c in range(len(board[r])) if board[r][c] == '0'}
    frontier = simple_analysis(unpack_zeros(zeros))
    for row in board:
        print(row)
    print()
    if mines_found[0] == nmines:
        return "\n".join((" ".join(row) for row in board))
    return '?'


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
    rows, columns = 10, 5
    nmines = rows*columns//5
    board, key = gen_board(rows, columns)
    print(solve_mine(board, nmines))

