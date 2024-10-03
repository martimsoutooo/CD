import pickle

class Message:
    def __init__(self, message_type, data):
        self.message_type = message_type
        self.data = data

    def serialize(self):
        """ Serializa a mensagem usando pickle para transmissão. """
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        """ Deserializa a mensagem recebida. """
        return pickle.loads(data)


class JoinMessage(Message):
    def __init__(self, node_id):
        """ Mensagem enviada por um novo nó ao se conectar à rede. """
        super().__init__("JoinMessage", node_id)


class AcknowledgeMessage(Message):
    def __init__(self, known_nodes):
        """ Mensagem de resposta com a lista de nós conhecidos. """
        super().__init__("Acknowledge", known_nodes)


class SubgridTaskMessage(Message):
    def __init__(self, subgrid_coords, subgrid_data):
        """ Mensagem para solicitar a resolução de um subgrid específico. """
        super().__init__("SubgridTask", (subgrid_coords, subgrid_data))


class SubgridSolutionMessage(Message):
    def __init__(self, subgrid_coords, solution):
        """ Mensagem para enviar uma solução de subgrid de volta ao solicitante. """
        super().__init__("SubgridSolution", (subgrid_coords, solution))


class MergeRequestMessage(Message):
    def __init__(self, subgrid_coords, partial_solutions):
        """ Mensagem para solicitar a fusão de soluções de subgrid. """
        super().__init__("MergeRequest", (subgrid_coords, partial_solutions))


class MergeResponseMessage(Message):
    def __init__(self, subgrid_coords, merged_solution):
        """ Mensagem que contém a solução final após a fusão. """
        super().__init__("MergeResponse", (subgrid_coords, merged_solution))


class SudokuProto:
    @staticmethod
    def request(sudoku_grid, origin_node, request_id):
        """Create a request message for solving a sudoku puzzle."""
        message_data = {
            'type': 'solve_request',
            'sudoku_grid': sudoku_grid,
            'origin_node': origin_node,
            'request_id': request_id
        }
        return pickle.dumps(message_data)

    @staticmethod
    def solve_response(sudoku_grid, solution, origin_node, request_id):
        """Create a response message with the solution of the sudoku puzzle."""
        message_data = {
            'type': 'solve_response',
            'sudoku_grid': sudoku_grid,
            'solution': solution,
            'origin_node': origin_node,
            'request_id': request_id
        }
        return pickle.dumps(message_data)

    @staticmethod
    def deserialize_message(serialized_message):
        """Deserialize a message received from the network."""
        return pickle.loads(serialized_message)
    