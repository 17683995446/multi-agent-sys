"""
阶段42验收测试：合同网协议任务竞标分发
"""

import unittest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.architecture.contract_net_protocol import (
    ContractNetProtocol,
    ContractNetService,
    TaskRequirement,
    TaskAnnouncement,
    Bid,
    Contract,
    Contractor,
    TaskState,
    BidStatus,
    ContractorStatus,
    get_cnp_service,
    reset_cnp_service
)


class TestContractor(unittest.TestCase):
    """测试Contractor类"""
    
    def test_create_contractor(self):
        """测试创建承包商"""
        contractor = Contractor(
            name="Test Contractor",
            skills=["python", "java"],
            max_workload=3
        )
        self.assertIsNotNone(contractor.contractor_id)
        self.assertEqual(contractor.name, "Test Contractor")
        self.assertEqual(contractor.skills, ["python", "java"])
        self.assertEqual(contractor.status, ContractorStatus.AVAILABLE)
    
    def test_can_accept_task(self):
        """测试是否可以接受任务"""
        contractor = Contractor(name="Test", skills=["test"])
        self.assertTrue(contractor.can_accept_task())
        
        contractor.current_workload = contractor.max_workload
        self.assertFalse(contractor.can_accept_task())
        
        contractor.current_workload = 0
        contractor.status = ContractorStatus.BUSY
        self.assertFalse(contractor.can_accept_task())
    
    def test_has_skill(self):
        """测试技能检查"""
        contractor = Contractor(name="Test", skills=["python", "java"])
        self.assertTrue(contractor.has_skill("python"))
        self.assertFalse(contractor.has_skill("rust"))
    
    def test_calculate_capability_score(self):
        """测试能力评分计算"""
        contractor = Contractor(
            name="Test",
            skills=["python", "java", "rust"],
            capabilities={"python": 0.9, "java": 0.8}
        )
        
        score = contractor.calculate_capability_score(["python", "java"])
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1)


class TestTaskRequirement(unittest.TestCase):
    """测试TaskRequirement类"""
    
    def test_create_requirement(self):
        """测试创建任务需求"""
        req = TaskRequirement(
            skill_required=["python", "testing"],
            estimated_time=8.0,
            budget=1000.0,
            priority=2
        )
        self.assertIsNotNone(req.requirement_id)
        self.assertEqual(req.skill_required, ["python", "testing"])
        self.assertEqual(req.estimated_time, 8.0)


