Desenvolva um aplicativo desktop completo em Python para Windows chamado **CubeSolver**, capaz de resolver um cubo mágico 3x3x3 a partir de fotografias das seis faces.

### Tecnologias
- Python 3.12 ou compatível com as dependências.
- PySide6 para a interface desktop.
- OpenCV para processamento das imagens.
- Biblioteca kociemba para calcular a solução.
- Three.js para visualizar e animar o cubo em 3D, integrado à interface.
- pytest para testes automatizados.

### Funcionalidades

1. Criar uma interface moderna, escura, intuitiva e em português brasileiro.
2. Permitir importar seis imagens, uma para cada face do cubo.
3. Mostrar as seis imagens em painéis identificados como frente, trás, esquerda, direita, cima e baixo.
4. Detectar e classificar os nove adesivos de cada face usando OpenCV, com possibilidade de correção manual das cores.
5. Permitir confirmar o centro e a orientação de cada face antes de prosseguir.
6. Validar a quantidade de cada cor, as peças de canto e aresta, a orientação das peças e a consistência física do cubo.
7. Converter o estado validado para a notação exigida pela biblioteca kociemba.
8. Calcular uma sequência de movimentos válida e apresentar a solução completa.
9. Exibir o cubo em 3D com animações dos movimentos.
10. Permitir avançar, voltar, pausar, reiniciar e executar a sequência passo a passo.
11. Exibir a notação de cada movimento, com explicação de como girar a face.
12. Permitir carregar imagens novamente e corrigir qualquer erro sem reiniciar o aplicativo.
13. Incluir mensagens claras quando as fotos estiverem incorretas ou o estado do cubo for impossível.
14. Criar testes automatizados para cubo resolvido, embaralhamentos válidos, estados inválidos e conversão da notação.
15. Criar README em português com instruções de instalação, execução e empacotamento em executável Windows.

### Requisitos de qualidade

- Organize o código em módulos separados para interface, visão computacional, validação, resolução e visualização.
- Não use uma IA generativa para inventar movimentos. A solução deve ser calculada por um algoritmo determinístico.
- Não presuma que as fotos estejam sempre na orientação correta.
- Não declare uma solução válida antes de validar a configuração e testar a sequência calculada.
- Implemente primeiro uma versão funcional que permita informar as cores manualmente e resolver o cubo. Em seguida, implemente a leitura das fotografias e a visualização 3D.
- Execute os testes, corrija os erros encontrados e entregue o projeto completo com todos os arquivos necessários.

Comece apresentando o plano de implementação e a estrutura dos arquivos. Depois implemente o projeto em etapas, verificando cada etapa antes de prosseguir.