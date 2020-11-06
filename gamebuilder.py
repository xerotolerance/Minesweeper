from random import shuffle


def gen_board(rows: int, columns: int, nmines: int = None):
    def update_left_right(r, c):
        # Update Left
        if c and board[r][c - 1] != 'x':
            board[r][c - 1] += 1

        # Update Right
        if c < columns - 1 and board[r][c + 1] != 'x':
            board[r][c + 1] += 1

    def make_string(hidden=False):
        return "\n".join((' '.join(('?' if hidden and c != 0 else str(c) for c in row)) for row in board))

    if nmines is None:
        nmines = int((rows*columns) * (1/5))
    assert nmines < rows * columns

    board = [0 for _ in range(rows*columns)]    # create empty board in 1 dimension
    board[:nmines] = ['x' for _ in range(nmines)]   # populate the first few spaces with mines
    shuffle(board)  # mix up the board
    board = [board[n * columns: (n+1) * columns] for n in range(rows)]  # translate board into 2 dimensions

    mine_spots = [(r, c) for r in range(rows) for c in range(columns) if board[r][c] == 'x']    # find the mines

    # For each mine:
    for _ in range(len(mine_spots)):
        row_num, col_num = mine_spots.pop()
        # Update counts in squares left & right of mine
        update_left_right(row_num, col_num)

        # Update squares in row above
        if row_num:
            if board[row_num-1][col_num] != 'x':
                board[row_num - 1][col_num] += 1
            update_left_right(row_num-1, col_num)

        # Update squares in row below
        if row_num < rows - 1:
            if board[row_num + 1][col_num] != 'x':
                board[row_num + 1][col_num] += 1
            update_left_right(row_num+1, col_num)

    return make_string(hidden=True), make_string()



if __name__ == '__main__':
    board, key = gen_board(10, 10)
    print(f'board:\n{board}\n\nkey:\n{key}')