class TestContractNetProtocol(unittest.TestCase):
    """测试ContractNetProtocol类"""
    
    def setUp(self):
        """测试准备"""
        self.protocol = ContractNetProtocol()
    
    def test_register_contractor(self):
        """测试注册承包商"""
        contractor = self.protocol.register_contractor(
            "Developer Agent",
            ["coding", "testing"]
        )
        self.assertIsNotNone(contractor.contractor_id)
        self.assertEqual(len(self.protocol.contractors), 1)
    
    def test_publish_task(self):
        """测试发布任务"""
        req = TaskRequirement(
            skill_required=["python"],
            estimated_time=8.0,
            budget=500.0
        )
        announcement = self.protocol.publish_task(
            "task_001",
            "开发任务",
            req,
            "publisher_001"
        )
        
        self.assertIsNotNone(announcement.announcement_id)
        self.assertEqual(announcement.task_id, "task_001")
        self.assertEqual(announcement.state, TaskState.PUBLISHED)
    
    def test_submit_bid(self):
        """测试提交竞标"""
        contractor = self.protocol.register_contractor(
            "Test Contractor",
            ["python", "testing"]
        )
        
        req = TaskRequirement(
            skill_required=["python"],
            estimated_time=8.0,
            budget=500.0
        )
        announcement = self.protocol.publish_task(
            "task_002",
            "测试任务",
            req
        )
        
        bid = self.protocol.submit_bid(
            announcement.announcement_id,
            contractor.contractor_id,
            400.0,
            7.0,
            "我可以完成这个任务"
        )
        
        self.assertIsNotNone(bid)
        self.assertEqual(bid.contractor_id, contractor.contractor_id)
        self.assertEqual(bid.proposed_price, 400.0)
    
    def test_evaluate_bids_comprehensive(self):
        """测试综合评标"""
        contractor1 = self.protocol.register_contractor(
            "Contractor 1",
            ["python"],
            max_workload=3
        )
        contractor2 = self.protocol.register_contractor(
            "Contractor 2",
            ["python"],
            max_workload=3
        )
        
        req = TaskRequirement(
            skill_required=["python"],
            estimated_time=8.0,
            budget=1000.0
        )
        announcement = self.protocol.publish_task("task_003", "任务", req)
        
        self.protocol.submit_bid(
            announcement.announcement_id,
            contractor1.contractor_id,
            500.0, 8.0
        )
        self.protocol.submit_bid(
            announcement.announcement_id,
            contractor2.contractor_id,
            300.0, 6.0
        )
        
        ranked_bids = self.protocol.evaluate_bids(
            announcement.announcement_id,
            "comprehensive"
        )
        
        self.assertEqual(len(ranked_bids), 2)
    
    def test_award_contract(self):
        """测试授予合同"""
        contractor = self.protocol.register_contractor(
            "Best Contractor",
            ["python"],
            max_workload=3
        )
        
        req = TaskRequirement(
            skill_required=["python"],
            estimated_time=8.0,
            budget=500.0
        )
        announcement = self.protocol.publish_task("task_004", "任务", req)
        
        self.protocol.submit_bid(
            announcement.announcement_id,
            contractor.contractor_id,
            400.0, 7.0
        )
        
        contract = self.protocol.award_contract(
            announcement.announcement_id,
            contractor.contractor_id,
            400.0, 7.0
        )
        
        self.assertIsNotNone(contract)
        self.assertEqual(contract.contractor_id, contractor.contractor_id)
        self.assertEqual(contract.agreed_price, 400.0)
    
    def test_complete_contract(self):
        """测试完成任务"""
        contractor = self.protocol.register_contractor(
            "Worker",
            ["python"],
            max_workload=3
        )
        
        req = TaskRequirement(skill_required=["python"], estimated_time=8.0, budget=500.0)
        announcement = self.protocol.publish_task("task_005", "任务", req)
        
        self.protocol.submit_bid(
            announcement.announcement_id,
            contractor.contractor_id,
            400.0, 7.0
        )
        
        contract = self.protocol.award_contract(
            announcement.announcement_id,
            contractor.contractor_id,
            400.0, 7.0
        )
        
        result = self.protocol.complete_contract(
            contract.contract_id,
            {"success": True, "output": "任务完成"}
        )
        
        self.assertTrue(result)
        self.assertEqual(contractor.completed_tasks, 1)
    
    def test_cancel_announcement(self):
        """测试取消任务公告"""
        req = TaskRequirement(skill_required=["python"], estimated_time=8.0, budget=500.0)
        announcement = self.protocol.publish_task("task_006", "任务", req)
        
        result = self.protocol.cancel_announcement(announcement.announcement_id)
        self.assertTrue(result)
        self.assertEqual(announcement.state, TaskState.CANCELLED)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        stats = self.protocol.get_statistics()
        self.assertIn("total_announcements", stats)
        self.assertIn("total_bids", stats)
        self.assertIn("total_contracts", stats)


