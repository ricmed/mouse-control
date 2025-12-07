"""
MouseControl - Aplicação Streamlit para controle do cursor via gestos manuais.
Usa streamlit-webrtc para vídeo em tempo real sem piscar.
"""
import streamlit as st
import cv2
import numpy as np
import time
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
from hand_tracker import HandTracker
from mouse_controller import MouseController
import calibration
import utils

# Configuração da página
st.set_page_config(
    page_title="MouseControl",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do session_state
if 'tracking' not in st.session_state:
    st.session_state.tracking = False

if 'sensitivity' not in st.session_state:
    st.session_state.sensitivity = 1.0

if 'scale_factor' not in st.session_state:
    st.session_state.scale_factor = 1.0

if 'last_double_click_time' not in st.session_state:
    st.session_state.last_double_click_time = 0.0

if 'position_history' not in st.session_state:
    st.session_state.position_history = []

if 'calibrating' not in st.session_state:
    st.session_state.calibrating = False

if 'hand_tracker' not in st.session_state:
    st.session_state.hand_tracker = HandTracker()

if 'mouse_controller' not in st.session_state:
    st.session_state.mouse_controller = MouseController()

if 'last_calibration_time' not in st.session_state:
    st.session_state.last_calibration_time = 0

if 'calibration_success' not in st.session_state:
    st.session_state.calibration_success = False

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00FF88;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        text-align: center;
    }
    .status-tracking {
        background-color: #00FF88;
        color: #000;
    }
    .status-paused {
        background-color: #FF4444;
        color: #FFF;
    }
