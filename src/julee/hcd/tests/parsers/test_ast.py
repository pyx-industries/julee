"""Tests for AST parser."""

from pathlib import Path

from julee.hcd.parsers.ast import (
    parse_bounded_context,
    parse_module_docstring,
    parse_python_classes,
    scan_bounded_contexts,
)


class TestParsePythonClasses:
    """Test parse_python_classes function."""

    def test_parse_single_class(self, tmp_path: Path) -> None:
        """Test parsing a file with a single class."""
        py_file = tmp_path / "document.py"
        py_file.write_text(
            '''
class Document:
    """A document entity."""
    pass
'''
        )

        classes = parse_python_classes(tmp_path)
        assert len(classes) == 1
        assert classes[0].name == "Document"
        assert classes[0].docstring == "A document entity."
        assert classes[0].file == "document.py"

    def test_parse_multiple_classes(self, tmp_path: Path) -> None:
        """Test parsing a file with multiple classes."""
        py_file = tmp_path / "models.py"
        py_file.write_text(
            '''
class Document:
    """A document entity."""
    pass

class Term:
    """A term in a vocabulary."""
    pass
'''
        )

        classes = parse_python_classes(tmp_path)
        assert len(classes) == 2
        names = {c.name for c in classes}
        assert names == {"Document", "Term"}

    def test_parse_class_no_docstring(self, tmp_path: Path) -> None:
        """Test parsing a class without a docstring."""
        py_file = tmp_path / "simple.py"
        py_file.write_text(
            """
class SimpleClass:
    pass
"""
        )

        classes = parse_python_classes(tmp_path)
        assert len(classes) == 1
        assert classes[0].name == "SimpleClass"
        assert classes[0].docstring == ""

    def test_parse_multiline_docstring_extracts_first_line(
        self, tmp_path: Path
    ) -> None:
        """Test that only the first line of docstring is extracted."""
        py_file = tmp_path / "complex.py"
        py_file.write_text(
            '''
class ComplexClass:
    """First line of docstring.

    More detailed description here.
    With multiple lines.
    """
    pass
'''
        )

        classes = parse_python_classes(tmp_path)
        assert len(classes) == 1
        assert classes[0].docstring == "First line of docstring."

    def test_skip_private_files(self, tmp_path: Path) -> None:
        """Test that files starting with underscore are skipped."""
        (tmp_path / "_private.py").write_text("class Private: pass")
        (tmp_path / "__init__.py").write_text("class Init: pass")
        (tmp_path / "public.py").write_text("class Public: pass")

        classes = parse_python_classes(tmp_path)
        assert len(classes) == 1
        assert classes[0].name == "Public"

    def test_nonexistent_directory(self) -> None:
        """Test parsing nonexistent directory returns empty list."""
        classes = parse_python_classes(Path("/nonexistent/path"))
        assert classes == []

    def test_sorted_by_name(self, tmp_path: Path) -> None:
        """Test classes are sorted by name."""
        py_file = tmp_path / "classes.py"
        py_file.write_text(
            """
class Zebra: pass
class Apple: pass
class Mango: pass
"""
        )

        classes = parse_python_classes(tmp_path)
        names = [c.name for c in classes]
        assert names == ["Apple", "Mango", "Zebra"]

    def test_syntax_error_handled(self, tmp_path: Path) -> None:
        """Test that syntax errors are handled gracefully."""
        py_file = tmp_path / "broken.py"
        py_file.write_text("class Broken def invalid")  # Invalid syntax
        (tmp_path / "valid.py").write_text("class Valid: pass")

        classes = parse_python_classes(tmp_path)
        assert len(classes) == 1
        assert classes[0].name == "Valid"


