import enum
import random
import os

_COLUMNS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_FIELD_SIZE = 10
_DEBUG = os.environ.get('DEBUG', False)


class BattleshipException(Exception):
    pass


class FieldGenerationException(BattleshipException):
    pass


class FieldCell(enum.Enum):
    WATER = '.'
    SHIP = 'S'
    DEBRIS = '@'
    SUNKEN = 'F'
    MISS = 'x'


class Shot(enum.Enum):
    MISS = enum.auto()
    HIT = enum.auto()
    SUNK = enum.auto()


def _is_valid_x_ship_start(field, cell_idx, deck_length, field_size):
    cell_y, cell_x = cell_idx // field_size, cell_idx % field_size
    if field_size - cell_x < deck_length:
        return []
    deck_offset = cell_x + deck_length
    start_x, end_x = max(cell_x - 1, 0), min(deck_offset + 1, field_size)
    start_y, end_y = max(cell_y - 1, 0), min(cell_y + 2, field_size)
    ship_coords = []
    for i in range(start_y, end_y):
        row_idx = i * field_size
        for j in range(start_x, end_x):
            cell_idx = row_idx + j
            if i == cell_y and cell_x <= j < deck_offset:
                ship_coords.append(cell_idx)
            field_cell = field[cell_idx]
            if field_cell is not FieldCell.WATER:
                return []
    return ship_coords


def _is_valid_y_ship_start(field, cell_idx, deck_length, field_size):
    cell_y, cell_x = cell_idx // field_size, cell_idx % field_size
    if field_size - cell_y < deck_length:
        return []
    deck_offset = cell_y + deck_length
    start_x, end_x = max(cell_x - 1, 0), min(cell_x + 2, field_size)
    start_y, end_y = max(cell_y - 1, 0), min(deck_offset + 1, field_size)
    ship_coords = []
    for i in range(start_y, end_y):
        row_idx = i * field_size
        for j in range(start_x, end_x):
            cell_idx = row_idx + j
            if j == cell_x and cell_y <= i < deck_offset:
                ship_coords.append(cell_idx)
            field_cell = field[cell_idx]
            if field_cell is not FieldCell.WATER:
                return []
    return ship_coords


def generate_field(field_size=10, max_deck_length=4):
    cell_num = field_size * field_size
    field = [FieldCell.WATER for _ in range(cell_num)]
    ships = []
    deck_length_limit = max_deck_length + 1
    for deck_length in reversed(range(1, deck_length_limit)):
        for _ in range(deck_length_limit - deck_length):
            possible_cells = []  # possible cells to put ship onto
            for cell_idx in range(cell_num):
                ship_x_coords = _is_valid_x_ship_start(field, cell_idx, deck_length, field_size)
                if ship_x_coords:
                    possible_cells.append(ship_x_coords)
                ship_y_coords = _is_valid_y_ship_start(field, cell_idx, deck_length, field_size)
                if ship_y_coords:
                    possible_cells.append(ship_y_coords)
            possible_num = len(possible_cells)
            if not possible_num:
                raise FieldGenerationException(
                    'Could not generate field with given field size of '
                    f'{field_size} and max deck length of {max_deck_length}')
            ship = possible_cells[random.randint(0, possible_num - 1)]
            ships.append(ship)
            for cell_idx in ship:
                field[cell_idx] = FieldCell.SHIP
    return field, ships


def _print_battleship_header(field_index):
    print('    ', end='')
    for col_idx in field_index:
        col_name = _COLUMNS[col_idx]
        print(col_name, end=' ')


def _print_field_row(field, row_idx, field_size, show_ships=False):
    for j in range(field_size):
        cell_idx = row_idx + j
        cell = field[cell_idx]
        if not show_ships and cell is FieldCell.SHIP:
            cell = FieldCell.WATER
        print(cell.value, end=' ')


