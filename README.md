# 🎮 MouseControl

Aplicação Streamlit para controle do cursor do mouse via gestos manuais capturados por webcam, utilizando visão computacional e machine learning.

## 📋 Descrição

O MouseControl permite controlar o cursor do computador e executar cliques através de gestos manuais, eliminando a necessidade de contato físico com um mouse tradicional. Utiliza MediaPipe Hands para detecção de landmarks da mão, PyAutoGUI para emulação de eventos do mouse e streamlit-webrtc para transmissão de vídeo em tempo real sem piscar.

## ✨ Funcionalidades

- **Rastreamento do Cursor em Tempo Real**: Mapeamento da palma da mão (pulso) para movimento do cursor com suavização
- **Vídeo em Tempo Real sem Piscar**: Utiliza streamlit-webrtc para transmissão fluida de vídeo
- **Clique Simples**: Gesto de polegar + dedo médio com feedback visual
- **Clique Duplo**: Gesto de polegar + dedo indicador com debounce para evitar duplicação
- **Calibração de Sensibilidade**: Ajuste automático baseado na distância da mão à câmera
- **Interface Visual**: Feedback em tempo real com cores indicativas e landmarks desenhados
- **Controles Ajustáveis**: Slider de sensibilidade (0.5 a 3.0) e calibração on-demand
- **Imagem Espelhada**: Exibição em modo espelho para experiência mais natural
- **Status em Tempo Real**: Indicador visual de "Rastreando" ou "Pausado" no vídeo

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Webcam funcional
- Windows, macOS ou Linux

### Passos de Instalação

