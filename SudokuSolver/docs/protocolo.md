# Protocolo de Comunicação para a Resolução Distribuída de Sudoku

## Visão Geral
Este documento descreve o protocolo de comunicação entre nós numa rede distribuída destinada à resolução de puzzles Sudoku. A comunicação utiliza um modelo peer-to-peer (P2P), com mensagens serializadas usando o módulo `pickle`, facilitando a transmissão de objetos complexos.

## Segurança
É importante notar que a utilização de `pickle` para serialização pode ser insegura se os dados recebidos não forem de fontes fiáveis. Recomenda-se a implementação de verificações de autenticação e validação dos dados recebidos para mitigar riscos de segurança.

## Formato das Mensagens
As mensagens na rede são objetos de classe que herdam de uma classe base `Message`. Cada tipo de mensagem possui um propósito específico dentro do protocolo e transporta dados relevantes para a sua função.

### Classe Base: Message
- **Tipo**: `Message`
- **Campos**:
  - `message_type`: Tipo da mensagem (cadeia de caracteres)
  - `data`: Dados contidos na mensagem (variável)

### Tipos de Mensagem
#### JoinMessage
- **Tipo**: `JoinMessage`
- **Descrição**: Utilizada por um novo nó ao conectar-se à rede.
- **Campos**:
  - `node_id`: Identificador único do nó que se conecta.

#### AcknowledgeMessage
- **Tipo**: `Acknowledge`
- **Descrição**: Resposta ao `JoinMessage`, contendo informações sobre outros nós conhecidos.
- **Campos**:
  - `known_nodes`: Lista dos identificadores dos nós conhecidos pelo nó respondente.

#### SubgridTaskMessage
- **Tipo**: `SubgridTask`
- **Descrição**: Solicita a resolução de um subgrid específico.
- **Campos**:
  - `subgrid_coords`: Coordenadas do subgrid a ser resolvido.
  - `subgrid_data`: Dados do subgrid para resolução.

#### SubgridSolutionMessage
- **Tipo**: `SubgridSolution`
- **Descrição**: Devolve a solução de um subgrid.
- **Campos**:
  - `subgrid_coords`: Coordenadas do subgrid resolvido.
  - `solution`: Solução do subgrid.

#### MergeRequestMessage
- **Tipo**: `MergeRequest`
- **Descrição**: Inicia o processo de fusão de soluções parciais.
- **Campos**:
  - `subgrid_coords`: Coordenadas do subgrid para o qual a fusão é solicitada.
  - `partial_solutions`: Lista de soluções parciais de subgrids a serem combinadas.

#### MergeResponseMessage
- **Tipo**: `MergeResponse`
- **Descrição**: Contém a solução final após a fusão.
- **Campos**:
  - `subgrid_coords`: Coordenadas do subgrid final.
  - `merged_solution`: Solução final combinada do subgrid.

## Uso das Mensagens
Cada nó na rede pode enviar e receber estas mensagens conforme necessário. O processo típico de comunicação pode envolver:
1. Um nó junta-se à rede e envia um `JoinMessage`.
2. Os nós respondem com `AcknowledgeMessage` para informar sobre outros nós na rede.
3. Tarefas de subgrids são distribuídas usando `SubgridTaskMessage`.
4. As soluções são recolhidas através de `SubgridSolutionMessage`.
5. A fusão de soluções é solicitada por `MergeRequestMessage` e concluída com `MergeResponseMessage`.

## Conclusão
Este protocolo facilita a colaboração eficaz entre nós numa rede distribuída para resolver Sudoku de forma eficiente e escalável. Alterações e expansões futuras podem ser implementadas conforme necessário para suportar mais funcionalidades ou melhorar a segurança e eficiência da rede.