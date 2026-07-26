"""Code generation helpers for Crewspan repository bootstrap."""

from tools.codegen.domains import DOMAINS, DomainSpec, all_domains, get_domain
from tools.codegen.generate_api import generate_api_tree, print_generation_summary
from tools.codegen.generate_docs import generate_docs_tree
from tools.codegen.generate_infra import generate_infra_tree
from tools.codegen.generate_tests import generate_tests_tree
from tools.codegen.generate_web import generate_web_tree
from tools.codegen.generate_worker import generate_worker_tree

__all__ = [
    "DOMAINS",
    "DomainSpec",
    "all_domains",
    "generate_api_tree",
    "generate_docs_tree",
    "generate_infra_tree",
    "generate_tests_tree",
    "generate_web_tree",
    "generate_worker_tree",
    "get_domain",
    "print_generation_summary",
]
# history-note: evolutionary edit 7
