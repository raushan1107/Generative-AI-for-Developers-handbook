"""Drill 04.4: check a Pydantic model against the rules of strict structured outputs
before you send it to the model.
Run:  python schema_lint.py business_enquiry:BusinessEnquiry"""
import importlib
import sys

import openai

# Keywords Azure OpenAI structured outputs does not support (check the docs for your model).
UNSUPPORTED = {
    "minLength", "maxLength", "pattern", "format",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "minItems", "maxItems", "uniqueItems", "contains",
    "patternProperties", "unevaluatedProperties", "propertyNames",
    "minProperties", "maxProperties", "unevaluatedItems",
}
MAX_PROPERTIES = 100
MAX_DEPTH = 5


def strict_schema(model):
    """The schema the SDK sends for this model (same as .parse() and pydantic_function_tool)."""
    return openai.pydantic_function_tool(model)["function"]["parameters"]


def lint(schema):
    problems, count = [], 0
    if "anyOf" in schema:
        problems.append("root: the root must be an object, not anyOf")

    defs = schema.get("$defs", {})

    def walk(node, path, depth, seen=()):
        nonlocal count
        if isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]", depth, seen)
            return
        if not isinstance(node, dict):
            return
        ref = node.get("$ref", "")
        if ref.startswith("#/$defs/"):                 # nested models are stored in $defs
            name = ref.rsplit("/", 1)[1]
            if name not in seen:                       # recursion is allowed; don't loop forever
                walk(defs.get(name, {}), path, depth, seen + (name,))
            return
        for key in sorted(UNSUPPORTED & node.keys()):
            problems.append(f"{path}: '{key}' is not supported; enforce it in a validator instead")
        if node.get("type") == "object" or "properties" in node:
            props = node.get("properties", {})
            count += len(props)
            if depth > MAX_DEPTH:
                problems.append(f"{path}: nested {depth} levels deep (max {MAX_DEPTH})")
            if node.get("additionalProperties") is not False:
                problems.append(f"{path}: additionalProperties must be false")
            missing = set(props) - set(node.get("required", []))
            if missing:
                problems.append(f"{path}: every field must be required (use Optional for 'may be null'): {sorted(missing)}")
            for name, sub in props.items():
                walk(sub, f"{path}.{name}", depth + 1, seen)
        for key in ("items", "anyOf"):
            if key in node:
                walk(node[key], f"{path}.{key}", depth, seen)

    walk(schema, "root", 1)
    if count > MAX_PROPERTIES:
        problems.append(f"root: {count} properties in total (max {MAX_PROPERTIES})")
    return problems


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "business_enquiry:BusinessEnquiry"
    module_name, class_name = target.split(":")
    model = getattr(importlib.import_module(module_name), class_name)
    found = lint(strict_schema(model))
    for p in found:
        print("PROBLEM", p)
    print(f"{class_name}: {'OK, ready for strict structured outputs' if not found else str(len(found)) + ' problem(s)'}")
    sys.exit(1 if found else 0)
