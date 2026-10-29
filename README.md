# 🧊 CubeSolver — Resolvedor de Cubo Mágico 3x3x3 Desktop

Aplicativo desktop completo em Python para Windows capaz de detectar, validar, resolver e animar em 3D um cubo mágico 3x3x3 a partir de **fotografias das seis faces**, **captura ao vivo pela câmera (webcam)** ou **edição manual**.

---

## ✨ Funcionalidades Principais

1. **Interface Desktop Moderna em Português (PySide6):**
   - Tema escuro intuitivo com painéis dedicados para as 6 faces: **Cima (U)**, **Baixo (D)**, **Frente (F)**, **Trás (B)**, **Esquerda (L)** e **Direita (R)**.
2. **Múltiplas Formas de Entrada:**
   - **📷 Assistente de Câmera (Webcam):** Captura guiada em tempo real com mira 3x3 centralizada e prévia instantânea das cores detectadas (modo de 6 faces ou captura individual por face).
   - **📁 Importação de 6 Fotografias:** Carregamento individual em cada painel ou importação em lote das 6 imagens (ex.: pasta `exemplos_faces/`).
   - **🧩 Importação de Planificação (`cubo.png`):** Extração automática das 6 faces a partir de uma imagem em formato de cruz.
   - **🎨 Edição e Correção Manual:** Paleta de pincéis de cores e alternância rápida clicando em qualquer adesivo.
3. **Ajuste de Orientação e Confirmação de Centros:**
   - Botões `↺ 90°` e `↻ 90°` em cada face para girar a orientação da foto/grade sem precisar reiniciar o aplicativo.
   - Confirmação explícita do centro e orientação de cada face antes da resolução.
4. **Validação Física e Combinatória Completa:**
   - Contagem exata de 9 adesivos para cada uma das 6 cores (`Branco`, `Vermelho`, `Verde`, `Amarelo`, `Laranja`, `Azul`).
   - Verificação de 6 centros distintos, existência e quiralidade das 8 peças de canto, 12 peças de aresta, orientação de cantos (*Corner Twist*), orientação de arestas (*Edge Flip*) e paridade global de permutação.
5. **Resolução Determinística (`kociemba`) com Verificação por Simulação:**
   - Conversão automática para a notação Kociemba de 54 caracteres (`UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB`).
   - Cálculo determinístico pelo algoritmo *Two-Phase* de Herbert Kociemba.
   - Simulação automática da sequência gerada sobre o modelo virtual antes de declarar a solução válida.
6. **Visualização e Animação 3D Interativa (`Three.js`):**
   - Cubo 3D interativo integrado à interface via `QWebEngineView` (rotação orbital de 360° com o mouse e zoom).
   - Controles de reprodução: **⏮ Reiniciar**, **⏪ Voltar**, **▶ Executar / ⏸ Pausar**, **⏩ Avançar Passo a Passo** e seletor de velocidade.
   - Explicação detalhada em português de como girar a face em cada movimento (`R`, `R'`, `U2`, etc.).

---

## 📂 Estrutura do Projeto

```text
cubo-magico/
├── main.py                        # Ponto de entrada do aplicativo desktop
├── requirements.txt               # Dependências do projeto
├── README.md                      # Documentação completa em português
├── .gitignore                     # Arquivos ignorados pelo Git
├── cubo.png                       # Imagem de planificação de referência
├── exemplos_faces/                # 6 fotos individuais extraídas para teste rápido
├── cube_solver/
│   ├── models/
│   │   └── cube_state.py          # Modelo matemático 3x3x3 e aplicação de movimentos
│   ├── validation/
│   │   └── validator.py           # Validação de cores, peças, orientação e paridade
│   ├── solver/
│   │   ├── notation.py            # Conversão Kociemba (54 chars) e explicações em PT-BR
│   │   └── kociemba_solver.py     # Motor determinístico Kociemba + teste de verificação
│   ├── vision/
│   │   ├── color_classifier.py    # Classificação de cores em espaço HSV/BGR
│   │   └── detector.py            # Detecção OpenCV para fotos, planificação e webcam
│   ├── viewer3d/
│   │   ├── viewer_widget.py       # Integração PySide6 QWebEngineView <-> Three.js
│   │   └── assets/
│   │       ├── cube3d.html        # Cena 3D interativa e animador de movimentos
│   │       └── three.min.js       # Biblioteca Three.js local (funciona 100% offline)
│   └── ui/
│       ├── styles.py              # Tema escuro QSS
│       ├── camera_dialog.py       # Assistente de captura ao vivo por câmera (Webcam)
│       ├── face_panel.py          # Painel individual de cada face (foto, 3x3, rotação 90°)
│       ├── solution_panel.py      # Painel de validação e reprodução passo a passo
│       └── main_window.py         # Janela principal do aplicativo
└── tests/
    ├── test_cube_state.py         # Testes de movimentos e rotações
    ├── test_validator.py          # Testes de estados válidos e fisicamente impossíveis
    ├── test_notation_solver.py    # Testes de notação Kociemba e resolução de embaralhamentos
    ├── test_vision.py             # Testes de visão computacional OpenCV
    └── test_ui.py                 # Testes automatizados da interface gráfica
```

---

## 🚀 Instalação

1. Certifique-se de ter o **Python 3.12+** instalado no Windows.
2. (Opcional) Crie e ative um ambiente virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Instale as dependências:
   ```powershell
   python -m pip install -r requirements.txt
   ```

---

## 💻 Como Executar o Aplicativo

Na raiz do projeto, execute:

```powershell
python main.py
```

### Fluxo de Uso Recomendado:
1. **Capturar ou Importar:**
   - Clique em **"📷 Assistente de Câmera (Webcam)"** para capturar as faces apontando o cubo para a câmera; **ou**
   - Clique em **"📁 Importar 6 Fotos"** (você pode selecionar as 6 imagens de exemplo na pasta `exemplos_faces/`); **ou**
   - Clique em **"🧩 Importar Planificação (cubo.png)"** para carregar a imagem `cubo.png`.
2. **Revisar e Confirmar:**
   - Caso alguma foto esteja virada, use os botões **`↺ 90°`** ou **`↻ 90°`** no painel da respectiva face.
   - Se desejar ajustar alguma cor manualmente, selecione uma cor no **Pincel de Correção Manual** (ou use o modo *Alternar ao Clicar*) e clique sobre o adesivo.
   - Confirme os centros e orientações clicando em **"✔ Confirmar Centros e Orientações (Todas)"**.
3. **Resolver e Animar em 3D:**
   - Clique em **"🚀 Validar e Resolver Cubo"**.
   - Utilize os botões **▶ Executar**, **⏸ Pausar**, **⏩ Avançar**, **⏪ Voltar** e **⏮ Reiniciar** para acompanhar cada movimento no cubo 3D junto com a explicação em português.

---

## 🧪 Como Executar os Testes Automatizados

Para rodar toda a suíte de testes (`pytest`):

```powershell
python -m pytest -v
```

---

## 📦 Como Gerar o Executável Windows (`.exe`)

Com o `pyinstaller` instalado (já incluído no `requirements.txt`), execute o comando abaixo na raiz do projeto para empacotar o aplicativo incluindo os recursos 3D (`cube3d.html` e `three.min.js`):

```powershell
pyinstaller --noconfirm --onedir --windowed --name CubeSolver --add-data "cube_solver/viewer3d/assets;cube_solver/viewer3d/assets" main.py
```

O executável final estará disponível em:
```text
dist\CubeSolver\CubeSolver.exe
```

