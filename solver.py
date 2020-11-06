from typing import Union, List

from gamebuilder import gen_board


def open(row: int, column: int) -> Union[bool, int]:
    assert 'board' in globals()
    _key: List[List[str]] = [[c for c in _row.split()] for _row in key.splitlines()]
    res: str = _key[row][column]
    return int(res) if res != 'x' else False


def solve_mine(map, n):
    # coding and coding...
    board = [row.split(' ') for row in map.splitlines()]
    while True:
        for row in board:
            print(row)

        zeros = 0  # [(row, col) for row in range(len(board)) for col in range(len(board[row])) if board[row][col] == '0']
        if zeros:
            for _ in range(len(zeros)):
                row, col = zeros.pop()
                board[row][col] = open(row, col)
        else:
            break


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

