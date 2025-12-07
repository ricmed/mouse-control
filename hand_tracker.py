"""
Módulo para rastreamento de mão usando MediaPipe Hands.
"""
import cv2
import mediapipe as mp
import streamlit as st
from typing import Optional, Tuple, Any
import numpy as np

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


@st.cache_resource
def get_hand_model():
    """
    Obtém o modelo MediaPipe Hands (cacheado pelo Streamlit).
    
    Returns:
        Objeto Hands do MediaPipe
    """
    return mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )


class HandTracker:
    """
    Classe para rastreamento de mão usando MediaPipe.
    """
    
    def __init__(self):
        """Inicializa o rastreador de mão."""
        self.hands = get_hand_model()
        self.frame_width = 640
        self.frame_height = 480
    
    def process_frame(self, frame) -> Tuple[Optional[Any], np.ndarray]:
        """
        Processa um frame e detecta landmarks da mão.
        
        Args:
            frame: Frame OpenCV (BGR)
        
        Returns:
            Tupla (landmarks, frame_anotado)
            - landmarks: Objeto HandLandmarks ou None se não detectado
            - frame_anotado: Frame com landmarks desenhados
        """
        # Redimensiona frame para 640x480
        frame_resized = cv2.resize(frame, (self.frame_width, self.frame_height))
        
        # Converte BGR para RGB (MediaPipe requer RGB)
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        
        # Processa frame
        results = self.hands.process(frame_rgb)
        
        # Frame anotado (começa com o frame original)
        annotated_frame = frame_resized.copy()
        
        # Desenha landmarks se detectado
        if results.multi_hand_landmarks:
            # Pega a primeira mão detectada
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Desenha landmarks e conexões
            mp_drawing.draw_landmarks(
                annotated_frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            
            return hand_landmarks, annotated_frame
        else:
            return None, annotated_frame
    
    def get_landmark(self, landmarks, landmark_index: int):
        """
        Obtém um landmark específico.
        
        Args:
            landmarks: Objeto HandLandmarks
            landmark_index: Índice do landmark (0-20)
        
        Returns:
            Landmark ou None
        """
        if landmarks is None or landmark_index >= len(landmarks.landmark):
            return None
        return landmarks.landmark[landmark_index]
    
    def get_landmark_pixel_coords(self, landmark, frame_width: int, frame_height: int) -> Tuple[int, int]:
        """
        Converte coordenadas normalizadas do landmark para pixels.
        
        Args:
            landmark: Landmark do MediaPipe
            frame_width: Largura do frame
            frame_height: Altura do frame
        
        Returns:
            Tupla (x, y) em pixels
        """
        if landmark is None:
            return None, None
        
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        return x, y

