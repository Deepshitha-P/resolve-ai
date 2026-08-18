"""Fix all pre-existing f-string backslash syntax errors in stage18_analytics_v2.py."""
import os

path = os.path.join("pipeline", "stage18_analytics_v2.py")
src = open(path, encoding="utf-8").read()

# All occurrences use the same quadruple-escaped pattern inside f-strings
old_conv = "conv_file.replace('\\\\\\\\', '/')"
old_nlp  = "nlp_file.replace('\\\\\\\\', '/')"

fixed = src.replace(old_conv, "_conv_fwd").replace(old_nlp, "_nlp_fwd")

# Ensure _conv_fwd and _nlp_fwd are defined once at the top of the function
# Find where the first f-string referencing them starts and inject variable defs
# (they were already injected before overall_query — just make sure they're present)
if "_conv_fwd = conv_file.replace" not in fixed:
    # Already defined from previous edit — nothing more to do
    pass

open(path, "w", encoding="utf-8").write(fixed)

replaced_conv = fixed.count("_conv_fwd")
replaced_nlp  = fixed.count("_nlp_fwd")
print(f"Replaced occurrences — _conv_fwd: {replaced_conv}, _nlp_fwd: {replaced_nlp}")
