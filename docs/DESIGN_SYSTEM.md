# JobPilot AI — Design System

This is a reusable productivity-SaaS system for future UI work; token values require visual approval before implementation.

| Token/component | Specification |
|---|---|
| Color | Neutral surfaces and text; one accessible primary action; semantic success, warning, danger, info tokens. Never convey state by color alone. **UNDEFINED:** exact palette/brand colors. |
| Typography | System sans-serif; clear page/title/body/label hierarchy; 16px minimum body text. **UNDEFINED:** approved font family. |
| Spacing/grid | 4px base unit; 8/12/16/24/32/48 scale; responsive 1-column mobile, bounded desktop content grid. |
| Cards/tables | Cards group job, draft, and activity detail; tables support dense scanning, responsive row-to-card fallback, empty/loading/error variants. |
| Buttons | Primary for one safe next action, secondary for alternatives, destructive only in confirmation. Disabled buttons state why. |
| Inputs/forms | Label, help text, validation message, required indicator, inline field error and submitted error summary. Preserve input on recoverable failure. |
| Badges/status | Text plus icon for Saved/Preparing/Ready for Review/Approved/Submitted/Interview/Rejected/Offer/Withdrawn/Unknown and activity states. |
| Dialogs | Focus-trapped, labelled, escape/cancel where safe; confirmation dialogs show target/effect/undo limitations. |
| Feedback states | Skeleton loading; explanatory empty state; recoverable error with retry; non-deceptive success. Agent states distinguish success, warning, paused, failed, waiting-for-user, completed. |

All components must meet the accessibility requirements in `UI_UX_SPEC.md`, reuse shared primitives, and avoid autonomous-looking confirmation language.
