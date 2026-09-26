"""Tests for reading what kits claim and what a solution accepts."""

from pathlib import Path

import pytest

from julee.core.entities.claim import Claim, ClaimKind
from julee.core.entities.kit import Kit
from julee.core.semantics import (
    accepted_claims,
    claim_packages,
    kit_claims,
    load_semantics,
    names_bound_in,
    resolves_in,
    semantics_documents,
    solution_claims,
)

pytestmark = pytest.mark.unit

HCD_SEMANTICS = """
[[claim]]
id = "story-projects-usecase"
source = "julee_hcd.domain.models.story.Story"
kind = "projects"
target = "julee.core.entities.use_case.UseCase"
note = "The same event, told from outside."

[[claim]]
id = "story-part-of-app"
source = "julee_hcd.domain.models.story.Story"
kind = "part_of"
target = "julee_hcd.domain.models.app.App"
"""


def _write_solution(tmp_path: Path, **documents: str) -> Path:
    """A solution root with a semantics directory."""
    directory = tmp_path / "semantics"
    directory.mkdir()
    for name, text in documents.items():
        (directory / f"{name}.toml").write_text(text)
    return tmp_path


# =============================================================================
# What a solution says itself
# =============================================================================


def test_a_solution_with_no_semantics_directory_says_nothing(
    tmp_path: Path,
) -> None:
    """Most solutions never write one, and that is not an error."""
    assert solution_claims(tmp_path) == ()


def test_a_solution_declares_its_own_claims(tmp_path: Path) -> None:
    """A solution knows things about its own words that no kit does."""
    root = _write_solution(
        tmp_path,
        ours="""
[[claim]]
id = "segment-is-a-persona"
source = "acme.domain.models.CustomerSegment"
kind = "is_a"
target = "julee_hcd.domain.models.persona.Persona"
""",
    )

    claims = solution_claims(root)

    assert len(claims) == 1
    assert claims[0].kind is ClaimKind.IS_A
    assert claims[0].source == "acme.domain.models.CustomerSegment"


def test_several_documents_are_read_together(tmp_path: Path) -> None:
    """A solution may keep one file per kit it has an opinion about."""
    root = _write_solution(
        tmp_path,
        a='[[claim]]\nid = "one"\nsource = "a.A"\nkind = "is_a"\ntarget = "b.B"\n',
        b='[[claim]]\nid = "two"\nsource = "c.C"\nkind = "is_a"\ntarget = "d.D"\n',
    )

    assert {claim.id for claim in solution_claims(root)} == {"one", "two"}


def test_the_same_id_in_two_documents_is_an_error(tmp_path: Path) -> None:
    """Which one wins would otherwise depend on filename order."""
    root = _write_solution(
        tmp_path,
        a='[[claim]]\nid = "same"\nsource = "a.A"\nkind = "is_a"\ntarget = "b.B"\n',
        b='[[claim]]\nid = "same"\nsource = "c.C"\nkind = "is_a"\ntarget = "d.D"\n',
    )

    with pytest.raises(ValueError, match="already declares"):
        solution_claims(root)


def test_a_malformed_document_names_itself(tmp_path: Path) -> None:
    """Whoever has to fix it needs to know which file to open."""
    root = _write_solution(tmp_path, broken="[[claim]\nnot toml at all")

    with pytest.raises(ValueError, match="broken.toml"):
        solution_claims(root)


def test_a_claim_needs_both_ends(tmp_path: Path) -> None:
    """A claim with a blank end asserts nothing and cannot be checked."""
    root = _write_solution(
        tmp_path,
        bad='[[claim]]\nid = "x"\nsource = ""\nkind = "is_a"\ntarget = "b.B"\n',
    )

    with pytest.raises(ValueError):
        solution_claims(root)


def test_an_unknown_kind_is_refused(tmp_path: Path) -> None:
    """The vocabulary is five words; a sixth is a typo until it is not."""
    root = _write_solution(
        tmp_path,
        bad='[[claim]]\nid = "x"\nsource = "a.A"\nkind = "sort_of"\ntarget = "b.B"\n',
    )

    with pytest.raises(ValueError):
        solution_claims(root)


# =============================================================================
# What a solution accepts from a kit
# =============================================================================


@pytest.fixture
def hcd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Kit:
    """A kit publishing the two claims above."""
    package = tmp_path / "julee_hcd_stub"
    package.mkdir()
    (package / "semantics.toml").write_text(HCD_SEMANTICS)
    monkeypatch.setattr("julee.core.semantics.files", lambda _package: package)
    return Kit(slug="hcd", name="HCD", package="julee_hcd_stub")


def test_a_kit_publishes_what_it_claims(hcd: Kit) -> None:
    """Read as data; the kit's code is never imported."""
    claims = kit_claims(hcd)

    assert [claim.id for claim in claims] == [
        "story-projects-usecase",
        "story-part-of-app",
    ]


def test_a_note_survives_because_it_is_the_documentation(hcd: Kit) -> None:
    """The reason is the point; without it this is only configuration."""
    claims = kit_claims(hcd)

    assert claims[0].note == "The same event, told from outside."


