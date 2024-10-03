import copy
from sudoku import Sudoku
from itertools import product

class SudokuSolver:
    def __init__(self, sudoku_grid):
        self.sudoku = Sudoku(sudoku_grid)
        self.subgrid_solutions = {}
        self.validations = 0

    def __str__(self):
        return str(self.sudoku)

    def get_sudoku(self):
        return self.sudoku.grid
    
    def validate(self):
        self.validations += 1
    
    def get_validations(self):
        return self.validations

    def update_sudoku(self, sudoku_grid):
        self.sudoku = Sudoku(sudoku_grid)

    def is_solved(self):
        return self.sudoku.check()

    def solve(self, task, coordinates):
        if task == "subgrid":
            return self.solve_subgrid(coordinates)
        else:
            raise ValueError("Invalid task")

    def solve_subgrid(self, coordinates):
        print(coordinates)
        subgrid = self.get_subgrid(coordinates)
        empty_spaces = self.get_empty_spaces(subgrid)
        available_numbers = self.get_available_numbers(subgrid)
        solutions = self.find_solutions_for_subgrid(subgrid, empty_spaces, available_numbers)
        self.subgrid_solutions[coordinates] = solutions
        print(solutions)
        return solutions

    def get_subgrid(self, coordinates):
        row_block, col_block = coordinates
        if not (1 <= row_block <= 3 and 1 <= col_block <= 3):
            raise ValueError("Invalid coordinates. Valid coordinates are (1,1) to (3,3) inclusive.")

        row_start = (row_block - 1) * 3
        col_start = ((col_block - 1) * 3)

        subgrid = []
        for i in range(3):
            row = []
            for j in range(3):
                row.append(self.sudoku.grid[row_start + i][col_start + j])
            subgrid.append(row)

        print(f"Subgrid: {subgrid}")

        return subgrid

    def get_empty_spaces(self, subgrid):
        empty_spaces = []
        for i in range(3):
            for j in range(3):
                if subgrid[i][j] == 0:
                    empty_spaces.append((i, j))
        return empty_spaces

    def get_available_numbers(self, subgrid):
        used_numbers = set()
        for row in subgrid:
            for num in row:
                if num != 0:
                    used_numbers.add(num)
        available_numbers = set(range(1, 10)) - used_numbers
        return available_numbers

    def find_solutions_for_subgrid(self, subgrid, empty_spaces, available_numbers):
        solutions = []
        self.solve_subgrid_recursive(subgrid, empty_spaces, list(available_numbers), 0, solutions)
        return solutions

    def solve_subgrid_recursive(self, subgrid, empty_spaces, available_numbers, index, solutions):
        if index == len(empty_spaces):
            if self.is_valid_subgrid(subgrid):
                solutions.append(copy.deepcopy(subgrid))
            return

        row, col = empty_spaces[index]

        for num in available_numbers:
            if self.is_valid_placement(subgrid, row, col, num):
                subgrid[row][col] = num
                self.solve_subgrid_recursive(subgrid, empty_spaces, available_numbers, index + 1, solutions)
                subgrid[row][col] = 0

    def is_valid_placement(self, subgrid, row, col, num):
        self.validate()
        for i in range(3):
            if subgrid[row][i] == num or subgrid[i][col] == num:
                return False
        return True

    def is_valid_subgrid(self, subgrid):
        self.validate()
        numbers = [num for row in subgrid for num in row if num != 0]
        return len(numbers) == len(set(numbers))

    def update_subgrid_solutions(self):
        for row in range(1, 4):
            for col in range(1, 4):
                coordinates = (row, col)
                self.solve_subgrid(coordinates)

    def get_subgrid_solutions(self):
        return self.subgrid_solutions


class MergingSolver:
    def __init__(self, subgrid_possibilities):
        self.subgrid_possibilities = subgrid_possibilities
        self.sudoku = Sudoku([[0] * 9 for _ in range(9)])
        self.validations = 0

    def validate(self):
        self.validations += 1

    def get_validations(self):
        return self.validations

    def solve(self, task, coordinates):
        if task == "merging":
            return self.solve_merging(coordinates)
        else:
            raise ValueError("Invalid task")

    def solve_merging(self, coordinates):
        self.merge_solutions_for_subgrid(coordinates)
        return self.sudoku.grid

    def merge_solutions_for_subgrid(self, coordinates):
        related_subgrids = [
            (coordinates[0], col) for col in range(1, 4) if col != coordinates[1]
        ] + [
            (row, coordinates[1]) for row in range(1, 4) if row != coordinates[0]
        ]

        combined_solutions = self.combine_solutions(related_subgrids, coordinates)
        if combined_solutions:
            chosen_solution = combined_solutions[0]
            row_start = (coordinates[0] - 1) * 3
            col_start = (coordinates[1] - 1) * 3
            for i in range(3):
                for j in range(3):
                    self.sudoku.grid[row_start + i][col_start + j] = chosen_solution[i][j]
        else:
            print(f"No valid combined solutions found for subgrid {coordinates}")

    def combine_solutions(self, related_subgrids, target_coordinates):
        target_solutions = self.subgrid_possibilities.get(str(target_coordinates), [])
        if not target_solutions:
            print(f"No target solutions for subgrid {target_coordinates}")
            return []

        related_solutions = [self.subgrid_possibilities.get(str(coords), []) for coords in related_subgrids]

        for idx, solutions in enumerate(related_solutions):
            if not solutions:
                print(f"No solutions for related subgrid {related_subgrids[idx]}")

        combined_solutions = []

        for target_sol in target_solutions:
            for related_combination in product(*related_solutions):
                self.validate()
                if self.is_valid_combination(target_sol, related_combination, target_coordinates, related_subgrids):
                    combined_solutions.append(target_sol)
        return combined_solutions


    def is_valid_combination(self, target_sol, related_combination, target_coordinates, related_subgrids):
        temp_grid = [["-" for _ in range(9)] for _ in range(9)]

        row_start = (target_coordinates[0] - 1) * 3
        col_start = (target_coordinates[1] - 1) * 3
        for i in range(3):
            for j in range(3):
                temp_grid[row_start + i][col_start + j] = target_sol[i][j]

        for related_sol, (related_row_block, related_col_block) in zip(related_combination, related_subgrids):
            row_start = (related_row_block - 1) * 3
            col_start = (related_col_block - 1) * 3
            for i in range(3):
                for j in range(3):
                    temp_grid[row_start + i][col_start + j] = related_sol[i][j]

        for i in range(9):
            self.validate()
            row = [num for num in temp_grid[i] if num != "-"]
            if len(row) != len(set(row)):
                return False
            col = [temp_grid[j][i] for j in range(9) if temp_grid[j][i] != "-"]
            if len(col) != len(set(col)):
                return False

        return True