def _print_battleship_screen(field_player, field_ai, field_size=10):
    field_index = list(range(field_size))

    try:
        _print_battleship_header(field_index)
        _print_battleship_header(field_index)
        print(end='\n')
        for i in range(field_size):
            row_name = str(i + 1).ljust(2)
            row_idx = i * field_size
            print(f'{row_name}) ', end='')
            _print_field_row(field_player, row_idx, field_size, show_ships=True)
            print(f'{row_name}) ', end='')
            _print_field_row(field_ai, row_idx, field_size, show_ships=_DEBUG)
            print(end='\n')
    except IndexError as exc:
        raise BattleshipException(f'Invalid field size of {field_size}') from exc
    print('    ^ Your field ^')


def _accept_valid_bullet_placement(field, field_size=10):
    is_valid_placement = False
    cell_idx = -1
    while not is_valid_placement:
        placement = input('Enter column and row such as A3: ')
        placement = placement.upper()
        if len(placement) <= 0 or len(placement) > 3:
            print('Error: Please enter only one column and row such as A3')
            continue
        col = placement[0]
        row = placement[1:]
        if not col.isalpha() or not row.isnumeric():
            print('Error: Please enter letter for column and number for row')
            continue
        col = _COLUMNS.find(col)
        if not (-1 < col < field_size):
            print('Error: Please enter valid column')
            continue
        row = int(row) - 1
        if not (-1 < row < field_size):
            print('Error: Please enter valid row')
            continue
        cell_idx = row * field_size + col
        cell = field[cell_idx]
        if cell is not FieldCell.WATER and cell is not FieldCell.SHIP:
            print('You have already shot a bullet here, pick somewhere else')
            continue
        is_valid_placement = True
    return cell_idx


def register_hit(field, ships, cell_idx):
    cell = field[cell_idx]
    if cell is FieldCell.WATER:
        field[cell_idx] = FieldCell.MISS
        return Shot.MISS
    assert cell is FieldCell.SHIP
    field[cell_idx] = FieldCell.DEBRIS
    for ship in ships:
        if cell_idx not in ship:
            continue
        for ship_cell_idx in ship:
            if field[ship_cell_idx] is FieldCell.SHIP:
                return Shot.HIT
        for ship_cell_idx in ship:
            field[ship_cell_idx] = FieldCell.SUNKEN
        return Shot.SUNK


def check_for_game_over(field):
    for cell in field:
        if cell is FieldCell.SHIP:
            return False
    return True


def _is_sunken_ship_in_proximity(field, cell_x, cell_y, field_size):
    start_x, end_x = max(cell_x - 1, 0), min(cell_x + 2, field_size)
    start_y, end_y = max(cell_y - 1, 0), min(cell_y + 2, field_size)
    for i in range(start_y, end_y):
        for j in range(start_x, end_x):
            cell_idx = i * field_size + j
            cell = field[cell_idx]
            if cell is FieldCell.SUNKEN:
                return True
    return False


def cell_idx_to_human_readable(cell_idx, field_size):
    cell_y, cell_x = cell_idx // field_size, cell_idx % field_size
    return f'{_COLUMNS[cell_x]}{cell_y + 1}'


def decide_random_shot(field, field_size=10):
    potential_targets = []
    for i in range(field_size):
        for j in range(field_size):
            cell_idx = i * field_size + j
            cell = field[cell_idx]
            if cell is FieldCell.MISS or cell is FieldCell.DEBRIS:
                continue
            if cell is FieldCell.SHIP:
                potential_targets.append(cell_idx)
                continue
            if _is_sunken_ship_in_proximity(field, j, i, field_size):
                continue
            potential_targets.append(cell_idx)
    target_num = len(potential_targets)
    if not target_num:
        raise BattleshipException('Could not dtermine next random target')
    return potential_targets[random.randint(0, target_num - 1)]


