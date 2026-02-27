POLICY_NAME = "frontend-design"
POLICY_DESCRIPTION = (
    "Create distinctive, production-grade frontend interfaces with high design quality "
    "and avoid generic AI aesthetics."
)
POLICY_LICENSE = "Complete terms in LICENSE.txt"
POLICY_VERSION = "2026-02-26"

FRONTEND_DESIGN_POLICY = """
Common Rules for Professional UI

Icons & Visual Elements
- No emoji icons: use SVG icons (Heroicons, Lucide, Simple Icons).
- Stable hover states: use color/opacity transitions; avoid scale transforms that shift layout.
- Correct brand logos: verify official logos from trusted sources (for example, Simple Icons).
- Consistent icon sizing: use a fixed viewBox and consistent rendered sizes.

Interaction & Cursor
- Add pointer cursor to clickable/hoverable cards and controls.
- Provide clear hover feedback (color, shadow, border, opacity).
- Use smooth transitions, ideally 150-300ms, avoid instant or very slow transitions.

Light/Dark Mode Contrast
- Ensure glass cards remain visible in light mode (avoid excessive transparency).
- Ensure readable text contrast in light mode.
- Keep muted text readable and borders visible in all themes.

Layout & Spacing
- Floating navigation should have edge spacing.
- Account for fixed navbar height so content is not obscured.
- Keep container max-width consistent within a page.

Pre-Delivery Checklist
- No emojis used as icons.
- Icons come from one consistent icon set.
- Brand logos are correct.
- Hover states do not cause layout shifts.
- Clickable elements use cursor-pointer.
- Focus states are visible.
- Contrast is sufficient in light/dark themes.
- Responsive at 375, 768, 1024, 1440 widths.
- No horizontal mobile scroll.
- Inputs have labels and images have alt text.
- Color is not the only indicator.
- Respect prefers-reduced-motion.
""".strip()


def get_frontend_design_policy() -> str:
    return FRONTEND_DESIGN_POLICY
