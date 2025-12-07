"""
Funções auxiliares para processamento de landmarks e suavização.
"""
import numpy as np
import cv2
from collections import deque
from typing import Tuple, Optional

# Cores do design system
COLOR_GREEN = (0, 255, 136)  # #00FF88 - Palma da mão, rastreamento ativo
COLOR_BLUE = (0, 136, 255)   # #0088FF - Clique simples
COLOR_YELLOW = (0, 170, 255) # #FFAA00 - Clique duplo
COLOR_RED = (68, 68, 255)    # #FF4444 - Erro/pausado
COLOR_GRAY = (72, 61, 45)    # #2D3748 - Fundo
COLOR_WHITE = (255, 255, 255)

# Landmarks importantes
LANDMARK_INDEX = 0   # Palma da mão (pulso) - usado para movimento do cursor
LANDMARK_INDEX_FINGER = 8   # Ponta do dedo indicador - usado para feedback visual
LANDMARK_THUMB = 4   # Ponta do polegar
LANDMARK_MIDDLE = 12 # Ponta do dedo médio
LANDMARK_WRIST = 0   # Pulso
LANDMARK_MIDDLE_BASE = 9  # Base do dedo médio


def calculate_distance(landmark1, landmark2) -> float:
    """
    Calcula a distância euclidiana entre dois landmarks.
    
    Args:
        landmark1: Primeiro landmark (x, y, z)
        landmark2: Segundo landmark (x, y, z)
    
    Returns:
        Distância euclidiana em pixels
    """
    if landmark1 is None or landmark2 is None:
        return float('inf')
    
    x1, y1 = landmark1.x, landmark1.y
    x2, y2 = landmark2.x, landmark2.y
    
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def smooth_coordinates(position_history: deque, window_size: int = 5) -> Optional[Tuple[float, float]]:
    """
    Aplica média móvel para suavizar coordenadas do cursor.
    
    Args:
        position_history: Deque com histórico de posições (x, y)
        window_size: Tamanho da janela para média móvel
    
    Returns:
        Tupla (x, y) suavizada ou None se histórico insuficiente
    """
    if len(position_history) < 2:
        return None
    
    # Usa os últimos window_size elementos ou todos se houver menos
    recent_positions = list(position_history)[-window_size:]
    
    if not recent_positions:
        return None
    
    x_coords = [pos[0] for pos in recent_positions if pos is not None]
    y_coords = [pos[1] for pos in recent_positions if pos is not None]
    
    if not x_coords or not y_coords:
        return None
    
    avg_x = np.mean(x_coords)
    avg_y = np.mean(y_coords)
    
    return (avg_x, avg_y)


def draw_landmarks(frame, landmarks, hand_connections, is_tracking: bool = True):
    """
    Desenha landmarks e conexões da mão no frame.
    
    Args:
        frame: Frame OpenCV
        landmarks: Lista de landmarks do MediaPipe
        hand_connections: Conexões entre landmarks
        is_tracking: Se está rastreando ativamente
    """
    if landmarks is None:
        return frame
    
    h, w = frame.shape[:2]
    color = COLOR_GREEN if is_tracking else COLOR_GRAY
    
    # Desenha conexões
    for connection in hand_connections:
        start_idx = connection[0]
        end_idx = connection[1]
        
        if start_idx < len(landmarks.landmark) and end_idx < len(landmarks.landmark):
            start_point = landmarks.landmark[start_idx]
            end_point = landmarks.landmark[end_idx]
            
            x1, y1 = int(start_point.x * w), int(start_point.y * h)
            x2, y2 = int(end_point.x * w), int(end_point.y * h)
            
            cv2.line(frame, (x1, y1), (x2, y2), color, 2)
    
    # Desenha pontos dos landmarks
    for landmark in landmarks.landmark:
        x, y = int(landmark.x * w), int(landmark.y * h)
        cv2.circle(frame, (x, y), 3, color, -1)
    
    return frame


