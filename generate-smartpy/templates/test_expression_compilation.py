import smartpy as sp

sp.add_expression_compilation_target("f", lambda x : x + 1)

sp.add_expression_compilation_target("x", 42)

sp.add_expression_compilation_target("y", ("a", [1, 2, 3]))
