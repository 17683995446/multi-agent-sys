"""
阶段93验收测试 - 单机稳定运行版本冻结
"""

import pytest
from src.architecture.stable_release import (
    ReleaseStatus,
    ReleaseNote,
    VersionFreezer,
    StableReleaseManager,
    StableReleaseService,
)


class TestReleaseStatus:
    """测试发布状态枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ReleaseStatus.DEVELOPMENT.value == "development"
        assert ReleaseStatus.CANDIDATE.value == "candidate"
        assert ReleaseStatus.FROZEN.value == "frozen"
        assert ReleaseStatus.RELEASED.value == "released"
        assert ReleaseStatus.HOTFIX.value == "hotfix"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(ReleaseStatus)
        assert len(statuses) == 5


class TestReleaseNote:
    """测试发布说明"""

    def test_default_creation(self):
        """测试默认创建"""
        note = ReleaseNote()
        assert note.release_id != ""
        assert note.version == "0.0.0"
        assert note.status == ReleaseStatus.DEVELOPMENT
        assert note.features == []
        assert note.bug_fixes == []
        assert note.breaking_changes == []
        assert note.dependencies == {}
        assert note.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        note = ReleaseNote(
            version="1.2.0",
            status=ReleaseStatus.FROZEN,
            features=["新功能A", "新功能B"],
            bug_fixes=["修复Bug1"],
            breaking_changes=["接口变更X"],
            dependencies={"numpy": "1.24.0"},
        )
        assert note.version == "1.2.0"
        assert note.status == ReleaseStatus.FROZEN
        assert len(note.features) == 2
        assert len(note.bug_fixes) == 1
        assert len(note.breaking_changes) == 1
        assert note.dependencies["numpy"] == "1.24.0"

    def test_release_id_unique(self):
        """测试发布ID唯一性"""
        n1 = ReleaseNote()
        n2 = ReleaseNote()
        assert n1.release_id != n2.release_id


class TestVersionFreezer:
    """测试版本冻结器"""

    def test_initialization(self):
        """测试初始化"""
        freezer = VersionFreezer()
        assert len(freezer._releases) == 0
        assert len(freezer._checksums) == 0

    def test_freeze_version_success(self):
        """测试成功冻结版本"""
        freezer = VersionFreezer()
        note = freezer.freeze_version(
            version="1.0.0",
            features=["功能A"],
            bug_fixes=["修复B"],
        )
        assert note.status == ReleaseStatus.FROZEN
        assert note.version == "1.0.0"
        assert note.release_id in freezer._releases

    def test_freeze_version_invalid_format(self):
        """测试无效版本号格式"""
        freezer = VersionFreezer()
        note = freezer.freeze_version(version="invalid")
        assert note.status == ReleaseStatus.DEVELOPMENT

    def test_freeze_version_too_many_breaking_changes(self):
        """测试过多破坏性变更"""
        freezer = VersionFreezer()
        note = freezer.freeze_version(
            version="1.0.0",
            breaking_changes=["变更1", "变更2", "变更3", "变更4"],
        )
        assert note.status == ReleaseStatus.DEVELOPMENT

    def test_freeze_version_zero_version(self):
        """测试0.0版本冻结（冒烟测试失败）"""
        freezer = VersionFreezer()
        note = freezer.freeze_version(version="0.0.1")
        assert note.status == ReleaseStatus.DEVELOPMENT

    def test_verify_stability_valid(self):
        """测试验证稳定性通过"""
        freezer = VersionFreezer()
        note = ReleaseNote(version="1.0.0", breaking_changes=["变更1"])
        assert freezer._verify_stability(note) is True

    def test_verify_stability_too_many_breaking(self):
        """测试验证稳定性失败（过多破坏性变更）"""
        freezer = VersionFreezer()
        note = ReleaseNote(
            version="1.0.0",
            breaking_changes=["变更1", "变更2", "变更3", "变更4"],
        )
        assert freezer._verify_stability(note) is False

    def test_verify_stability_bad_version(self):
        """测试验证稳定性失败（版本号格式）"""
        freezer = VersionFreezer()
        note = ReleaseNote(version="bad")
        assert freezer._verify_stability(note) is False

    def test_run_smoke_tests_pass(self):
        """测试冒烟测试通过"""
        freezer = VersionFreezer()
        note = ReleaseNote(version="1.0.0")
        assert freezer._run_smoke_tests(note) is True

    def test_run_smoke_tests_fail(self):
        """测试冒烟测试失败"""
        freezer = VersionFreezer()
        note = ReleaseNote(version="0.0.1")
        assert freezer._run_smoke_tests(note) is False

    def test_generate_checksum(self):
        """测试生成校验和"""
        freezer = VersionFreezer()
        note = ReleaseNote(version="1.0.0", features=["功能A"])
        checksum = freezer._generate_checksum(note)
        assert len(checksum) == 32
        assert checksum != ""

    def test_create_release_note(self):
        """测试创建发布说明"""
        freezer = VersionFreezer()
        note = freezer.freeze_version(
            version="1.0.0",
            features=["功能A"],
            bug_fixes=["修复B"],
        )
        release_note = freezer.create_release_note(note.release_id)
        assert "release_id" in release_note
        assert "version" in release_note
        assert "status" in release_note
        assert "features" in release_note
        assert "checksum" in release_note

    def test_create_release_note_not_found(self):
        """测试创建发布说明未找到"""
        freezer = VersionFreezer()
        result = freezer.create_release_note("non-existent-id")
        assert "message" in result


class TestStableReleaseManager:
    """测试稳定发布管理器"""

    def test_initialization(self):
        """测试初始化"""
        manager = StableReleaseManager()
        assert manager.freezer is not None

    def test_initialization_with_freezer(self):
        """测试使用自定义冻结器初始化"""
        freezer = VersionFreezer()
        manager = StableReleaseManager(freezer=freezer)
        assert manager.freezer is freezer

    def test_create_release(self):
        """测试创建发布"""
        manager = StableReleaseManager()
        note = manager.create_release(
            version="1.0.0",
            features=["功能A"],
        )
        assert note.version == "1.0.0"
        assert note.status == ReleaseStatus.FROZEN

    def test_promote_frozen_to_released(self):
        """测试提升冻结版本为已发布"""
        manager = StableReleaseManager()
        note = manager.create_release(version="1.0.0")
        promoted = manager.promote(note.release_id)
        assert promoted is not None
        assert promoted.status == ReleaseStatus.RELEASED

    def test_promote_candidate_to_frozen(self):
        """测试提升候选版本为冻结"""
        manager = StableReleaseManager()
        note = ReleaseNote(version="1.0.0", status=ReleaseStatus.CANDIDATE)
        manager.freezer._releases[note.release_id] = note
        promoted = manager.promote(note.release_id)
        assert promoted is not None
        assert promoted.status == ReleaseStatus.FROZEN

    def test_promote_not_found(self):
        """测试提升不存在的发布"""
        manager = StableReleaseManager()
        result = manager.promote("non-existent-id")
        assert result is None

    def test_get_release(self):
        """测试获取发布"""
        manager = StableReleaseManager()
        note = manager.create_release(version="1.0.0")
        fetched = manager.get_release(note.release_id)
        assert fetched is not None
        assert fetched.version == "1.0.0"

    def test_get_release_not_found(self):
        """测试获取不存在的发布"""
        manager = StableReleaseManager()
        result = manager.get_release("non-existent-id")
        assert result is None

    def test_list_releases(self):
        """测试列出所有发布"""
        manager = StableReleaseManager()
        manager.create_release(version="1.0.0")
        manager.create_release(version="1.1.0")
        releases = manager.list_releases()
        assert len(releases) >= 2

    def test_list_releases_by_status(self):
        """测试按状态列出发布"""
        manager = StableReleaseManager()
        manager.create_release(version="1.0.0")
        releases = manager.list_releases(status=ReleaseStatus.FROZEN)
        assert all(r.status == ReleaseStatus.FROZEN for r in releases)

    def test_create_hotfix(self):
        """测试创建热修复"""
        manager = StableReleaseManager()
        note = manager.create_hotfix(
            version="1.0.1",
            bug_fixes=["紧急修复安全漏洞"],
        )
        assert note.version == "1.0.1"
        assert note.status == ReleaseStatus.HOTFIX
        assert len(note.bug_fixes) == 1


class TestStableReleaseService:
    """测试单机稳定运行版本冻结服务"""

    def test_initialization(self):
        """测试初始化"""
        service = StableReleaseService()
        assert service.manager is not None

    def test_freeze(self):
        """测试冻结版本"""
        service = StableReleaseService()
        note = service.freeze(version="1.0.0", features=["功能A"])
        assert note.version == "1.0.0"
        assert note.status == ReleaseStatus.FROZEN

    def test_release(self):
        """测试发布版本"""
        service = StableReleaseService()
        note = service.freeze(version="1.0.0")
        released = service.release(note.release_id)
        assert released is not None
        assert released.status == ReleaseStatus.RELEASED

    def test_get_release(self):
        """测试获取发布信息"""
        service = StableReleaseService()
        note = service.freeze(version="1.0.0")
        fetched = service.get_release(note.release_id)
        assert fetched is not None

    def test_get_notes(self):
        """测试获取发布说明"""
        service = StableReleaseService()
        note = service.freeze(version="1.0.0", features=["功能A"])
        release_note = service.get_notes(note.release_id)
        assert "release_id" in release_note
        assert "version" in release_note

    def test_get_notes_not_found(self):
        """测试获取不存在的发布说明"""
        service = StableReleaseService()
        result = service.get_notes("non-existent-id")
        assert "message" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
