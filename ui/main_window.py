import sys
import json
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QCheckBox,QComboBox,QSpinBox
from capture import WindowCapture,find_window
from vision.detector import CandleDetector
from analysis.engine import AnalysisEngine
from ui.overlay import Overlay

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Quotex Vision AI Desktop'); self.resize(520,360); self.cfg=self._cfg(); self.cap=WindowCapture(); self.det=CandleDetector(self.cfg['min_candles'],self.cfg['max_candles'],2); self.eng=AnalysisEngine(); self.ov=Overlay(); self.running=False; self.vision=True; self.analysis=True; self.timer=QTimer(self); self.timer.timeout.connect(self.tick); self.build()
    def _cfg(self):
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            config_path = Path(sys._MEIPASS) / 'config.json'
        else:
            config_path = Path(__file__).resolve().parent.parent / 'config.json'

        if config_path.exists():
            return json.loads(config_path.read_text(encoding='utf-8'))

        return {
            'window_title_contains': 'Quotex',
            'capture_fps': 8,
            'overlay_opacity': 0.52,
            'min_candles': 10,
            'max_candles': 30,
            'min_body_width_px': 2,
            'chart_roi': {
                'left': 0.08,
                'top': 0.18,
                'right': 0.98,
                'bottom': 0.96
            },
            'signal': {
                'min_confidence': 0.66,
                'min_agreement': 0.70,
                'min_direction_edge': 0.12
            }
        }
    def build(self):
        root=QWidget(); lay=QVBoxLayout(root); lay.addWidget(QLabel('<b>QUOTEX VISION AI DESKTOP</b>')); self.status=QLabel('Open Quotex and press START'); lay.addWidget(self.status)
        row=QHBoxLayout(); a=QPushButton('START'); a.clicked.connect(self.start); b=QPushButton('STOP'); b.clicked.connect(self.stop); row.addWidget(a); row.addWidget(b); lay.addLayout(row)
        row2=QHBoxLayout(); v=QCheckBox('VISION BOXES'); v.setChecked(True); v.stateChanged.connect(lambda s:self._vision(bool(s))); an=QCheckBox('ANALYSIS'); an.setChecked(True); an.stateChanged.connect(lambda s:self._analysis(bool(s))); row2.addWidget(v); row2.addWidget(an); lay.addLayout(row2)
        row3=QHBoxLayout(); row3.addWidget(QLabel('Horizon')); self.h=QComboBox(); self.h.addItems(['30 seconds','60 seconds','120 seconds']); self.h.setCurrentIndex(1); row3.addWidget(self.h); row3.addWidget(QLabel('Min candles')); self.mc=QSpinBox(); self.mc.setRange(5,30); self.mc.setValue(self.cfg['min_candles']); row3.addWidget(self.mc); lay.addLayout(row3)
        self.detect=QLabel('Detection: waiting'); lay.addWidget(self.detect); self.signal=QLabel('Signal: NO EDGE'); self.signal.setStyleSheet('font-size:24px;font-weight:bold;'); lay.addWidget(self.signal); lay.addWidget(QLabel('The overlay is read-only and click-through.')); self.setCentralWidget(root)
    def _vision(self,s): self.vision=s; self.ov.setVisible(self.running and s)
    def _analysis(self,s): self.analysis=s
    def start(self): self.running=True; self.timer.start(max(60,int(1000/max(1,self.cfg['capture_fps'])))); self.ov.show()
    def stop(self): self.running=False; self.timer.stop(); self.ov.hide(); self.status.setText('Stopped')
    def tick(self):
        if not self.running:return
        hwnd=find_window(self.cfg['window_title_contains'])
        if not hwnd: self.status.setText('Quotex window not found'); return
        frame,rect=self.cap.capture(hwnd); r=self.cfg['chart_roi']; d=self.det.detect(frame,(r['left'],r['top'],r['right'],r['bottom'])); left,top,right,bottom=rect; self.ov.setGeometry(left,top,right-left,bottom-top)
        sig=None
        if self.analysis and d.usable:
            horizon=[30,60,120][self.h.currentIndex()]; sig=self.eng.analyze(d.candles,d.quality,horizon)
        boxes=[(int(c.body_left-left),int(c.body_top-top),max(2,int(c.body_right-c.body_left+1)),max(3,int(c.body_bottom-c.body_top+1))) for c in d.candles]
        label='SCAN' if sig is None else sig.label; pup=50 if sig is None else sig.up_probability*100; conf=0 if sig is None else sig.confidence; self.ov.set_data(boxes,label,pup,conf,f'{len(d.candles)} candles | {d.quality*100:.0f}% vision'); self.ov.setVisible(self.vision); self.detect.setText(d.message); self.signal.setText(f'Signal: {label}'); self.status.setText(f'Quotex detected | {len(d.candles)} candles | vision {d.quality*100:.0f}%')