def test_accepting_all_takes_everything_the_kit_claims(hcd: Kit) -> None:
    """The shorthand, for a solution that agrees with the kit."""
    assert len(accepted_claims(hcd, "all")) == 2


def test_accepting_none_takes_nothing(hcd: Kit) -> None:
    """Adopting a kit is not adopting its opinions about its neighbours."""
    assert accepted_claims(hcd, "none") == ()


def test_a_solution_may_take_only_the_claims_it_agrees_with(hcd: Kit) -> None:
    """Disagreeing with one claim should not cost you the others."""
    claims = accepted_claims(hcd, ["story-part-of-app"])

    assert [claim.id for claim in claims] == ["story-part-of-app"]


def test_accepting_a_claim_the_kit_does_not_make_is_an_error(hcd: Kit) -> None:
    """Otherwise a renamed claim silently disappears from the solution."""
    with pytest.raises(ValueError, match="does not claim"):
        accepted_claims(hcd, ["no-such-claim"])


def test_a_misspelt_acceptance_says_what_was_meant(hcd: Kit) -> None:
    """ "al" should not quietly mean "none"."""
    with pytest.raises(ValueError, match="say 'all', 'none'"):
        accepted_claims(hcd, "al")


def test_a_kit_that_publishes_nothing_claims_nothing(tmp_path: Path) -> None:
    """Which is every kit today, and not an error."""
    assert kit_claims(Kit(slug="x", name="X", package="julee")) == ()


def test_claims_are_data_not_imports() -> None:
    """The guarantee that makes this safe: no end is ever imported."""
    claim = Claim(
        id="x",
        source="nothing.that.exists.Anywhere",
        kind=ClaimKind.IS_A,
        target="also.nothing.Here",
    )

    assert claim.source == "nothing.that.exists.Anywhere"


# =============================================================================
# What a solution ends up holding true
# =============================================================================


def test_a_solution_that_says_nothing_holds_nothing(tmp_path: Path, hcd: Kit) -> None:
    """Adopting a kit is not adopting its opinions: silence is not consent."""
    assert load_semantics(tmp_path, (hcd,)) == ()


def test_adopting_all_of_a_kit_takes_its_claims(tmp_path: Path, hcd: Kit) -> None:
    """The shorthand, for a solution that agrees with the kit."""
    root = _write_solution(tmp_path, map='[adopt]\nhcd = "all"\n')

    assert len(load_semantics(root, (hcd,))) == 2


def test_a_solution_can_take_part_of_a_kit_and_add_its_own(
    tmp_path: Path, hcd: Kit
) -> None:
    """The case the whole apparatus exists for."""
    root = _write_solution(
        tmp_path,
        map="""
[adopt]
hcd = ["story-part-of-app"]

[[claim]]
id = "segment-is-a-persona"
source = "acme.domain.models.CustomerSegment"
kind = "is_a"
target = "julee_hcd.domain.models.persona.Persona"
""",
    )

    claims = load_semantics(root, (hcd,))

    assert [claim.id for claim in claims] == [
        "story-part-of-app",
        "segment-is-a-persona",
    ]


def test_accepting_from_a_kit_the_solution_has_not_adopted_is_an_error(
    tmp_path: Path,
) -> None:
    """A map naming a kit nobody installed is a mistake, not a no-op."""
    root = _write_solution(tmp_path, map='[adopt]\nnobody = "all"\n')

    with pytest.raises(ValueError, match="does not adopt"):
        load_semantics(root, ())


def test_two_documents_disagreeing_about_a_kit_is_an_error(
    tmp_path: Path, hcd: Kit
) -> None:
    """Otherwise which one wins depends on filename order."""
    root = _write_solution(
        tmp_path,
        a='[adopt]\nhcd = "all"\n',
        b='[adopt]\nhcd = "none"\n',
    )

    with pytest.raises(ValueError, match="disagree about what to accept"):
        load_semantics(root, (hcd,))


def test_a_solution_may_not_reuse_an_id_a_kit_already_claims(
    tmp_path: Path, hcd: Kit
) -> None:
    """Overriding is done by not accepting, not by shadowing."""
    root = _write_solution(
        tmp_path,
        map="""
[adopt]
hcd = "all"

[[claim]]
id = "story-part-of-app"
source = "acme.Story"
kind = "part_of"
target = "acme.App"
""",
    )

    with pytest.raises(ValueError, match="claimed twice"):
        load_semantics(root, (hcd,))


def test_replacing_a_claim_means_declining_it_first(tmp_path: Path, hcd: Kit) -> None:
    """Which is the same test from the other side, and the intended way."""
    root = _write_solution(
        tmp_path,
        map="""
[adopt]
hcd = ["story-projects-usecase"]

[[claim]]
id = "story-part-of-app"
source = "acme.Story"
kind = "part_of"
target = "acme.App"
""",
    )

    claims = load_semantics(root, (hcd,))

    assert [claim.source for claim in claims] == [
        "julee_hcd.domain.models.story.Story",
        "acme.Story",
    ]


