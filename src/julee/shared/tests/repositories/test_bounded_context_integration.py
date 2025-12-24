"""Integration tests for bounded context discovery against julee codebase."""

from pathlib import Path

import pytest

from julee.shared.repositories.introspection import FilesystemBoundedContextRepository

# Mark all tests as integration tests
pytestmark = pytest.mark.integration


class TestJuleeCodebaseDiscovery:
    """Integration tests verifying discovery against actual julee codebase."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get the julee project root."""
        # Navigate from this test file to project root
        # test_...py -> repositories -> tests -> shared -> julee -> src -> julee2
        # That's 6 parent directories
        return Path(__file__).parent.parent.parent.parent.parent.parent

    @pytest.fixture
    def repo(self, project_root: Path) -> FilesystemBoundedContextRepository:
        """Create repository for julee codebase."""
        return FilesystemBoundedContextRepository(project_root)

    @pytest.mark.asyncio
    async def test_discovers_expected_bounded_contexts(self, repo):
        """Should discover hcd, c4, ceap bounded contexts."""
        contexts = await repo.list_all()
        slugs = {c.slug for c in contexts}

        # These should always exist in julee
        assert "hcd" in slugs, "hcd bounded context should be discovered"
        assert "c4" in slugs, "c4 bounded context should be discovered"
        assert "ceap" in slugs, "ceap bounded context should be discovered"

    @pytest.mark.asyncio
    async def test_discovers_contrib_polling(self, repo):
        """Should discover polling in contrib/."""
        contexts = await repo.list_all()

        polling = next((c for c in contexts if c.slug == "polling"), None)
        assert polling is not None, "polling should be discovered"
        assert polling.is_contrib is True, "polling should be marked as contrib"

    @pytest.mark.asyncio
    async def test_viewpoints_marked_correctly(self, repo):
        """Should mark hcd and c4 as viewpoints."""
        contexts = await repo.list_all()

        hcd = next((c for c in contexts if c.slug == "hcd"), None)
        c4 = next((c for c in contexts if c.slug == "c4"), None)
        ceap = next((c for c in contexts if c.slug == "ceap"), None)

        assert hcd is not None and hcd.is_viewpoint is True
        assert c4 is not None and c4.is_viewpoint is True
        assert ceap is not None and ceap.is_viewpoint is False

    @pytest.mark.asyncio
    async def test_excludes_reserved_directories(self, repo):
        """Should not discover reserved directories as bounded contexts."""
        contexts = await repo.list_all()
        slugs = {c.slug for c in contexts}

        # These should never appear as bounded contexts
        reserved = {"shared", "util", "api", "repositories", "services", "workflows"}
        found_reserved = slugs & reserved

        assert not found_reserved, f"Reserved words found as BCs: {found_reserved}"

    @pytest.mark.asyncio
    async def test_hcd_has_expected_structure(self, repo):
        """HCD should have models, repositories, and use_cases."""
        hcd = await repo.get("hcd")

        assert hcd is not None
        assert hcd.markers.has_domain_models is True
        assert hcd.markers.has_domain_repositories is True
        assert hcd.markers.has_domain_use_cases is True

    @pytest.mark.asyncio
    async def test_c4_has_expected_structure(self, repo):
        """C4 should have models, repositories, and use_cases."""
        c4 = await repo.get("c4")

        assert c4 is not None
        assert c4.markers.has_domain_models is True
        assert c4.markers.has_domain_repositories is True
        assert c4.markers.has_domain_use_cases is True

    @pytest.mark.asyncio
    async def test_ceap_has_expected_structure(self, repo):
        """CEAP should have models, repositories, and use_cases."""
        ceap = await repo.get("ceap")

        assert ceap is not None
        assert ceap.markers.has_domain_models is True
        assert ceap.markers.has_domain_repositories is True
        assert ceap.markers.has_domain_use_cases is True

    @pytest.mark.asyncio
    async def test_import_paths_are_correct(self, repo):
        """Import paths should be valid Python module paths."""
        contexts = await repo.list_all()

        for ctx in contexts:
            # Should start with julee
            assert ctx.import_path.startswith(
                "julee."
            ), f"{ctx.slug} import_path should start with 'julee.': {ctx.import_path}"
            # Should not contain path separators
            assert "/" not in ctx.import_path
            assert "\\" not in ctx.import_path