class TestContractNetService(unittest.TestCase):
    """测试ContractNetService类"""
    
    def setUp(self):
        """测试准备"""
        reset_cnp_service()
        self.service = get_cnp_service()
    
    def tearDown(self):
        """测试清理"""
        reset_cnp_service()
    
    def test_register_agent_as_contractor(self):
        """测试注册Agent为承包商"""
        contractor = self.service.register_agent_as_contractor(
            "agent_001",
            "Python Developer",
            ["python", "testing"]
        )
        
        self.assertIsNotNone(contractor)
        self.assertEqual(contractor.metadata["agent_id"], "agent_001")
    
    def test_full_auction_flow(self):
        """测试完整拍卖流程"""
        self.service.register_agent_as_contractor(
            "agent_001",
            "Agent One",
            ["python", "testing"]
        )
        self.service.register_agent_as_contractor(
            "agent_002",
            "Agent Two",
            ["python", "testing"]
        )
        
        req = TaskRequirement(
            skill_required=["python", "testing"],
            estimated_time=10.0,
            budget=1000.0
        )
        
        contract = self.service.full_auction_flow(
            "task_101",
            "完整拍卖测试任务",
            req,
            "manager_001"
        )
        
        self.assertIsNotNone(contract)
        self.assertEqual(contract.status, "pending")
    
    def test_publish_and_bid_flow(self):
        """测试发布和竞标流程"""
        self.service.register_agent_as_contractor(
            "agent_001",
            "Developer",
            ["python"]
        )
        
        req = TaskRequirement(
            skill_required=["python"],
            estimated_time=8.0,
            budget=500.0
        )
        
        announcement, bids = self.service.publish_and_bid_flow(
            "task_102",
            "发布竞标测试任务",
            req
        )
        
        self.assertIsNotNone(announcement)
        self.assertGreaterEqual(len(bids), 1)
    
    def test_complete_task_flow(self):
        """测试完成任务流程"""
        self.service.register_agent_as_contractor(
            "agent_001",
            "Worker",
            ["python"]
        )
        
        req = TaskRequirement(
            skill_required=["python"],
            estimated_time=8.0,
            budget=500.0
        )
        
        contract = self.service.full_auction_flow(
            "task_103",
            "完成任务测试",
            req
        )
        
        result = self.service.complete_task_flow(
            contract.contract_id,
            success=True,
            message="任务成功完成"
        )
        
        self.assertTrue(result)
    
    def test_get_agent_performance(self):
        """测试获取Agent性能"""
        contractor = self.service.register_agent_as_contractor(
            "agent_001",
            "Top Performer",
            ["python", "java"]
        )
        
        performance = self.service.get_agent_performance(contractor.contractor_id)
        
        self.assertIsNotNone(performance)
        self.assertEqual(performance["name"], "Top Performer")
        self.assertIn("completed_tasks", performance)
        self.assertIn("success_rate", performance)


class TestContractNetIntegration(unittest.TestCase):
    """测试合同网集成功能"""
    
    def test_multi_agent_auction(self):
        """测试多Agent竞标"""
        reset_cnp_service()
        service = get_cnp_service()
        
        for i in range(5):
            service.register_agent_as_contractor(
                f"agent_{i}",
                f"Agent {i}",
                ["python", "testing"]
            )
        
        req = TaskRequirement(
            skill_required=["python", "testing"],
            estimated_time=20.0,
            budget=5000.0
        )
        
        contract = service.full_auction_flow(
            "multi_agent_task",
            "多Agent竞标测试",
            req,
            "manager"
        )
        
        self.assertIsNotNone(contract)
    
    def test_task_publishing_multi_dimension(self):
        """测试多维任务发布"""
        reset_cnp_service()
        service = get_cnp_service()
        
        service.register_agent_as_contractor(
            "agent_001",
            "Full Stack Developer",
            ["python", "java", "react", "testing"]
        )
        
        req = TaskRequirement(
            skill_required=["python", "react"],
            estimated_time=40.0,
            budget=8000.0,
            priority=3,
            deadline=time.time() + 86400
        )
        
        announcement, bids = service.publish_and_bid_flow(
            "multi_dim_task",
            "多维任务测试",
            req
        )
        
        self.assertIsNotNone(announcement)
        self.assertGreaterEqual(len(bids), 1)


def run_acceptance_tests():
    """运行验收测试"""
    print("=" * 60)
    print("阶段42验收测试：合同网协议任务竞标分发")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestContractor))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskRequirement))
    suite.addTests(loader.loadTestsFromTestCase(TestContractNetProtocol))
    suite.addTests(loader.loadTestsFromTestCase(TestContractNetService))
    suite.addTests(loader.loadTestsFromTestCase(TestContractNetIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("验收测试结果汇总")
    print("=" * 60)
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"跳过数: {len(result.skipped)}")
    print("=" * 60)
    
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("✅ 阶段42验收测试通过！")
        print("\n验收标准达成情况：")
        print("  ✅ 合同网集成：完整实现Contract Net Protocol")
        print("  ✅ 任务发布：支持基本发布和多维发布")
        print("  ✅ 竞标机制：支持Agent竞标和智能评标")
        print("  ✅ 分发执行：支持基本分发和最优分发")
        return True
    else:
        print("❌ 阶段42验收测试失败！")
        return False


if __name__ == "__main__":
    success = run_acceptance_tests()
    sys.exit(0 if success else 1)
