"""Tests for ValidateAcceleratorsUseCase."""

import pytest

from julee.hcd.entities.code_info import BoundedContextInfo, ClassInfo
from julee.supply_chain.entities.accelerator import Accelerator
from julee.supply_chain.infrastructure.repositories.memory.accelerator import (
    MemoryAcceleratorRepository,
)
from julee.hcd.infrastructure.repositories.memory.code_info import (
    MemoryCodeInfoRepository,
)
from julee.hcd.use_cases.queries.validate_accelerators import (
    ValidateAcceleratorsRequest,
    ValidateAcceleratorsUseCase,
)


class TestValidateAcceleratorsUseCase:
    """Test validating accelerators against code structure."""

    @pytest.fixture
    def accelerator_repo(self) -> MemoryAcceleratorRepository:
        """Create a fresh accelerator repository."""
        return MemoryAcceleratorRepository()

    @pytest.fixture
    def code_info_repo(self) -> MemoryCodeInfoRepository:
        """Create a fresh code info repository."""
        return MemoryCodeInfoRepository()

    @pytest.fixture
    def use_case(
        self,
        accelerator_repo: MemoryAcceleratorRepository,
        code_info_repo: MemoryCodeInfoRepository,
    ) -> ValidateAcceleratorsUseCase:
        """Create the use case with repositories."""
        return ValidateAcceleratorsUseCase(
            accelerator_repo=accelerator_repo,
            code_info_repo=code_info_repo,
        )

    @pytest.mark.asyncio
    async def test_all_accelerators_match(
        self,
        use_case: ValidateAcceleratorsUseCase,
        accelerator_repo: MemoryAcceleratorRepository,
        code_info_repo: MemoryCodeInfoRepository,
    ) -> None:
        """Test validation passes when all accelerators match code."""
        # Set up matching documented and discovered
        await accelerator_repo.save(Accelerator(slug="vocabulary", status="active"))
        await accelerator_repo.save(Accelerator(slug="compliance", status="beta"))

        await code_info_repo.save(
            BoundedContextInfo(
                slug="vocabulary",
                entities=[ClassInfo(name="Term")],
            )
        )
        await code_info_repo.save(
            BoundedContextInfo(
                slug="compliance",
                entities=[ClassInfo(name="Policy")],
            )
        )

        request = ValidateAcceleratorsRequest()
        response = await use_case.execute(request)

        assert response.is_valid
        assert len(response.issues) == 0
        assert set(response.matched_slugs) == {"vocabulary", "compliance"}
        assert set(response.documented_slugs) == {"vocabulary", "compliance"}
        assert set(response.discovered_slugs) == {"vocabulary", "compliance"}

    @pytest.mark.asyncio
    async def test_undocumented_bounded_context(
        self,
        use_case: ValidateAcceleratorsUseCase,
        accelerator_repo: MemoryAcceleratorRepository,
        code_info_repo: MemoryCodeInfoRepository,
    ) -> None:
        """Test detection of bounded context without documentation."""
        # Documented accelerator
        await accelerator_repo.save(Accelerator(slug="vocabulary", status="active"))

        # Both discovered, but only one documented
        await code_info_repo.save(
            BoundedContextInfo(
                slug="vocabulary",
                entities=[ClassInfo(name="Term")],
            )
        )
        await code_info_repo.save(
            BoundedContextInfo(
                slug="undocumented-context",
                entities=[ClassInfo(name="SomeEntity")],
                use_cases=[ClassInfo(name="SomeUseCase")],
            )
        )

        request = ValidateAcceleratorsRequest()
        response = await use_case.execute(request)

        assert not response.is_valid
        assert len(response.issues) == 1

        issue = response.issues[0]
        assert issue.slug == "undocumented-context"
        assert issue.issue_type == "undocumented"
        assert "exists in code" in issue.message
        assert "no define-accelerator" in issue.message

    @pytest.mark.asyncio
    async def test_documented_but_no_code(
        self,
        use_case: ValidateAcceleratorsUseCase,
        accelerator_repo: MemoryAcceleratorRepository,
        code_info_repo: MemoryCodeInfoRepository,
    ) -> None:
        """Test detection of documented accelerator with no code."""
        # Both documented, but only one has code
        await accelerator_repo.save(Accelerator(slug="vocabulary", status="active"))
        await accelerator_repo.save(Accelerator(slug="future-feature", status="future"))

        # Only vocabulary exists in code
        await code_info_repo.save(
            BoundedContextInfo(
                slug="vocabulary",
                entities=[ClassInfo(name="Term")],
            )
        )

        request = ValidateAcceleratorsRequest()
        response = await use_case.execute(request)

        assert not response.is_valid
        assert len(response.issues) == 1

        issue = response.issues[0]
        assert issue.slug == "future-feature"
        assert issue.issue_type == "no_code"
        assert "documented but has no" in issue.message

    @pytest.mark.asyncio
    async def test_multiple_issues(
        self,
        use_case: ValidateAcceleratorsUseCase,
        accelerator_repo: MemoryAcceleratorRepository,
        code_info_repo: MemoryCodeInfoRepository,
    ) -> None:
        """Test detection of multiple issues."""
        # Documented but no code
        await accelerator_repo.save(Accelerator(slug="docs-only", status="future"))

        # Code but no docs
        await code_info_repo.save(
            BoundedContextInfo(
                slug="code-only",
                entities=[ClassInfo(name="Entity")],
            )
        )

        request = ValidateAcceleratorsRequest()
        response = await use_case.execute(request)

        assert not response.is_valid
        assert len(response.issues) == 2
        assert response.matched_slugs == []

        issue_types = {i.issue_type for i in response.issues}
        assert issue_types == {"undocumented", "no_code"}

        issue_slugs = {i.slug for i in response.issues}
        assert issue_slugs == {"code-only", "docs-only"}

    @pytest.mark.asyncio
    async def test_empty_repositories(
        self,
        use_case: ValidateAcceleratorsUseCase,
    ) -> None:
        """Test validation with empty repositories."""
        request = ValidateAcceleratorsRequest()
        response = await use_case.execute(request)

        assert response.is_valid
        assert len(response.issues) == 0
        assert response.matched_slugs == []
        assert response.documented_slugs == []
        assert response.discovered_slugs == []

    @pytest.mark.asyncio
    async def test_issue_message_includes_summary(
        self,
        use_case: ValidateAcceleratorsUseCase,
        code_info_repo: MemoryCodeInfoRepository,
    ) -> None:
        """Test that undocumented issues include code summary."""
        await code_info_repo.save(
            BoundedContextInfo(
                slug="rich-context",
                entities=[
                    ClassInfo(name="Entity1"),
                    ClassInfo(name="Entity2"),
                ],
                use_cases=[ClassInfo(name="UseCase1")],
            )
        )

        request = ValidateAcceleratorsRequest()
        response = await use_case.execute(request)

        assert len(response.issues) == 1
        issue = response.issues[0]
        # Message should include the summary from BoundedContextInfo
        assert "2 entities" in issue.message
        assert "1 use cases" in issue.message

    @pytest.mark.asyncio
    async def test_sorted_output(
        self,
        use_case: ValidateAcceleratorsUseCase,
        accelerator_repo: MemoryAcceleratorRepository,
        code_info_repo: MemoryCodeInfoRepository,
    ) -> None:
        """Test that output lists are sorted alphabetically."""
        # Add in non-alphabetical order
        await accelerator_repo.save(Accelerator(slug="zebra"))
        await accelerator_repo.save(Accelerator(slug="alpha"))
        await accelerator_repo.save(Accelerator(slug="middle"))

        await code_info_repo.save(BoundedContextInfo(slug="zebra"))
        await code_info_repo.save(BoundedContextInfo(slug="alpha"))
        await code_info_repo.save(BoundedContextInfo(slug="middle"))

        request = ValidateAcceleratorsRequest()
        response = await use_case.execute(request)

        assert response.documented_slugs == ["alpha", "middle", "zebra"]
        assert response.discovered_slugs == ["alpha", "middle", "zebra"]
        assert response.matched_slugs == ["alpha", "middle", "zebra"]