def draw_gesture_feedback(frame, landmarks, thumb_landmark, middle_landmark, 
                         index_landmark, single_click_threshold: float = 30.0,
                         double_click_threshold: float = 30.0):
    """
    Desenha feedback visual quando gestos estão próximos do limiar.
    
    Args:
        frame: Frame OpenCV
        landmarks: Lista de landmarks do MediaPipe
        thumb_landmark: Landmark do polegar
        middle_landmark: Landmark do dedo médio
        index_landmark: Landmark do dedo indicador
        single_click_threshold: Limiar para clique simples
        double_click_threshold: Limiar para clique duplo
    """
    if landmarks is None:
        return frame
    
    h, w = frame.shape[:2]
    
    # IMPORTANTE: Como a imagem foi invertida antes do MediaPipe processar,
    # os landmarks estão nas coordenadas da imagem invertida.
    # Mas o frame que recebemos aqui já está na imagem invertida,
    # então as coordenadas dos landmarks devem corresponder diretamente.
    # No entanto, se houver problemas de alinhamento, pode ser necessário
    # inverter as coordenadas X. Vamos usar as coordenadas diretamente primeiro.
    
    # Clique simples: polegar + médio
    if thumb_landmark and middle_landmark:
        distance_single = calculate_distance(thumb_landmark, middle_landmark)
        threshold_visual = single_click_threshold * 1.5  # Mostra feedback antes do limiar
        
        if distance_single < threshold_visual:
            # Converte coordenadas normalizadas para pixels
            # IMPORTANTE: A imagem foi invertida antes do MediaPipe processar.
            # Os landmarks foram calculados na imagem invertida, mas o MediaPipe
            # desenha os landmarks corretamente nessa imagem invertida.
            # Para alinhar nossos círculos com os landmarks do MediaPipe,
            # precisamos inverter as coordenadas X ao desenhar.
            x1 = int((1.0 - thumb_landmark.x) * w)  # Inverte X para alinhar
            y1 = int(thumb_landmark.y * h)
            x2 = int((1.0 - middle_landmark.x) * w)  # Inverte X para alinhar
            y2 = int(middle_landmark.y * h)
            
            # Círculos nas pontas dos dedos (polegar e médio)
            cv2.circle(frame, (x1, y1), 10, COLOR_BLUE, 2)
            cv2.circle(frame, (x2, y2), 10, COLOR_BLUE, 2)
            
            # Linha conectando os dedos
            if distance_single < single_click_threshold:
                cv2.line(frame, (x1, y1), (x2, y2), COLOR_BLUE, 3)
            else:
                cv2.line(frame, (x1, y1), (x2, y2), COLOR_BLUE, 1)
    
    # Clique duplo: polegar + indicador
    if thumb_landmark and index_landmark:
        distance_double = calculate_distance(thumb_landmark, index_landmark)
        threshold_visual = double_click_threshold * 1.5
        
        if distance_double < threshold_visual:
            # Converte coordenadas normalizadas para pixels
            # Inverte X para corresponder à imagem invertida
            x1 = int((1.0 - thumb_landmark.x) * w)  # Inverte X
            y1 = int(thumb_landmark.y * h)
            x2 = int((1.0 - index_landmark.x) * w)  # Inverte X
            y2 = int(index_landmark.y * h)
            
            # Círculos nas pontas dos dedos (polegar e indicador)
            cv2.circle(frame, (x1, y1), 10, COLOR_YELLOW, 2)
            cv2.circle(frame, (x2, y2), 10, COLOR_YELLOW, 2)
            
            # Linha conectando os dedos
            if distance_double < double_click_threshold:
                cv2.line(frame, (x1, y1), (x2, y2), COLOR_YELLOW, 3)
            else:
                cv2.line(frame, (x1, y1), (x2, y2), COLOR_YELLOW, 1)
    
    # Destaque especial para o dedo indicador (feedback visual)
    if index_landmark:
        x = int((1.0 - index_landmark.x) * w)  # Inverte X
        y = int(index_landmark.y * h)
        cv2.circle(frame, (x, y), 12, COLOR_GREEN, 2)
    
    # Destaque para a palma da mão (usada para movimento do cursor)
    if landmarks is not None and len(landmarks.landmark) > 0:
        palm = landmarks.landmark[0]  # Landmark 0 = pulso/palma
        x = int((1.0 - palm.x) * w)  # Inverte X
        y = int(palm.y * h)
        cv2.circle(frame, (x, y), 15, COLOR_GREEN, 4)  # Círculo maior para a palma
    
    return frame

