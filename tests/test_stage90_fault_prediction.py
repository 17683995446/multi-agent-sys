"""
阶段90验收测试 - 智能故障预测与预防
"""

import pytest
from src.architecture.fault_prediction import (
    FaultType,
    PredictionConfidence,
    FaultPrediction,
    FaultPredictor,
    FaultPredictionService,
)


class TestFaultType:
    """测试故障类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert FaultType.HARDWARE.value == "hardware"
        assert FaultType.SOFTWARE.value == "software"
        assert FaultType.NETWORK.value == "network"
        assert FaultType.RESOURCE_EXHAUSTION.value == "resource_exhaustion"
        assert FaultType.CONFIGURATION.value == "configuration"

    def test_all_types(self):
        """测试所有类型"""
        types = list(FaultType)
        assert len(types) == 5


class TestPredictionConfidence:
    """测试预测置信度枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert PredictionConfidence.LOW.value == "low"
        assert PredictionConfidence.MEDIUM.value == "medium"
        assert PredictionConfidence.HIGH.value == "high"

    def test_all_confidences(self):
        """测试所有置信度"""
        confidences = list(PredictionConfidence)
        assert len(confidences) == 3


class TestFaultPrediction:
    """测试故障预测"""

    def test_default_creation(self):
        """测试默认创建"""
        pred = FaultPrediction()
        assert pred.prediction_id != ""
        assert pred.fault_type == FaultType.SOFTWARE
        assert pred.confidence == PredictionConfidence.MEDIUM
        assert pred.estimated_time == 0.0
        assert pred.description == ""
        assert pred.prevention_measures == []

    def test_custom_creation(self):
        """测试自定义创建"""
        pred = FaultPrediction(
            fault_type=FaultType.NETWORK,
            confidence=PredictionConfidence.HIGH,
            estimated_time=1700000000.0,
            description="网络延迟异常",
            prevention_measures=["检查网络连接", "增加带宽"],
        )
        assert pred.fault_type == FaultType.NETWORK
        assert pred.confidence == PredictionConfidence.HIGH
        assert pred.estimated_time == 1700000000.0
        assert pred.description == "网络延迟异常"
        assert len(pred.prevention_measures) == 2

    def test_prediction_id_unique(self):
        """测试预测ID唯一性"""
        p1 = FaultPrediction()
        p2 = FaultPrediction()
        assert p1.prediction_id != p2.prediction_id


