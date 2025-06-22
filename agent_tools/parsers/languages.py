"""Language configuration for tree-sitter grammars."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LanguageConfig:
    """Configuration for a programming language."""
    
    name: str
    grammar_url: str
    grammar_repo: str
    node_types_to_include: Optional[List[str]] = None
    node_types_to_exclude: Optional[List[str]] = None
    file_extensions: Optional[List[str]] = None
    
    @property
    def repo_name(self) -> str:
        """Extract repository name from URL."""
        return self.grammar_repo.split("/")[-1]


# Language configurations
LANGUAGE_CONFIGS: Dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        name="python",
        grammar_url="https://github.com/tree-sitter/tree-sitter-python",
        grammar_repo="tree-sitter/tree-sitter-python",
        node_types_to_include=[
            "module", "class_definition", "function_definition",
            "decorated_definition", "if_statement", "for_statement",
            "while_statement", "try_statement", "with_statement",
            "import_statement", "import_from_statement", "assignment",
            "call", "binary_operator", "unary_operator", "comparison_operator",
            "list", "dictionary", "tuple", "set", "list_comprehension",
            "dictionary_comprehension", "generator_expression",
        ],
        file_extensions=[".py", ".pyw"],
    ),
    
    "javascript": LanguageConfig(
        name="javascript",
        grammar_url="https://github.com/tree-sitter/tree-sitter-javascript",
        grammar_repo="tree-sitter/tree-sitter-javascript",
        node_types_to_include=[
            "program", "function_declaration", "function_expression",
            "arrow_function", "class_declaration", "method_definition",
            "if_statement", "for_statement", "while_statement",
            "do_statement", "switch_statement", "try_statement",
            "variable_declaration", "assignment_expression", "call_expression",
            "member_expression", "array", "object", "template_string",
            "import_statement", "export_statement",
        ],
        file_extensions=[".js", ".jsx", ".mjs"],
    ),
    
    "typescript": LanguageConfig(
        name="typescript",
        grammar_url="https://github.com/tree-sitter/tree-sitter-typescript",
        grammar_repo="tree-sitter/tree-sitter-typescript",
        node_types_to_include=[
            "program", "function_declaration", "function_expression",
            "arrow_function", "class_declaration", "method_definition",
            "interface_declaration", "type_alias_declaration",
            "enum_declaration", "if_statement", "for_statement",
            "while_statement", "switch_statement", "try_statement",
            "variable_declaration", "assignment_expression", "call_expression",
            "type_annotation", "generic_type", "union_type", "intersection_type",
        ],
        file_extensions=[".ts", ".tsx"],
    ),
    
    "go": LanguageConfig(
        name="go",
        grammar_url="https://github.com/tree-sitter/tree-sitter-go",
        grammar_repo="tree-sitter/tree-sitter-go",
        node_types_to_include=[
            "source_file", "package_clause", "import_declaration",
            "function_declaration", "method_declaration", "struct_type",
            "interface_type", "if_statement", "for_statement",
            "switch_statement", "select_statement", "go_statement",
            "defer_statement", "var_declaration", "const_declaration",
            "assignment_statement", "call_expression", "selector_expression",
            "composite_literal", "func_literal",
        ],
        file_extensions=[".go"],
    ),
    
    "cpp": LanguageConfig(
        name="cpp",
        grammar_url="https://github.com/tree-sitter/tree-sitter-cpp",
        grammar_repo="tree-sitter/tree-sitter-cpp",
        node_types_to_include=[
            "translation_unit", "function_definition", "class_specifier",
            "struct_specifier", "namespace_definition", "template_declaration",
            "if_statement", "for_statement", "while_statement",
            "switch_statement", "try_statement", "declaration",
            "assignment_expression", "call_expression", "field_expression",
            "lambda_expression", "new_expression", "delete_expression",
        ],
        file_extensions=[".cpp", ".cc", ".cxx", ".hpp", ".h", ".hxx"],
    ),
}


def get_language_config(language: str) -> Optional[LanguageConfig]:
    """Get configuration for a language."""
    return LANGUAGE_CONFIGS.get(language.lower())


def get_supported_languages() -> List[str]:
    """Get list of supported languages."""
    return list(LANGUAGE_CONFIGS.keys())


def get_language_by_extension(file_extension: str) -> Optional[str]:
    """Get language name by file extension."""
    ext = file_extension.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    
    for lang, config in LANGUAGE_CONFIGS.items():
        if config.file_extensions and ext in config.file_extensions:
            return lang
    
    return None