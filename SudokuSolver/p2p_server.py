import socket
import threading
import time
from protocolo import Message, JoinMessage, AcknowledgeMessage, SubgridTaskMessage, SubgridSolutionMessage, MergeRequestMessage, MergeResponseMessage
from sudoku_solver import SudokuSolver, MergingSolver
import uuid

class P2PServer:
    def __init__(self, p2p_port, known_nodes=None):
        self.p2p_port = p2p_port
        self.known_nodes = known_nodes if known_nodes else []
        #self.node_id = f'172.20.10.2:{self.p2p_port}'
        self.node_id = f'127.0.0.1:{self.p2p_port}'
        self.server_socket = None
        self.solved_puzzles = 0
        self.total_validations = 0
        self.node_validations = {self.node_id: 0}
        self.heartbeat_interval = 10

    def increment_solved_puzzles(self):
        self.solved_puzzles += 1

    def increment_validations(self, node, count):
        if node in self.node_validations:
            self.node_validations[node] += count
        else:
            self.node_validations[node] = count

    def increment_total_validations(self, count):
        self.total_validations += count

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.p2p_port))
        self.server_socket.listen(5)
        print(f"P2P Server started on port {self.p2p_port} with ID {self.node_id}")

        threading.Thread(target=self.listen_for_connections).start()
        if self.known_nodes:
            self.join_network()

    def run_heartbeat(self):
        while True:
            time.sleep(self.heartbeat_interval)
            for node in list(self.known_nodes):
                if not self.check_node_availability(node):
                    print(f"Node {node} is inactive.")
                    self.known_nodes.remove(node)

    def check_node_availability(self, node):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                sock.connect(self.convert_to_tuple(node))
                sock.shutdown(2)
            return True
        except:
            return False

    def listen_for_connections(self):
        while True:
            client_socket, _ = self.server_socket.accept()
            threading.Thread(target=self.handle_connection, args=(client_socket,)).start()

    def handle_connection(self, client_socket):
        try:
            data = client_socket.recv(8192)
            if not data:
                raise ValueError("Received empty data")
            message = Message.deserialize(data)
            response = self.process_message(message)
            if response:
                client_socket.send(response.serialize())
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            client_socket.close()

    def process_message(self, message):
        if isinstance(message, JoinMessage):
            new_node = message.data
            if isinstance(new_node, str):
                new_node = self.convert_to_tuple(new_node)
            if new_node not in self.known_nodes:
                self.known_nodes.append(new_node)
                self.node_validations[f"{new_node[0]}:{new_node[1]}"] = 0
            return AcknowledgeMessage(self.known_nodes)
        elif isinstance(message, SubgridTaskMessage):
            subgrid_coords, subgrid_data = message.data
            print(f"Received SubgridTaskMessage for coords {subgrid_coords}")
            try:
                solution = self.solve_subgrid((1,1), subgrid_data)
                return SubgridSolutionMessage(subgrid_coords, solution)
            except Exception as e:
                print(f"Error solving subgrid {subgrid_coords}: {e}")
                return None
        elif isinstance(message, SubgridSolutionMessage):
            print(f"Received SubgridSolutionMessage: {message.data}")
        elif isinstance(message, MergeRequestMessage):
            subgrid_coords, subgrid_solutions = message.data
            print(f"Received MergeRequestMessage for coords {subgrid_coords}")
            try:
                merged_solution = self.solve_merging_p2p(subgrid_solutions, subgrid_coords)
                return MergeResponseMessage(subgrid_coords, merged_solution)
            except Exception as e:
                print(f"Error merging subgrid {subgrid_coords}: {e}")
                return None
        elif isinstance(message, MergeResponseMessage):
            print(f"Received MergeResponseMessage: {message.data}")
        else:
            print(f"Unknown message type: {type(message)}")
            return None

    def join_network(self):
        for node_address in self.known_nodes:
            node_address = self.convert_to_tuple(node_address)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(node_address)
                    join_message = JoinMessage(self.node_id)
                    s.send(join_message.serialize())
                    response_data = s.recv(8192)
                    response = Message.deserialize(response_data)
                    if isinstance(response, AcknowledgeMessage):
                        print(f"Joined network via node {response.data}")
                        for addr in response.data:
                            addr = self.convert_to_tuple(addr)
                            if addr != self.node_id and addr not in self.known_nodes:
                                self.known_nodes.append(addr)
                                self.node_validations[f"{addr[0]}:{addr[1]}"] = 0
            except Exception as e:
                print(f"Error connecting to node {node_address}: {e}")

    def send_request(self, target_node, request_message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(target_node)
                s.send(request_message.serialize())
                response_data = s.recv(8192)
                
                if not response_data:
                    raise ValueError("Received empty response data")
                try:
                    response = Message.deserialize(response_data)
                    if response and hasattr(response, 'data'):
                        return response.data[1]
                    else:
                        raise ValueError("Invalid response format")
                except Exception as deserialization_error:
                    print(f"Deserialization error: {deserialization_error}")
                    return None
        except Exception as e:
            print(f"Error sending request to {target_node}: {e}")
            return None

    def send_merge_request(self, target_node, subgrid_solutions, target_coords):
        target_node = self.convert_to_tuple(target_node)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(target_node)
                request_message = MergeRequestMessage(target_coords, subgrid_solutions)
                s.send(request_message.serialize())
                response_data = s.recv(8192)
                if not response_data:
                    raise ValueError("Received empty response data")
                response = Message.deserialize(response_data)
                if isinstance(response, MergeResponseMessage):
                    return response.data[1]
                else:
                    print(f"Invalid response type: {type(response)}")
                    return None
        except Exception as e:
            print(f"Error sending merge request to {target_node}: {e}")
            return None

    @staticmethod
    def convert_to_tuple(address):
        if isinstance(address, str):
            address_parts = address.split(':')
            return address_parts[0], int(address_parts[1])
        return address

    def solve_subgrid(self, coords, subgrid_data):
        if not all(len(row) == 3 for row in subgrid_data) or len(subgrid_data) != 3:
            raise ValueError(f"Invalid subgrid data: {subgrid_data}")
        solver = SudokuSolver(subgrid_data)
        solver.solve("subgrid", coords)
        solutions = solver.get_subgrid_solutions()
        if coords in solutions:
            self.increment_total_validations(solver.get_validations())
            self.increment_validations(self.node_id, solver.get_validations())
            return solutions[coords]
        else:
            print(f"No solution found for subgrid at {coords}")
            return []

    def solve_merging_p2p(self, subgrid_possibilities, coords):
        print(subgrid_possibilities)
        solver = MergingSolver(subgrid_possibilities)
        merged_solution = solver.solve("merging", coords)
        if merged_solution:
            self.increment_total_validations(solver.get_validations())
            self.increment_validations(self.node_id, solver.get_validations())
            return merged_solution
        else:
            print(f"No merged solution found for subgrid at {coords}")
            return []


    def distribute_sudoku_task(self, sudoku_grid):
        start_time = time.time()
        solutions = {}
        threads = []
        responses = {}

        for i in range(3):
            for j in range(3):
                subgrid_coords = (i + 1, j + 1)
                subgrid_data = [row[j * 3:(j + 1) * 3] for row in sudoku_grid[i * 3:(i + 1) * 3]]
                target_node = self.known_nodes[(i * 3 + j) % len(self.known_nodes)]
                thread = threading.Thread(target=self.solve_and_collect,
                                          args=(target_node, subgrid_coords, subgrid_data, solutions, responses))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

        for key, response in responses.items():
            if response is None:
                print(f"No response received for subgrid {key}")
            elif not response:
                print(f"Error processing subgrid {key}")

        if solutions:
            merge_threads = []
            merged_solutions = {}

            for i in range(3):
                for j in range(3):
                    subgrid_coords = (i + 1, j + 1)
                    target_node = self.known_nodes[(i * 3 + j) % len(self.known_nodes)]
                    thread = threading.Thread(target=self.collect_and_merge,
                                            args=(target_node, solutions, subgrid_coords, merged_solutions))
                    merge_threads.append(thread)
                    thread.start()

            for thread in merge_threads:
                thread.join()

            final_grid = self.create_final_grid(merged_solutions)
            solver = SudokuSolver(final_grid)
            print(solver)
            print(solver.is_solved())
            response = {'request_id': str(uuid.uuid4()), 'solutions': final_grid}
        else:
            response = {'request_id': str(uuid.uuid4()), 'solutions': None}

        end_time = time.time()
        elapsed_time = end_time - start_time
        response['time_taken'] = elapsed_time

        print(self.node_validations.items())
        print(self.total_validations)
        self.increment_solved_puzzles()
        print(elapsed_time)
        print(f"Sending response: {response}")
        return response

    def solve_and_collect(self, target_node, subgrid_coords, subgrid_data, solutions, responses):
        try:
            solution = self.send_request(target_node, SubgridTaskMessage(subgrid_coords, subgrid_data))
            if solution:
                print(solution)
                solutions[str(subgrid_coords)] = solution
                responses[str(subgrid_coords)] = True
                print(str(subgrid_coords))
            else:
                responses[str(subgrid_coords)] = False
        except Exception as e:
            print(f"Failed to get response from {target_node} for subgrid {subgrid_coords}: {e}")
            responses[str(subgrid_coords)] = None

    def collect_and_merge(self, target_node, solutions, subgrid_coords, merged_solutions):
        try:
            merged_solution = self.send_merge_request(target_node, solutions, subgrid_coords)
            if merged_solution:
                print(f"Merged solution for subgrid {subgrid_coords}: {merged_solution}")
                merged_solutions[subgrid_coords] = merged_solution
            else:
                print(f"No merged solution received for subgrid {subgrid_coords}")
        except Exception as e:
            print(f"Failed to merge subgrid {subgrid_coords} from {target_node}: {e}")

    def create_final_grid(self, merged_solutions):
        final_grid = [[0] * 9 for _ in range(9)]
        for (row_block, col_block), subgrid in merged_solutions.items():
            row_start = (row_block - 1) * 3
            col_start = (col_block - 1) * 3
            
            if not isinstance(subgrid, list) or not all(isinstance(row, list) for row in subgrid):
                print(f"Invalid subgrid format for {row_block}, {col_block}: {subgrid}")
                continue
            
            if len(subgrid) != 9 or any(len(row) != 9 for row in subgrid):
                print(f"Unexpected subgrid dimensions for {row_block}, {col_block}: {subgrid}")
                continue

            subgrid_3x3 = [row[col_start:col_start + 3] for row in subgrid[row_start:row_start + 3]]
            
            for i in range(3):
                for j in range(3):
                    try:
                        final_grid[row_start + i][col_start + j] = subgrid_3x3[i][j]
                    except IndexError as e:
                        print(f"IndexError at ({row_start + i}, {col_start + j}) for subgrid {subgrid}: {e}")
                        raise
                    
        return final_grid

    @staticmethod
    def convert_str_to_tuple(coord_str):
        return eval(coord_str)