class TestFaultPredictor:
    """测试故障预测器"""

    def test_initialization(self):
        """测试初始化"""
        predictor = FaultPredictor()
        assert len(predictor._predictions) == 0
        assert len(predictor._patterns) == 0

    def test_predict_healthy_system(self):
        """测试健康系统预测"""
        predictor = FaultPredictor()
        system_data = {
            "cpu_usage": 30.0,
            "memory_usage": 40.0,
            "error_rate": 1.0,
            "network_latency": 100.0,
            "disk_usage": 50.0,
            "config_changes": 2,
        }
        predictions = predictor.predict(system_data)
        assert predictions == []

    def test_predict_cpu_high(self):
        """测试CPU高使用率预测"""
        predictor = FaultPredictor()
        system_data = {"cpu_usage": 90.0}
        predictions = predictor.predict(system_data)
        assert len(predictions) >= 1
        assert any(p.fault_type == FaultType.RESOURCE_EXHAUSTION for p in predictions)

    def test_predict_memory_high(self):
        """测试内存高使用率预测"""
        predictor = FaultPredictor()
        system_data = {"memory_usage": 95.0}
        predictions = predictor.predict(system_data)
        assert len(predictions) >= 1
        assert any(p.fault_type == FaultType.RESOURCE_EXHAUSTION for p in predictions)

    def test_predict_error_rate_high(self):
        """测试错误率高预测"""
        predictor = FaultPredictor()
        system_data = {"error_rate": 10.0}
        predictions = predictor.predict(system_data)
        assert len(predictions) >= 1
        assert any(p.fault_type == FaultType.SOFTWARE for p in predictions)

    def test_predict_network_latency(self):
        """测试网络延迟高预测"""
        predictor = FaultPredictor()
        system_data = {"network_latency": 800.0}
        predictions = predictor.predict(system_data)
        assert len(predictions) >= 1
        assert any(p.fault_type == FaultType.NETWORK for p in predictions)

    def test_predict_disk_high(self):
        """测试磁盘高使用率预测"""
        predictor = FaultPredictor()
        system_data = {"disk_usage": 95.0}
        predictions = predictor.predict(system_data)
        assert len(predictions) >= 1
        assert any(p.fault_type == FaultType.HARDWARE for p in predictions)

    def test_predict_config_changes(self):
        """测试配置变更频繁预测"""
        predictor = FaultPredictor()
        system_data = {"config_changes": 15}
        predictions = predictor.predict(system_data)
        assert len(predictions) >= 1
        assert any(p.fault_type == FaultType.CONFIGURATION for p in predictions)

    def test_predict_multiple_issues(self):
        """测试多问题预测"""
        predictor = FaultPredictor()
        system_data = {
            "cpu_usage": 90.0,
            "memory_usage": 95.0,
            "error_rate": 10.0,
        }
        predictions = predictor.predict(system_data)
        assert len(predictions) >= 3

    def test_analyze_patterns(self):
        """测试分析模式"""
        predictor = FaultPredictor()
        system_data = {"cpu_usage": 85.0, "error_rate": 8.0}
        patterns = predictor._analyze_patterns(system_data)
        assert len(patterns) >= 2

    def test_analyze_patterns_healthy(self):
        """测试健康系统模式分析"""
        predictor = FaultPredictor()
        system_data = {"cpu_usage": 30.0, "memory_usage": 40.0}
        patterns = predictor._analyze_patterns(system_data)
        assert len(patterns) == 0

    def test_detect_anomalies(self):
        """测试检测异常"""
        predictor = FaultPredictor()
        patterns = [
            {"type": FaultType.RESOURCE_EXHAUSTION, "indicator": "cpu_high",
             "value": 90.0, "threshold": 80.0},
        ]
        anomalies = predictor._detect_anomalies({}, patterns)
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "medium"

    def test_detect_anomalies_high_severity(self):
        """测试检测高严重度异常"""
        predictor = FaultPredictor()
        patterns = [
            {"type": FaultType.RESOURCE_EXHAUSTION, "indicator": "cpu_high",
             "value": 130.0, "threshold": 80.0},
        ]
        anomalies = predictor._detect_anomalies({}, patterns)
        assert anomalies[0]["severity"] == "high"

    def test_calculate_probability(self):
        """测试计算概率"""
        predictor = FaultPredictor()
        anomalies = [
            {"type": FaultType.SOFTWARE, "indicator": "error_rate_high",
             "value": 10.0, "severity": "medium"},
        ]
        predictions = predictor._calculate_probability(anomalies, {})
        assert len(predictions) == 1
        assert predictions[0].confidence == PredictionConfidence.MEDIUM

    def test_calculate_probability_high(self):
        """测试高严重度概率计算"""
        predictor = FaultPredictor()
        anomalies = [
            {"type": FaultType.RESOURCE_EXHAUSTION, "indicator": "cpu_high",
             "value": 130.0, "severity": "high"},
        ]
        predictions = predictor._calculate_probability(anomalies, {})
        assert len(predictions) == 1
        assert predictions[0].confidence == PredictionConfidence.HIGH

    def test_generate_prevention_plan(self):
        """测试生成预防方案"""
        predictor = FaultPredictor()
        system_data = {"cpu_usage": 90.0, "error_rate": 10.0}
        predictions = predictor.predict(system_data)
        plan = predictor.generate_prevention_plan(predictions)
        assert "total_predictions" in plan
        assert "high_confidence_count" in plan
        assert "fault_type_summary" in plan
        assert "prevention_actions" in plan

    def test_generate_prevention_plan_empty(self):
        """测试空预测生成预防方案"""
        predictor = FaultPredictor()
        plan = predictor.generate_prevention_plan([])
        assert "message" in plan

    def test_predict_saves_predictions(self):
        """测试预测后保存结果"""
        predictor = FaultPredictor()
        system_data = {"cpu_usage": 90.0}
        predictions = predictor.predict(system_data)
        for pred in predictions:
            assert pred.prediction_id in predictor._predictions


class TestFaultPredictionService:
    """测试故障预测服务"""

    def test_initialization(self):
        """测试初始化"""
        service = FaultPredictionService()
        assert service.predictor is not None
        assert service._all_predictions == []

    def test_initialization_with_predictor(self):
        """测试使用自定义预测器初始化"""
        predictor = FaultPredictor()
        service = FaultPredictionService(predictor=predictor)
        assert service.predictor is predictor

    def test_predict(self):
        """测试执行预测"""
        service = FaultPredictionService()
        system_data = {"cpu_usage": 90.0}
        predictions = service.predict(system_data)
        assert len(predictions) >= 1

    def test_predict_accumulates(self):
        """测试预测结果累积"""
        service = FaultPredictionService()
        service.predict({"cpu_usage": 90.0})
        service.predict({"error_rate": 10.0})
        assert len(service._all_predictions) >= 2

    def test_get_predictions(self):
        """测试获取所有预测"""
        service = FaultPredictionService()
        service.predict({"cpu_usage": 90.0})
        service.predict({"error_rate": 10.0})
        all_preds = service.get_predictions()
        assert len(all_preds) >= 2

    def test_get_predictions_by_type(self):
        """测试按类型获取预测"""
        service = FaultPredictionService()
        service.predict({"cpu_usage": 90.0})
        service.predict({"error_rate": 10.0})
        resource_preds = service.get_predictions(FaultType.RESOURCE_EXHAUSTION)
        assert len(resource_preds) >= 1
        assert all(p.fault_type == FaultType.RESOURCE_EXHAUSTION for p in resource_preds)

    def test_get_predictions_no_match(self):
        """测试无匹配类型的预测"""
        service = FaultPredictionService()
        service.predict({"cpu_usage": 90.0})
        hardware_preds = service.get_predictions(FaultType.HARDWARE)
        assert hardware_preds == []

    def test_get_prevention_plan(self):
        """测试获取预防方案"""
        service = FaultPredictionService()
        service.predict({"cpu_usage": 90.0, "error_rate": 10.0})
        plan = service.get_prevention_plan()
        assert "total_predictions" in plan
        assert "prevention_actions" in plan

    def test_get_prevention_plan_empty(self):
        """测试空预测时获取预防方案"""
        service = FaultPredictionService()
        plan = service.get_prevention_plan()
        assert "message" in plan


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
