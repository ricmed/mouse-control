"""
Módulo para controle do cursor do mouse e detecção de gestos.
"""
import pyautogui
import time
from collections import deque
import utils

# Limites de segurança do PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01  # Pequena pausa entre ações


class MouseController:
    """
    Classe para controle do cursor do mouse via gestos.
    """
    
    def __init__(self, smoothing_window: int = 5):
        """
        Inicializa o controlador de mouse.
        
        Args:
            smoothing_window: Tamanho da janela para suavização (média móvel)
        """
        self.smoothing_window = smoothing_window
        self.position_history = deque(maxlen=smoothing_window)
        self.last_double_click_time = 0.0
        self.double_click_debounce = 0.5  # 0.5 segundos entre cliques duplos
        
        # Limiares padrão (em pixels normalizados, será ajustado pela calibração)
        self.single_click_threshold = 0.05  # ~30px em frame 640x480
        self.double_click_threshold = 0.05
        
        # Estado do último clique
        self.last_single_click_state = False
        self.last_double_click_state = False
    
    def move_cursor(self, landmark_index, landmarks, sensitivity: float = 1.0, 
                   scale_factor: float = 1.0) -> bool:
        """
        Move o cursor do mouse baseado na posição da palma da mão.
        
        Args:
            landmark_index: Índice do landmark da palma (0 = pulso/palma)
            landmarks: Objeto HandLandmarks do MediaPipe
            sensitivity: Fator de sensibilidade (0.5 a 3.0)
            scale_factor: Fator de escala da calibração
        
        Returns:
            True se o cursor foi movido, False caso contrário
        """
        if landmarks is None or landmark_index >= len(landmarks.landmark):
            return False
        
        # Obtém coordenadas da palma da mão (landmark 0 = pulso, centro da palma)
        palm_landmark = landmarks.landmark[landmark_index]
        
        # Coordenadas normalizadas (0-1)
        # NOTA: A imagem já é invertida antes do processamento do MediaPipe (em main.py),
        # então os landmarks já estão nas coordenadas da imagem invertida que o usuário vê.
        # Portanto, NÃO precisamos inverter novamente aqui.
        x_norm = palm_landmark.x
        y_norm = palm_landmark.y
        
        # Mapeia uma área maior da webcam (80% central) para 100% da tela
        # Isso permite que o cursor chegue nas bordas da tela mesmo quando a mão
        # está próxima das bordas da webcam, sem precisar sair da área visível
        # Usa uma zona central de 80% que mapeia para 100% da tela
        margin = 0.1  # 10% de margem em cada lado
        x_norm = (x_norm - margin) / (1.0 - 2 * margin)
        y_norm = (y_norm - margin) / (1.0 - 2 * margin)
        
        # Aplica fator de escala e sensibilidade
        x_norm = (x_norm - 0.5) * scale_factor * sensitivity + 0.5
        y_norm = (y_norm - 0.5) * scale_factor * sensitivity + 0.5
        
        # Limita entre 0 e 1 (permite valores ligeiramente fora para chegar nas bordas)
        x_norm = max(0.0, min(1.0, x_norm))
        y_norm = max(0.0, min(1.0, y_norm))
        
        # Adiciona ao histórico para suavização
        self.position_history.append((x_norm, y_norm))
        
        # Aplica suavização
        smoothed = utils.smooth_coordinates(self.position_history, self.smoothing_window)
        
        if smoothed is None:
            return False
        
        x_smooth, y_smooth = smoothed
        
        # Obtém dimensões da tela
        screen_width, screen_height = pyautogui.size()
        
        # Converte para coordenadas de tela
        screen_x = int(x_smooth * screen_width)
        screen_y = int(y_smooth * screen_height)
        
        # Move o cursor
        try:
            pyautogui.moveTo(screen_x, screen_y, duration=0.0)
            return True
        except Exception as e:
            print(f"Erro ao mover cursor: {e}")
            return False
    
    def detect_single_click(self, landmarks) -> bool:
        """
        Detecta gesto de clique simples (polegar + dedo médio).
        
        Args:
            landmarks: Objeto HandLandmarks do MediaPipe
        
        Returns:
            True se o clique foi detectado e executado
        """
        if landmarks is None:
            return False
        
        # Landmarks: polegar (4) e dedo médio (12)
        thumb = landmarks.landmark[4]
        middle = landmarks.landmark[12]
        
        # Calcula distância
        distance = utils.calculate_distance(thumb, middle)
        
        # Verifica se está abaixo do limiar
        is_clicking = distance < self.single_click_threshold
        
        # Detecta transição de não-clicando para clicando
        if is_clicking and not self.last_single_click_state:
            try:
                pyautogui.click()
                self.last_single_click_state = True
                return True
            except Exception as e:
                print(f"Erro ao executar clique: {e}")
                return False
        elif not is_clicking:
            self.last_single_click_state = False
        
        return False
    
    def detect_double_click(self, landmarks) -> bool:
        """
        Detecta gesto de clique duplo (polegar + dedo indicador).
        
        Args:
            landmarks: Objeto HandLandmarks do MediaPipe
        
        Returns:
            True se o clique duplo foi detectado e executado
        """
        if landmarks is None:
            return False
        
        # Verifica debounce
        current_time = time.time()
        if current_time - self.last_double_click_time < self.double_click_debounce:
            return False
        
        # Landmarks: polegar (4) e dedo indicador (8)
        thumb = landmarks.landmark[4]
        index = landmarks.landmark[8]
        
        # Calcula distância
        distance = utils.calculate_distance(thumb, index)
        
        # Verifica se está abaixo do limiar
        is_clicking = distance < self.double_click_threshold
        
        # Detecta transição de não-clicando para clicando
        if is_clicking and not self.last_double_click_state:
            try:
                pyautogui.doubleClick()
                self.last_double_click_time = current_time
                self.last_double_click_state = True
                return True
            except Exception as e:
                print(f"Erro ao executar clique duplo: {e}")
                return False
        elif not is_clicking:
            self.last_double_click_state = False
        
        return False
    
    def set_click_thresholds(self, single: float, double: float):
        """
        Define os limiares de detecção de clique.
        
        Args:
            single: Limiar para clique simples (em coordenadas normalizadas)
            double: Limiar para clique duplo (em coordenadas normalizadas)
        """
        self.single_click_threshold = single
        self.double_click_threshold = double
    
    def reset(self):
        """Reseta o estado do controlador."""
        self.position_history.clear()
        self.last_single_click_state = False
        self.last_double_click_state = False
        self.last_double_click_time = 0.0

