def build_react_prompt(ir_json: str) -> str:
    return f"""
You are a senior React engineer.
Convert the provided IRBundle JSON into a complete React component file in TypeScript.

Requirements:
- Output only TSX code, no markdown.
- Use Ant Design components for UI.
- Export default function `GeneratedApp()`.
- Code must compile cleanly with strict TypeScript (`tsc -b`) in a Vite React app.
- Avoid unused imports and unused variables.
- Do not use `App.message`. For notifications, use `message.useMessage()` and render `contextHolder`.
- Do not use a default `React` import.
- Do not annotate the component return type with `JSX.Element`.
- If style typing is needed, use `import type` from React (for example, `CSSProperties`).
- Handle nullable numeric state safely: copy to local `const` variables, guard for null/invalid values, and only perform arithmetic after narrowing.
- Build React state from `data_ir.state`.
- Build derived values from `data_ir.derived` (prefer `useMemo` where helpful).
- Implement event handlers from `behaviour_ir.events`.
- Respect component labels, bind, and onClick links from `component_ir.components`.
- Respect vertical/horizontal/grid hints from `layout_ir.layout`.
- Apply `component_ir.theme.primaryColor` and per-component styles where possible.
- Keep code readable and runnable.
- Do not add explanations.

IRBundle JSON:
{ir_json}
""".strip()