</style>
""", unsafe_allow_html=True)


class VideoProcessor(VideoProcessorBase):
    """
    Processador de vídeo para streamlit-webrtc.
    Processa cada frame com MediaPipe e controla o mouse.
    """
    
    def __init__(self):
        super().__init__()
        # Não inicializa aqui - será feito no recv quando session_state estiver disponível
        self.hand_tracker = None
        self.mouse_controller = None
        # Cache do estado de tracking para evitar problemas de acesso ao session_state
        # Inicializa como True por padrão - será atualizado no primeiro frame
        self._tracking_cache = True
        self._last_state_check = 0
    
    def _ensure_initialized(self):
        """Garante que os componentes estão inicializados."""
        try:
            # Sempre tenta usar as instâncias do session_state primeiro
            if 'hand_tracker' in st.session_state:
                self.hand_tracker = st.session_state.hand_tracker
            else:
                if self.hand_tracker is None:
                    self.hand_tracker = HandTracker()
                    st.session_state.hand_tracker = self.hand_tracker
            
            if 'mouse_controller' in st.session_state:
                self.mouse_controller = st.session_state.mouse_controller
            else:
                if self.mouse_controller is None:
                    self.mouse_controller = MouseController()
                    st.session_state.mouse_controller = self.mouse_controller
        except:
            # Se session_state não estiver disponível, cria instâncias locais
            if self.hand_tracker is None:
                self.hand_tracker = HandTracker()
            if self.mouse_controller is None:
                self.mouse_controller = MouseController()
    
    def recv(self, frame):
        """
        Processa cada frame recebido.
        
        Args:
            frame: Frame de vídeo do streamlit-webrtc
        
        Returns:
            Frame processado e anotado
        """
        # Garante que os componentes estão inicializados
        self._ensure_initialized()
        
        # Tenta atualizar o cache de tracking logo no início (antes de processar)
        # Isso garante que temos o estado mais recente
        # Atualiza SEMPRE a cada frame para garantir que está sincronizado
        try:
            if hasattr(st, 'session_state') and st.session_state is not None:
                new_tracking = st.session_state.get('tracking', self._tracking_cache)
                self._tracking_cache = new_tracking
        except Exception:
            # Se não conseguir acessar, mantém o cache atual
            # Isso é esperado na thread do webrtc às vezes
            pass
        
        # Converte frame para array numpy (BGR)
        img = frame.to_ndarray(format="bgr24")
        
        # Redimensiona se necessário
        img = cv2.resize(img, (640, 480))
        
        # Inverte horizontalmente a imagem (espelho) para corresponder ao movimento
        img = cv2.flip(img, 1)
        
        # Processa frame com MediaPipe
        landmarks, annotated_frame = self.hand_tracker.process_frame(img)
        
        # Obtém estado atual do session_state
        # IMPORTANTE: streamlit-webrtc roda em thread separada, então precisa verificar sempre
        # Atualiza cache a cada frame para garantir sincronização máxima
        calibrating = False
        
        try:
            # Tenta acessar session_state a cada frame para máxima responsividade
            if hasattr(st, 'session_state') and st.session_state is not None:
                # Força atualização do cache de tracking
                new_tracking = st.session_state.get('tracking', self._tracking_cache)
                self._tracking_cache = new_tracking  # Sempre atualiza, mesmo se igual
                calibrating = st.session_state.get('calibrating', False)
        except Exception:
            # Se não conseguir acessar session_state, mantém valores em cache
            # Isso é esperado na thread do webrtc às vezes
            pass
        
        # Usa o cache atualizado
        tracking = self._tracking_cache
        
        if calibrating and landmarks is not None:
            current_time = time.time()
            last_calibration_time = st.session_state.get('last_calibration_time', 0)
            if current_time - last_calibration_time > 0.5:
                scale_factor = calibration.calculate_scale_factor(landmarks)
                if scale_factor is not None:
                    try:
                        st.session_state.scale_factor = scale_factor
                        st.session_state.calibrating = False
                        st.session_state.calibration_success = True
                        st.session_state.last_calibration_time = current_time
                    except:
                        pass
        
        # Desenha feedback visual e controla mouse
        if landmarks is not None:
            # Obtém landmarks específicos
            thumb = self.hand_tracker.get_landmark(landmarks, 4)
            middle = self.hand_tracker.get_landmark(landmarks, 12)
            index = self.hand_tracker.get_landmark(landmarks, 8)
            
            # Desenha feedback de gestos
            annotated_frame = utils.draw_gesture_feedback(
                annotated_frame,
                landmarks,
                thumb,
                middle,
                index,
                single_click_threshold=self.mouse_controller.single_click_threshold * 640,
                double_click_threshold=self.mouse_controller.double_click_threshold * 640
            )
            
            # Controla mouse apenas se tracking estiver ativo
            # Usa o cache do tracking (atualizado periodicamente)
            if tracking:
                # Move cursor - obtém valores do session_state de forma segura
                try:
                    sensitivity = st.session_state.get('sensitivity', 1.0)
                    scale_factor = st.session_state.get('scale_factor', 1.0)
                except:
                    sensitivity = 1.0
                    scale_factor = 1.0
                
                # Move o cursor - garante que mouse_controller está inicializado
                # Se não estiver inicializado, tenta inicializar novamente
                if self.mouse_controller is None:
                    self._ensure_initialized()
                
                if self.mouse_controller is not None:
                    try:
                        # Usa landmark 0 (pulso/palma da mão) para controlar o cursor
                        self.mouse_controller.move_cursor(
                            landmark_index=0,  # 0 = pulso/palma da mão
                            landmarks=landmarks,
                            sensitivity=sensitivity,
                            scale_factor=scale_factor
                        )
                        
                        # Detecta cliques
                        self.mouse_controller.detect_single_click(landmarks)
                        self.mouse_controller.detect_double_click(landmarks)
                    except Exception as e:
                        # Ignora erros silenciosamente para não interromper o processamento
                        pass
        
        # Adiciona texto de status no frame
        # Usa o cache do tracking para mostrar o status correto
        status_text = "Rastreando" if tracking else "Pausado"
        color_status = utils.COLOR_GREEN if tracking else utils.COLOR_RED
        cv2.putText(
            annotated_frame,
            f"Status: {status_text}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color_status,
            2
        )
        
        # Retorna frame processado
        return av.VideoFrame.from_ndarray(annotated_frame, format="bgr24")


# Sidebar
with st.sidebar:
    st.title("🎮 MouseControl")
    st.markdown("---")
    
    # Botão Iniciar/Pausar
    if st.button(
        "▶️ Iniciar" if not st.session_state.tracking else "⏸️ Pausar",
        type="primary",
        width='stretch'
    ):
        st.session_state.tracking = not st.session_state.tracking
        if not st.session_state.tracking:
            st.session_state.mouse_controller.reset()
        # Força rerun para atualizar o estado
        st.rerun()
    
    st.markdown("---")
    
    # Slider de sensibilidade
    st.session_state.sensitivity = st.slider(
        "🎚️ Sensibilidade",
        min_value=0.5,
        max_value=3.0,
        value=st.session_state.sensitivity,
        step=0.1,
        help="Ajuste a sensibilidade do movimento do cursor"
    )
    
    st.markdown("---")
    
    # Botão de calibração
    if st.button("⚙️ Calibrar", width='stretch'):
        st.session_state.calibrating = True
    
    # Modal de calibração
    if st.session_state.calibrating:
        with st.expander("⚙️ Calibração", expanded=True):
            st.info("""
            **Instruções de Calibração:**
            
            1. Posicione sua mão a aproximadamente **30cm da câmera**
            2. Mantenha a mão aberta e visível
            3. Clique no botão "Calibrar Agora" abaixo
            4. Mantenha a posição até ver a confirmação
            """)
            
            if st.button("🎯 Calibrar Agora", type="primary", width='stretch'):
                st.session_state.calibrating = True
                st.rerun()
            
            if st.button("❌ Cancelar", width='stretch'):
                st.session_state.calibrating = False
                st.rerun()
    
    st.markdown("---")
    
    # Badge de status
    status_text = "🟢 Rastreando" if st.session_state.tracking else "🔴 Pausado"
    status_class = "status-tracking" if st.session_state.tracking else "status-paused"
    st.markdown(f'<div class="status-badge {status_class}">{status_text}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Informações
    st.info("""
    **Atalhos de Teclado:**
    - **P** = Pausar/Retomar
    - **Q** = Sair
    
    **Gestos:**
    - **Movimento:** Mova o dedo indicador
    - **Clique Simples:** Junte polegar + dedo médio
    - **Clique Duplo:** Junte polegar + dedo indicador
    """)
    
    # Informações técnicas
    with st.expander("ℹ️ Informações Técnicas"):
        st.write(f"**Fator de Escala:** {st.session_state.scale_factor:.2f}")
        st.write(f"**Sensibilidade:** {st.session_state.sensitivity:.1f}")
        st.write(f"**Status:** {'Ativo' if st.session_state.tracking else 'Inativo'}")

# Área principal
st.markdown('<h1 class="main-header">🎮 MouseControl</h1>', unsafe_allow_html=True)

# Container para mensagens de calibração
calibration_message = st.empty()

# Mensagem inicial
if not st.session_state.tracking:
    st.info("👆 Clique em 'Iniciar' na sidebar para começar o rastreamento.")
    st.info("💡 **Nota:** Quando iniciar, você precisará permitir o acesso à câmera no navegador.")
else:
    # Exibe mensagem de calibração se necessário
    if st.session_state.calibrating:
        calibration_message.info("🔄 Calibrando... Mantenha sua mão visível na câmera.")
    
    # Configuração WebRTC (sem servidor STUN/TURN para uso local)
    rtc_configuration = RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )
    
    # Stream de vídeo usando streamlit-webrtc
    webrtc_ctx = webrtc_streamer(
        key="mouse-control",
        video_processor_factory=VideoProcessor,
        rtc_configuration=rtc_configuration,
        media_stream_constraints={"video": True, "audio": False},
    )
    
    # Verifica se o stream está ativo
    if webrtc_ctx.state.playing:
        st.success("✅ Câmera ativa! Mova sua mão para controlar o cursor.")
        
        # Mostra mensagem de calibração bem-sucedida se aplicável
        if 'calibration_success' in st.session_state and st.session_state.calibration_success:
            calibration_message.success(f"✅ Calibração concluída! Fator de escala: {st.session_state.scale_factor:.2f}")
            st.session_state.calibration_success = False
            time.sleep(2)
            calibration_message.empty()
    else:
        st.warning("⚠️ Aguardando acesso à câmera... Clique em 'Start' no player de vídeo acima.")

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>MouseControl v1.0 - Controle de cursor via gestos manuais</p>
        <p>Desenvolvido com Streamlit, MediaPipe, PyAutoGUI e streamlit-webrtc</p>
    </div>
    """,
    unsafe_allow_html=True
)
