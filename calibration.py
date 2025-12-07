"""
Módulo para calibração de sensibilidade baseada na distância da mão à câmera.
"""
import streamlit as st
import utils
from typing import Optional, Tuple


def calculate_scale_factor(landmarks) -> Optional[float]:
    """
    Calcula o fator de escala baseado na distância entre landmarks de referência.
    
    Usa a distância entre o pulso (landmark 0) e a base do dedo médio (landmark 9)
    como referência para estimar a distância da mão à câmera.
    
    Args:
        landmarks: Objeto HandLandmarks do MediaPipe
    
    Returns:
        Fator de escala (float) ou None se não for possível calcular
    """
    if landmarks is None:
        return None
    
    try:
        # Landmarks de referência: pulso (0) e base do dedo médio (9)
        wrist = landmarks.landmark[0]
        middle_base = landmarks.landmark[9]
        
        # Calcula distância entre os landmarks
        distance = utils.calculate_distance(wrist, middle_base)
        
        if distance == 0 or distance == float('inf'):
            return None
        
        # Fator de escala base: distância de referência esperada (~0.15 em coordenadas normalizadas)
        # Quanto maior a distância entre pulso e base do dedo médio, mais próxima a mão está
        # Quanto menor a distância, mais longe a mão está
        reference_distance = 0.15  # Distância de referência para calibração
        
        # Calcula fator de escala (inverso da distância relativa)
        scale_factor = reference_distance / distance
        
        # Limita o fator de escala entre 0.5 e 2.0 para evitar valores extremos
        scale_factor = max(0.5, min(2.0, scale_factor))
        
        return scale_factor
    
    except Exception as e:
        st.error(f"Erro ao calcular fator de escala: {e}")
        return None


def show_calibration_modal():
    """
    Exibe modal de calibração com instruções.
    
    Returns:
        True se o usuário confirmou a calibração
    """
    with st.expander("⚙️ Calibração", expanded=True):
        st.info("""
        **Instruções de Calibração:**
        
        1. Posicione sua mão a aproximadamente **30cm da câmera**
        2. Mantenha a mão aberta e visível
        3. Clique no botão "Calibrar Agora" abaixo
        4. Mantenha a posição até ver a confirmação
        """)
        
        calibrate_button = st.button("🎯 Calibrar Agora", type="primary", width='stretch')
        
        return calibrate_button


def perform_calibration(landmarks) -> Tuple[bool, Optional[float]]:
    """
    Realiza a calibração e armazena o fator de escala.
    
    Args:
        landmarks: Objeto HandLandmarks do MediaPipe
    
    Returns:
        Tupla (sucesso, fator_escala)
    """
    if landmarks is None:
        st.warning("⚠️ Mão não detectada. Certifique-se de que sua mão está visível na câmera.")
        return False, None
    
    scale_factor = calculate_scale_factor(landmarks)
    
    if scale_factor is None:
        st.error("❌ Erro ao calcular fator de escala. Tente novamente.")
        return False, None
    
    # Armazena no session_state
    st.session_state.scale_factor = scale_factor
    
    st.success(f"✅ Calibração concluída! Fator de escala: {scale_factor:.2f}")
    st.info("💡 Dica: Ajuste a sensibilidade no slider se o movimento estiver muito rápido ou lento.")
    
    return True, scale_factor