# =============================================================================
# Resolving a claim's end by reading, not importing (#269)
# =============================================================================


def a_package(root: Path, name: str, modules: dict[str, str] | None = None) -> Path:
    """A package directory publishing claims, with the modules named.

    A key of "domain/models/story.py" is what the dotted path
    "<name>.domain.models.story.<something>" has to map onto.
    """
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "semantics.toml").write_text("")
    for relative, source in (modules or {}).items():
        module = directory / relative
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text(source)
    return directory


class TestNamesBoundInSource:
    def test_a_class_is_bound(self) -> None:
        assert "Story" in names_bound_in("class Story:\n    pass\n")

    def test_a_function_is_bound(self) -> None:
        assert "derive" in names_bound_in("def derive():\n    pass\n")

    def test_an_assignment_is_bound(self) -> None:
        """A claim may name a type alias as readily as a class."""
        assert "Slug" in names_bound_in("Slug = str\n")

    def test_an_annotated_assignment_is_bound(self) -> None:
        assert "LIMIT" in names_bound_in("LIMIT: int = 5\n")

    def test_a_re_export_is_bound(self) -> None:
        """Naming a package's __init__ re-export is the ordinary way to
        write a claim, and importing resolved it before."""
        assert "Story" in names_bound_in("from .story import Story\n")

    def test_an_aliased_import_is_bound_by_its_alias(self) -> None:
        bound = names_bound_in("from .story import Story as Tale\n")

        assert "Tale" in bound
        assert "Story" not in bound

    def test_a_conditional_re_export_is_bound(self) -> None:
        """A name offered behind a try/except is still offered."""
        source = "try:\n    from .fast import Story\nexcept ImportError:\n    from .slow import Story\n"

        assert "Story" in names_bound_in(source)

    def test_a_name_bound_only_inside_a_class_is_not_module_level(self) -> None:
        """Otherwise a claim could name a method and read as resolved."""
        assert "helper" not in names_bound_in(
            "class Story:\n    def helper(self):\n        pass\n"
        )

    def test_unparseable_source_binds_nothing(self) -> None:
        """So a file doctrine cannot read objects rather than passes."""
        assert names_bound_in("class Story(:\n") == frozenset()


class TestResolvingAgainstTheTarget:
    def test_a_class_in_a_module_resolves(self, tmp_path: Path) -> None:
        """The case #269 is about: answered from the tree, with nothing
        installed and nothing imported."""
        package = a_package(
            tmp_path,
            "julee_hcd",
            {"domain/models/story.py": "class Story:\n    pass\n"},
        )

        assert resolves_in("julee_hcd.domain.models.story.Story", package)

    def test_a_class_that_is_not_there_does_not_resolve(self, tmp_path: Path) -> None:
        package = a_package(
            tmp_path,
            "julee_hcd",
            {"domain/models/story.py": "class Tale:\n    pass\n"},
        )

        assert not resolves_in("julee_hcd.domain.models.story.Story", package)

    def test_a_module_that_is_not_there_does_not_resolve(self, tmp_path: Path) -> None:
        package = a_package(tmp_path, "julee_hcd")

        assert not resolves_in("julee_hcd.domain.models.story.Story", package)

    def test_a_name_in_the_packages_own_init_resolves(self, tmp_path: Path) -> None:
        package = a_package(
            tmp_path, "julee_hcd", {"__init__.py": "class Story:\n    pass\n"}
        )

        assert resolves_in("julee_hcd.Story", package)

    def test_a_name_in_a_subpackages_init_resolves(self, tmp_path: Path) -> None:
        package = a_package(
            tmp_path,
            "julee_hcd",
            {"domain/__init__.py": "class Story:\n    pass\n"},
        )

        assert resolves_in("julee_hcd.domain.Story", package)

    def test_a_dotted_path_naming_a_module_resolves(self, tmp_path: Path) -> None:
        """As it would if the package were imported."""
        package = a_package(tmp_path, "julee_hcd", {"domain/story.py": ""})

        assert resolves_in("julee_hcd.domain.story", package)

    def test_the_package_alone_names_nothing(self, tmp_path: Path) -> None:
        package = a_package(tmp_path, "julee_hcd")

        assert not resolves_in("julee_hcd", package)


class TestFindingWhoPublishes:
    def test_a_publisher_is_found_by_the_directory_holding_its_document(
        self, tmp_path: Path
    ) -> None:
        package = a_package(tmp_path / "src", "julee_hcd")

        assert claim_packages(tmp_path) == {"julee_hcd": package}

    def test_an_installed_kits_claims_are_not_the_solutions_problem(
        self, tmp_path: Path
    ) -> None:
        """A .venv holds every dependency's semantics.toml."""
        a_package(tmp_path / ".venv" / "lib", "julee_hcd")

        assert claim_packages(tmp_path) == {}
        assert semantics_documents(tmp_path) == ()