def make_recommendations(field, recomendation_pool, cell_idx, ai_shot, field_size=10):
    if ai_shot is Shot.MISS:
        return recomendation_pool
    if ai_shot is Shot.SUNK:
        return []
    i, j = cell_idx // field_size, cell_idx % field_size
    if not recomendation_pool:
        possible_recomendations = [[i + 1, j], [i, j + 1], [i - 1, j], [i, j - 1]]
        recomendation_pool = []
        for r_i, r_j in possible_recomendations:
            if r_i < 0 or r_i >= field_size or r_j < 0 or r_j >= field_size:
                continue
            cell_idx = r_i * field_size + r_j
            cell = field[cell_idx]
            if cell is FieldCell.MISS or cell is FieldCell.SUNKEN or cell is FieldCell.DEBRIS:
                continue
            recomendation_pool.append([r_i, r_j])
        return recomendation_pool
    new_recomendation_pool = []
    for r_i, r_j in recomendation_pool:
        if r_i == i and r_j == j or r_j != j and r_i != i:
            continue
        if r_i == i:
            new_recomendation_pool.append([r_i, r_j])
            if j - r_j > 0:
                n_r_i, n_r_j = i, j + 1
            else:
                n_r_i, n_r_j = i, j - 1
        else:
            new_recomendation_pool.append([r_i, r_j])
            if i - r_i > 0:
                n_r_i, n_r_j = i + 1, j
            else:
                n_r_i, n_r_j = i - 1, j
        if n_r_i < 0 or n_r_i >= field_size or n_r_j < 0 or n_r_j >= field_size:
            continue
        new_recomendation_pool.append([n_r_i, n_r_j])
    return new_recomendation_pool


def decide_recommended_shot(field, recomendation_pool, field_size=10):
    potential_targets = []
    for r_i, r_j in recomendation_pool:
        cell_idx = r_i * field_size + r_j
        cell = field[cell_idx]
        if cell is FieldCell.MISS or cell is FieldCell.SUNKEN or cell is FieldCell.DEBRIS:
            continue
        if _is_sunken_ship_in_proximity(field, r_j, r_i, field_size):
            continue
        potential_targets.append(cell_idx)
    target_num = len(potential_targets)
    if not target_num:
        if _DEBUG:
            print('Error: Could not decide according to recommendations')
            print(recomendation_pool)
        return decide_random_shot(field, field_size=field_size)
    return potential_targets[random.randint(0, target_num - 1)]


def _main_loop():
    field_player, ships_player = generate_field(field_size=_FIELD_SIZE)
    field_ai, ships_ai = generate_field(field_size=_FIELD_SIZE)
    print('\t\tWELCOME TO BATTLESHIP!', 'Legend:', sep='\n\n')
    for mark in FieldCell:
        print(mark.value, '-', mark.name)

    game_over = False
    turn_count = 0
    recomendation_pool = []
    while not game_over:
        _print_battleship_screen(field_player, field_ai, field_size=_FIELD_SIZE)
        turn_count += 1
        print(f'\t\tTurn: #{turn_count} (player)')

        cell_idx = _accept_valid_bullet_placement(field_ai, field_size=_FIELD_SIZE)
        player_shot = register_hit(field_ai, ships_ai, cell_idx)
        if player_shot is Shot.HIT:
            print('YOUR SHOT HIT, but ship is still afloat...')
            continue
        if player_shot is Shot.SUNK:
            print('YOU\'VE SUNK THEIR BATTLESHIP!')
            game_over = check_for_game_over(field_ai)
            if game_over:
                print('\n\t\tYOU WON!')
            continue
        turn_count += 1
        ai_shot = None
        print(
            'YOU MISSED! AI\'s turn...',
            f'\t\tTurn: #{turn_count} (AI)',
            'AI\'s turn log:', sep='\n')
        while not game_over and ai_shot is not Shot.MISS:
            if not recomendation_pool:
                cell_idx = decide_random_shot(field_player, field_size=_FIELD_SIZE)
            else:
                cell_idx = decide_recommended_shot(field_player, recomendation_pool, field_size=_FIELD_SIZE)
            ai_shot = register_hit(field_player, ships_player, cell_idx)
            recomendation_pool = make_recommendations(field_player, recomendation_pool, cell_idx, ai_shot, field_size=_FIELD_SIZE)
            ai_shot_hr = cell_idx_to_human_readable(cell_idx, field_size=_FIELD_SIZE)
            print(ai_shot_hr, '-', ai_shot.name)
            game_over = check_for_game_over(field_player)
            if game_over:
                print('\n\t\tYOU LOST!')


if __name__ == '__main__':
    _main_loop()