1. Clone o repositório:
```bash
git clone https://github.com/ricmed/mouse-control.git
cd mouse-control
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🎯 Como Usar

1. Execute a aplicação:
```bash
streamlit run main.py
```

2. A aplicação abrirá no navegador automaticamente.

3. Na sidebar:
   - Clique em **"▶️ Iniciar"** para começar o rastreamento
   - **IMPORTANTE**: Quando iniciar, você precisará clicar em **"Start"** no player de vídeo que aparecer
   - Permita o acesso à câmera quando solicitado pelo navegador
   - Ajuste a **Sensibilidade** conforme necessário
   - Clique em **"⚙️ Calibrar"** para calibrar a distância da mão

4. **Gestos:**
   - **Movimento do Cursor**: Mova a palma da mão na frente da câmera (o cursor segue o pulso/palma)
   - **Clique Simples**: Junte a ponta do polegar com a ponta do dedo médio
   - **Clique Duplo**: Junte a ponta do polegar com a ponta do dedo indicador

5. **Atalhos de Teclado:**
   - **P**: Pausar/Retomar rastreamento
   - **Q**: Sair da aplicação

## 🎨 Feedback Visual

- **Verde (#00FF88)**: Palma da mão (rastreamento ativo) - círculo destacado no pulso/palma. O dedo indicador também tem um círculo verde menor para referência visual
- **Azul (#0088FF)**: Gesto de clique simples detectado (polegar + dedo médio) - círculos e linha conectando
- **Amarelo (#FFAA00)**: Gesto de clique duplo detectado (polegar + dedo indicador) - círculos e linha conectando
- **Vermelho (#FF4444)**: Status pausado ou erro
- **Imagem Espelhada**: A imagem da webcam é exibida em modo espelho para melhor experiência natural

## ⚙️ Configurações

### Sensibilidade
Ajuste o slider de sensibilidade (0.5 a 3.0) para controlar a velocidade do movimento do cursor:
- Valores menores: Movimento mais lento e preciso
- Valores maiores: Movimento mais rápido e amplo

### Calibração
A calibração ajusta automaticamente o fator de escala baseado na distância da sua mão à câmera:
1. Posicione a mão a aproximadamente 30cm da câmera
2. Mantenha a mão aberta e visível
3. Clique em "Calibrar Agora"
4. O sistema calculará o fator de escala ideal

## 📁 Estrutura do Projeto

```
mouse-control/
├── main.py                 # Aplicação principal Streamlit com streamlit-webrtc
├── hand_tracker.py         # Módulo de rastreamento MediaPipe Hands
├── mouse_controller.py     # Módulo de controle do cursor e detecção de gestos
├── calibration.py          # Módulo de calibração de sensibilidade
├── utils.py                # Funções auxiliares (suavização, desenho, cálculos)
├── requirements.txt        # Dependências do projeto
├── .gitignore              # Arquivos a ignorar no Git
└── README.md               # Este arquivo
```

### Descrição dos Módulos

- **main.py**: Aplicação principal usando streamlit-webrtc para vídeo em tempo real. Gerencia a UI, estado da aplicação e integra todos os módulos.

- **hand_tracker.py**: Implementa o rastreamento de mão usando MediaPipe Hands. Processa frames e detecta landmarks (21 pontos) da mão.

- **mouse_controller.py**: Controla o movimento do cursor baseado na palma da mão (pulso) e detecta gestos de clique (simples e duplo). Implementa suavização com média móvel.

- **calibration.py**: Calcula fator de escala baseado na distância da mão à câmera usando landmarks de referência (pulso e base do dedo médio).

- **utils.py**: Funções auxiliares para cálculos de distância, suavização de coordenadas, desenho de landmarks e feedback visual de gestos.

## 🔧 Requisitos Técnicos

- **Python**: 3.12
- **Streamlit**: >=1.28.0
- **streamlit-webrtc**: Para vídeo em tempo real
- **OpenCV**: >=4.8.0
- **MediaPipe**: >=0.10.0
- **PyAutoGUI**: >=0.9.54
- **NumPy**: >=1.24.0
- **av**: Para processamento de vídeo (PyAV)

## 🐛 Solução de Problemas

### Webcam não detectada
- Verifique se a webcam está conectada e funcionando
- Certifique-se de que nenhum outro aplicativo está usando a webcam
- Clique em **"Start"** no player de vídeo após iniciar o rastreamento
- Permita o acesso à câmera quando solicitado pelo navegador
- Tente reiniciar a aplicação

### Vídeo não aparece ou está piscando
- Certifique-se de que o streamlit-webrtc está instalado corretamente
- Verifique se você clicou em **"Start"** no player de vídeo
- Tente atualizar a página do navegador
- Verifique se há erros no console do navegador (F12)

### Aviso "missing ScriptRunContext"
- Este aviso é normal e pode ser ignorado
- É um comportamento esperado do streamlit-webrtc quando roda em threads separadas
- Não afeta a funcionalidade da aplicação

### Movimento do cursor muito rápido/lento
- Ajuste o slider de sensibilidade na sidebar
- Execute a calibração novamente
- Verifique a distância da mão à câmera (ideal: ~30cm)

### Cliques não funcionam
- Certifique-se de que os dedos estão bem visíveis na câmera
- Verifique a iluminação do ambiente
- Tente aumentar a distância entre os dedos antes de juntá-los

### Performance baixa
- Feche outros aplicativos que possam estar usando a webcam
- Reduza a resolução da webcam no código (em `hand_tracker.py` - padrão: 640x480)
- Verifique se há processos pesados rodando em segundo plano
- O streamlit-webrtc processa vídeo em tempo real, então pode consumir mais recursos

### Movimento do cursor invertido
- A imagem é exibida em modo espelho (invertida horizontalmente)
- O movimento do cursor já está corrigido para corresponder à imagem espelhada
- Se ainda estiver invertido, verifique se não há configurações adicionais de espelhamento na webcam

## 📝 Notas Importantes

- **Failsafe do PyAutoGUI**: Mova o mouse para o canto superior esquerdo da tela para interromper ações automáticas
- **Primeira execução**: Pode ser mais lenta devido ao download do modelo MediaPipe
- **Iluminação**: Use boa iluminação e fundo contrastante para melhor precisão
- **Imagem espelhada**: A webcam é exibida em modo espelho para experiência mais natural
- **streamlit-webrtc**: Utiliza WebRTC para transmissão de vídeo em tempo real, eliminando o problema de piscar
- **Navegadores suportados**: Chrome, Firefox, Edge (navegadores modernos com suporte a WebRTC)
- **Permissões**: O navegador solicitará permissão para acessar a câmera - é necessário permitir

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## 📄 Licença

Este projeto é open-source e está disponível sob a licença MIT.

## 👥 Autores

Desenvolvido como parte do projeto MouseControl.

---

**Versão**: 1.0  
**Última atualização**: 12/2025