class TestParseModuleDocstring:
    """Test parse_module_docstring function."""

    def test_parse_module_with_docstring(self, tmp_path: Path) -> None:
        """Test parsing a module with a docstring."""
        py_file = tmp_path / "module.py"
        py_file.write_text(
            '''"""Module docstring.

More details about the module.
"""

class SomeClass:
    pass
'''
        )

        first_line, full = parse_module_docstring(py_file)
        assert first_line == "Module docstring."
        assert "More details" in full

    def test_parse_module_no_docstring(self, tmp_path: Path) -> None:
        """Test parsing a module without a docstring."""
        py_file = tmp_path / "no_doc.py"
        py_file.write_text(
            """
class SomeClass:
    pass
"""
        )

        first_line, full = parse_module_docstring(py_file)
        assert first_line is None
        assert full is None

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing nonexistent file."""
        first_line, full = parse_module_docstring(Path("/nonexistent/file.py"))
        assert first_line is None
        assert full is None


class TestParseBoundedContext:
    """Test parse_bounded_context function."""

    def test_parse_full_context(self, tmp_path: Path) -> None:
        """Test parsing a complete bounded context structure."""
        # Create ADR 001-compliant structure
        context_dir = tmp_path / "vocabulary"
        (context_dir / "domain" / "models").mkdir(parents=True)
        (context_dir / "domain" / "repositories").mkdir(parents=True)
        (context_dir / "domain" / "services").mkdir(parents=True)
        (context_dir / "use_cases").mkdir(parents=True)
        (context_dir / "infrastructure").mkdir(parents=True)

        # Module docstring
        (context_dir / "__init__.py").write_text('"""Vocabulary management."""')

        # Entity
        (context_dir / "domain" / "models" / "vocabulary.py").write_text(
            '''
class Vocabulary:
    """A vocabulary catalog."""
    pass
'''
        )

        # Use case
        (context_dir / "use_cases" / "create.py").write_text(
            '''
class CreateVocabulary:
    """Create a new vocabulary."""
    pass
'''
        )

        # Repository protocol
        (context_dir / "domain" / "repositories" / "vocabulary.py").write_text(
            '''
class VocabularyRepository:
    """Repository for vocabularies."""
    pass
'''
        )

        info = parse_bounded_context(context_dir)
        assert info is not None
        assert info.slug == "vocabulary"
        assert info.objective == "Vocabulary management."
        assert len(info.entities) == 1
        assert info.entities[0].name == "Vocabulary"
        # CreateVocabulary doesn't end with UseCase suffix, so it won't be
        # categorized as a use case by the parser's doctrine-based filtering
        assert len(info.use_cases) == 0
        assert len(info.repository_protocols) == 1
        assert info.has_infrastructure is True
        assert info.code_dir == "vocabulary"

    def test_parse_minimal_context(self, tmp_path: Path) -> None:
        """Test parsing a minimal bounded context."""
        context_dir = tmp_path / "simple"
        context_dir.mkdir()
        (context_dir / "__init__.py").write_text("")

        info = parse_bounded_context(context_dir)
        assert info is not None
        assert info.slug == "simple"
        assert info.entities == []
        assert info.use_cases == []
        assert info.has_infrastructure is False

    def test_parse_nonexistent_context(self) -> None:
        """Test parsing nonexistent context returns None."""
        info = parse_bounded_context(Path("/nonexistent/context"))
        assert info is None


class TestScanBoundedContexts:
    """Test scan_bounded_contexts function."""

    def test_scan_multiple_contexts(self, tmp_path: Path) -> None:
        """Test scanning a directory with multiple contexts."""
        # Create two contexts
        for name in ["vocabulary", "traceability"]:
            context_dir = tmp_path / name
            context_dir.mkdir()
            (context_dir / "__init__.py").write_text(f'"""{name.title()} module."""')
            (context_dir / "domain" / "models").mkdir(parents=True)
            (context_dir / "domain" / "models" / "entity.py").write_text(
                f"class {name.title()}Entity: pass"
            )

        contexts = scan_bounded_contexts(tmp_path)
        assert len(contexts) == 2
        slugs = {c.slug for c in contexts}
        assert slugs == {"vocabulary", "traceability"}

    def test_scan_skips_hidden_directories(self, tmp_path: Path) -> None:
        """Test that hidden directories are skipped."""
        (tmp_path / ".hidden").mkdir()
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "_private").mkdir()
        visible = tmp_path / "visible"
        visible.mkdir()
        (visible / "__init__.py").write_text("")
        (visible / "domain").mkdir()  # Required for bounded context

        contexts = scan_bounded_contexts(tmp_path)
        assert len(contexts) == 1
        assert contexts[0].slug == "visible"

    def test_scan_skips_files(self, tmp_path: Path) -> None:
        """Test that files (not directories) are skipped."""
        (tmp_path / "file.py").write_text("x = 1")
        context_dir = tmp_path / "context"
        context_dir.mkdir()
        (context_dir / "__init__.py").write_text("")
        (context_dir / "domain").mkdir()  # Required for bounded context

        contexts = scan_bounded_contexts(tmp_path)
        assert len(contexts) == 1
        assert contexts[0].slug == "context"

    def test_scan_nonexistent_directory(self) -> None:
        """Test scanning nonexistent directory returns empty list."""
        contexts = scan_bounded_contexts(Path("/nonexistent/src"))
        assert contexts == []

    def test_scan_empty_directory(self, tmp_path: Path) -> None:
        """Test scanning empty directory returns empty list."""
        contexts = scan_bounded_contexts(tmp_path)
        assert contexts == []
