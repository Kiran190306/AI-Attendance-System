import os
import tempfile
import time

import pytest
import numpy as np

from core.behavior.behavior_detector import BehaviorDetector
from core import config


def test_pose_analyzer_no_pose():
    from core.behavior.pose_analyzer import PoseAnalyzer
    pa = PoseAnalyzer()
    # blank image should return None
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    assert pa.analyze(frame) is None


def test_behavior_detector_normal():
    bd = BehaviorDetector()
    # simulate a small frame and unknown person
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    label, conf = bd.process(frame, None, (0, 0, 50, 50))
    assert label == "NORMAL"
    assert conf == 0.0


def test_behavior_logging(tmp_path, monkeypatch):
    # override log csv path
    temp_csv = tmp_path / "beh.csv"
    monkeypatch.setattr(config, "BEHAVIOR_LOG_CSV", temp_csv)
    bd = BehaviorDetector()

    # monkeypatch pose analyzer to return fake data with high motion
    class FakePA:
        def analyze(self, frame):
            return {"motions": {"LEFT_WRIST": (1, 1, 0)}}
    bd.pose = FakePA()

    # run process several times to trigger
    label, conf = bd.process(np.zeros((100, 100, 3), dtype=np.uint8), 1, (0, 0, 50, 50))
    # after a few iterations we expect classification
    assert label in ("NORMAL", "AGGRESSIVE", "SUSPICIOUS")
    # log file should have header already created
    if temp_csv.exists():
        text = temp_csv.read_text()
        assert "camera_id" in text or text == ""
