

FRONTEND_GUIDELINES.md
PDFextract — Canonical Frontend Guidelines
## 1. Document Purpose
This document defines exactly how the PDFextract frontend should look, feel, and behave
so the UI does not drift into random SaaS patterns, random AI styling, or invented product
features.
This file exists because frontend drift is one of the fastest ways AI-generated builds go
wrong. Without a locked frontend document, the system starts improvising:
- color palettes you never approved
- dashboard widgets that do not match the product
- navigation items tied to features that do not exist
- loading states that do not reflect actual backend behavior
- inconsistent components across pages
- fake “AI magic” interfaces instead of operational workflows
This document is the design system and UX behavior standard for the product. It defines:
- visual character
- design principles
- layout rules
- component rules
- spacing
- typography
- state styling
- page-level guidelines
- interaction rules
- accessibility requirements
- explicit anti-patterns
This document must be read together with:

- PRD.md
- APP_FLOW.md
- TECH_STACK.md
- BACKEND_STRUCTURE.md
- IMPLEMENTATION_PLAN.md
If generated frontend code conflicts with this document, the code is wrong.

- Frontend Role in the Product
The frontend is not the product’s intelligence layer. It is the product’s workflow layer.
PDFextract is a document-processing application. The frontend exists to help users do four
things clearly:
- authenticate
- upload PDFs
- track processing jobs
- download Excel outputs
That means the frontend should feel:
- operational
- calm
- trustworthy
- structured
- efficient
- readable
It should not feel:
- playful
- abstract
- futuristic for the sake of it
- overloaded with charts
- like a chatbot
- like a generic startup template

- like a low-trust drag-and-drop toy
The frontend must communicate control and clarity. The user should understand the
system at a glance.

## 3. Design Principles
These are the non-negotiable principles that govern every page and component.
## 3.1 Functional Before Decorative
Every visual choice must support usability. Styling is allowed, but decoration cannot
outrank clarity.
## 3.2 Trust Over Hype
PDFextract processes business documents. The UI should feel stable and credible, not
flashy or experimental.
## 3.3 One Clear Primary Action Per Screen
Every page should make the next step obvious. The user must never hunt for what to do
next.
## 3.4 System Status Must Be Visible
Because the backend is asynchronous, the UI must clearly show job status and progress
state.
## 3.5 Consistency Beats Creativity
Reusable patterns matter more than unique page art. The same status should always look
the same. The same button hierarchy should always mean the same thing.

## 3.6 Minimal Surface Area
No extra panels, cards, tabs, or widgets unless they directly support upload, tracking, or
download.
3.7 Readable at Speed
Users should be able to scan the app quickly. Information hierarchy must be strong
enough that key status, file names, and actions stand out immediately.

- Brand and Visual Character
The frontend should present PDFextract as a serious AI-enabled operations product, not a
consumer AI novelty app.
## 4.1 Personality
The visual personality should be:
- precise
- professional
- modern
- restrained
- structured
- slightly technical
- business-ready
## 4.2 Tone
The tone should feel like:
- document operations software
- finance-adjacent tooling
- enterprise-ready MVP
- human-readable backend transparency

## 4.3 What It Must Avoid
Do not make the product look like:
- a crypto dashboard
- a neon AI lab
- a gaming interface
- a social product
- a “vibe-coded” landing page
- an analytics platform stuffed with meaningless charts
## 4.4 Visual Direction
The overall visual direction should use:
- light surfaces
- crisp borders
- strong whitespace
- disciplined typography
- modest accent color usage
- clear status colors
- card-based content grouping
- gentle shadowing, not heavy glow

## 5. Color System
This product must not use random colors. The color system is locked.
## 5.1 Core Palette
## Base Colors
- Background: #F8FAFC
- Surface: #FFFFFF
- Surface Alt: #F1F5F9
- Border: #E2E8F0

- Border Strong: #CBD5E1
## Text Colors
- Text Primary: #0F172A
## • Text Secondary: #334155
- Text Muted: #64748B
- Text Inverse: #FFFFFF
## Primary Brand / Action Color
- Primary: #2563EB
- Primary Hover: #1D4ED8
- Primary Active: #1E40AF
- Primary Soft Background: #DBEAFE
## Status Colors
- Success: #16A34A
- Success Soft: #DCFCE7
- Warning: #D97706
- Warning Soft: #FEF3C7
- Error: #DC2626
- Error Soft: #FEE2E2
- Info: #0284C7
- Info Soft: #E0F2FE
## 5.2 Color Rules
- The primary blue is the main action color.
- Success, warning, and error colors are reserved for state communication.
- Do not use multiple accent colors competitively.
- Do not use purple-pink gradients, neon glows, or unrelated brand colors.
- Do not use green as the primary brand color because it would compete with
success state logic.
- Do not use red for decorative emphasis.

## 5.3 Background Rules
- App background uses #F8FAFC
- Cards and panels use white
- Input surfaces use white
- Subtle grouped sections may use #F1F5F9
- Dark mode is out of scope for MVP unless later approved

## 6. Typography
Typography must be clean, modern, and neutral.
## 6.1 Typeface
Use a single modern sans-serif system with strong web readability. The exact
implementation can use a Next.js-supported web font, but the visual intent must match:
- clean sans-serif
- high legibility
- neutral tone
- not overly geometric
- not decorative
Recommended visual standard:
- Primary font style: Inter-like sans-serif
## 6.2 Type Scale
- Display / Hero: 36px / 44px, semibold
- Page Title: 28px / 36px, semibold
- Section Title: 20px / 28px, semibold
- Card Title: 18px / 26px, semibold
- Body Large: 16px / 24px, regular
- Body Standard: 14px / 22px, regular
- Label / Meta: 13px / 20px, medium

- Small Meta: 12px / 18px, medium
## 6.3 Typography Rules
- Headings should be short and direct.
- Body text should avoid long paragraphs in the UI.
- Important data like file names, statuses, dates, and counts should be easy to scan.
- Never use ultra-light font weights.
- Never use oversized marketing typography for core app screens.

## 7. Spacing System
Spacing must be systematic. No arbitrary padding values.
## 7.1 Base Spacing Scale
Use an 8px-based spacing system:
## • 4
## • 8
## • 12
## • 16
## • 24
## • 32
## • 40
## • 48
## • 64
## 7.2 Component Padding Standards
- Small inline elements: 8–12px
- Inputs: 12–14px vertical, 14–16px horizontal
## • Cards: 20–24px
- Page sections: 24–32px between major blocks
- Page outer padding: 24px on desktop, 16px on mobile

## 7.3 Whitespace Rules
The app should breathe. Dense interfaces create anxiety in an async processing workflow.
Use enough whitespace to create hierarchy, but not so much that screens feel empty or
wasteful.

## 8. Layout System
The layout must feel like an operational workspace.
## 8.1 App Shell
The authenticated app should use a consistent shell with:
- top header
- primary navigation
- content container
- optional page actions region
## 8.2 Max Width
Primary page content should sit within a controlled content width:
- standard pages: around 1200px max width
- narrower content screens like login: 420px–480px
- job detail pages: allow structured width but do not stretch edge to edge
## 8.3 Grid Rules
Use simple responsive grid patterns:
- single column for narrow screens
- two-column layouts only when it helps comprehension
- dashboard cards can use 2–4 columns on desktop depending on density

- upload and detail pages should prioritize a main content column over aggressive
grid complexity
## 8.4 Alignment Rules
- Titles align left
- Action buttons align predictably near relevant content
- Card content aligns to a consistent baseline
- Avoid centered layout except on login or small empty states

- Borders, Radius, and Shadow
## 9.1 Radius
- Standard card radius: 12px
- Input radius: 10px
- Small chips/badges: 999px or pill style where appropriate
## 9.2 Borders
Use borders actively. They help this app feel structured and precise.
- Standard border: 1px solid #E2E8F0
- Strong border where needed: 1px solid #CBD5E1
## 9.3 Shadows
Use soft, low-contrast shadows only:
- light card shadow
- hover elevation shadow for interactive surfaces
- no glow effects
- no exaggerated floating panels


## 10. Core Component Rules
The component set must be small, reusable, and stable.
## 10.1 Buttons
## Button Types
- Primary Button: main call-to-action on a page
- Secondary Button: secondary action
- Tertiary / Ghost Button: low emphasis action
- Danger Button: destructive admin action only
## Button Rules
- Only one primary button should dominate a page section.
- Use primary for upload, continue, download, retry confirmation.
- Use secondary for navigation alternatives.
- Ghost buttons are for subtle actions like back, filter reset, or view details.
## Button Styling
- strong shape
- medium weight label
- no oversized rounded cartoon buttons
- no gradient primary buttons
## 10.2 Inputs
Inputs should be rectangular, clean, and quiet. They must prioritize legibility and
validation.
## States:
- default
- hover
- focus

- disabled
- error
Focus must be clearly visible with a clean ring or outline using the primary color family.
## 10.3 Upload Dropzone
This is a core component and must feel premium and clear.
It should include:
- upload icon or simple visual cue
- “drag and drop or browse” message
- accepted format note: PDF only
- strong hover and selected states
- inline validation errors
It must not look playful or oversimplified. This is a business tool entry point.
## 10.4 Status Badge
Status badges are critical. They must be consistent across dashboard, jobs list, and detail
pages.
Approved user-facing statuses:
## • Queued
## • Processing
## • Completed
## • Failed
Recommended badge styling:
- pill or rounded rectangle
- small icon optional
- colored text on soft background
- high contrast enough to scan fast

## 10.5 Data Table / Job List
The job list is one of the most important reusable components.
Each row should support:
- file name
- upload date
- document type if known
- status
- result availability
- click to detail
The table must prioritize clarity, not density. Avoid overstuffing it with filters, hidden
menus, or meaningless columns.
## 10.6 Stat Card
Used on dashboard only for core summaries such as:
- total recent jobs
- processing jobs
- completed jobs
- failed jobs
Stat cards must be simple. No chart mini-visuals unless explicitly approved later.
## 10.7 Timeline / Step Status
On job detail pages, a timeline or stage indicator should help the user understand
progress. It should look structured and calm, not animated like a loading toy.
## 10.8 Empty State
Empty states should always:
- explain the current absence clearly
- point to the next action

- avoid generic illustration clutter
## 10.9 Error State
Error states should:
- name the problem simply
- preserve user context
- provide next best action where available
- avoid technical stack traces for standard users.

## 11. Navigation Guidelines
The navigation must match APP_FLOW.md exactly.
## Allowed Primary Navigation
## • Dashboard
## • Upload
## • Jobs
- Admin (admin users only)
## Navigation Rules
- Keep nav labels short and literal
- Do not invent “Workspace,” “AI Center,” “Reports,” or “Automation Studio”
- Active route styling must be obvious
- Navigation should remain visible and stable across authenticated pages
## Header Rules
Header contains:
- product name or compact wordmark
- route context
- signed-in user indicator
- sign-out action

No clutter. No promotional banners. No onboarding carousel in the header.

- Page-Specific Guidelines
## 12.1 Login Page
The login page should be minimal, centered, and focused.
## Required:
- product name
- brief one-line purpose
- sign-in method
- loading state
- error state
## Avoid:
- large marketing sections
- testimonials
- feature walls
- side illustrations
- random split-screen creativity
## 12.2 Dashboard
The dashboard is not a general analytics screen. It is a workflow overview.
## Required:
- upload CTA
- recent jobs
- summary cards
- clearly visible job status
## Avoid:

- unrelated charts
- broad KPI walls
- trend graphs with no product relevance
## 12.3 Upload Page
This page is action-oriented and must feel high trust.
## Required:
- upload dropzone
- accepted format note
- selected file display
- upload button
- concise processing explanation
## Avoid:
- multiple competing upload modes
- unsupported file type hints
- wizard-style flow unless truly needed
## 12.4 Jobs Page
This page is a structured history list.
## Required:
- job list
- sortable or naturally ordered recent-first structure
- status visibility
- row click to detail
## Avoid:
- visual clutter
- dense admin-only metadata
- overcomplicated filters in MVP

## 12.5 Job Detail Page
This page is where trust is either reinforced or lost.
## Required:
- file name
- status
- timestamps
- stage/timeline summary
- download button when complete
- clear failure messaging when failed
## Avoid:
- fake progress percentages unless the backend actually supports them
- artificial AI confidence dials
- hidden output action
## 12.6 Admin Jobs Pages
Admin pages can be denser, but still must remain organized and readable.
## Required:
- stronger operational detail
- clear failure visibility
- retry controls
- distinction from user-facing views
## Avoid:
- raw console dump layout
- stack-trace-as-design
- ungrouped metadata walls


## 13. State Design
State design is one of the most important parts of this product.
## 13.1 Loading
Use loading states that reflect real waiting conditions:
- skeletons for page or card loading
- spinner only where compact inline waiting is needed
- progress language that explains what the system is doing
Do not use vague “AI is thinking...” copy.
## 13.2 Success
Success should be communicated clearly but calmly:
- file uploaded
- job created
- output ready
- download available
Avoid over-celebration animations.
## 13.3 Error
Error messaging should be:
- short
- clear
- actionable when possible
Examples of tone:
- “Upload failed. Please try again.”
- “This file could not be processed.”
- “Output is not available yet.”

## 13.4 Disabled
Disabled states must be visually obvious. Do not make inactive controls look clickable.

## 14. Interaction Guidelines
## 14.1 Upload Interaction
The upload flow should feel direct:
- select file
- validate
- submit
- transition to job detail
Do not create unnecessary multi-step upload wizards.
## 14.2 Polling / Refresh Behavior
Because processing is asynchronous, job detail and list pages may refresh status
periodically. The UI should make this feel natural, not jumpy.
## Use:
- stable layout during refresh
- badge/state updates without disruptive full-page flash
- subtle refresh indicators only where useful
## 14.3 Download Interaction
Download buttons should be highly visible only when the file truly exists. Never expose a
dead download action.

## 14.4 Retry Interaction
Retry is admin-only. It should require clear confirmation and then return the page to a job
status flow.

## 15. Accessibility Standards
Accessibility is required, not optional.
## 15.1 Contrast
All text and status elements must maintain readable contrast. Soft backgrounds are
allowed only when text remains clearly legible.
## 15.2 Keyboard Navigation
All major actions must be keyboard accessible:
- sign in
- upload
- job row selection
- download
- retry
- sign out
## 15.3 Focus Visibility
Interactive elements must show visible focus states. Never remove focus indicators
without providing an equally strong replacement.
## 15.4 Semantic Structure
Use proper heading hierarchy, labels, buttons, tables, and landmarks so assistive
technologies can understand page structure.

## 15.5 Status Communication
Status must not be communicated by color alone. Text labels are mandatory.

## 16. Responsive Design Rules
This product must remain usable on smaller screens, but it is primarily a desktop-oriented
operations tool in MVP.
## Desktop First, Mobile Safe
Design for desktop workflows first, then adapt cleanly for tablet and mobile widths.
## Responsive Behavior
- navigation collapses cleanly
- tables may stack or simplify intelligently
- key actions remain visible
- upload remains easy to use
- job status remains readable
## Avoid:
- squeezing dense tables into unreadable mobile layouts
- hiding key actions behind multiple taps unnecessarily

- Motion and Animation
Motion should be subtle and purposeful.
## Allowed:
- hover transitions
- fade-in for loaded content
- soft status transitions
- button press feedback

Not allowed:
- dramatic entrances
- bouncing cards
- animated gradients
- decorative motion loops
- meaningless micro-animations
This product should feel stable, not theatrical.

- Content and Microcopy
The written language in the frontend must match the product tone.
## 18.1 Voice
Use language that is:
- clear
- brief
- professional
- calm
- literal
## 18.2 Approved Style
Good examples:
- “Upload PDF”
- “Processing”
- “Download Excel”
- “Recent jobs”
- “This file is still being processed.”
Bad examples:
- “Watch the AI work its magic”

- “Your document journey starts here”
- “We’re cooking your data”
- “Sit tight while our smart engine vibes”
## 18.3 Labeling Rules
Use product language consistently:
## • PDF
## • Job
## • Processing
## • Completed
## • Failed
## • Download Excel
Do not randomly switch between “task,” “workflow,” “run,” and “pipeline” in user-facing
## UI.

- Explicit Anti-Patterns
These are forbidden unless the canonical docs change.
Do not generate:
- dark mode by default
- purple/pink AI gradients
- giant hero marketing sections inside the app
- crypto-style glassmorphism
- analytics dashboards unrelated to jobs
- chatbot panes
- “Ask AI” sidebars
- floating assistant widgets
- fake progress percentages
- editable extraction studio in MVP
- heavy charts
- random icons on every card

- decorative illustrations that reduce clarity
- multiple accent colors fighting each other
- overly rounded consumer-style controls
This product is an operational document tool, not a trend collage.

- Implementation Rules for Codex
Codex must treat these frontend rules as implementation constraints, not inspiration.
## Codex Must Do
- use consistent design tokens
- keep the component set small and reusable
- implement only approved pages from APP_FLOW.md
- reflect real backend state only
- preserve one clear primary action per page
- keep status styling consistent
- prefer calm, structured, high-trust UI
## Codex Must Not Do
- invent pages
- invent features
- invent navigation items
- invent charts
- invent extra settings panels
- use random colors
- switch to a different styling philosophy mid-app
- expose backend internals in user-facing screens.


## 21. Final Frontend Definition
The frontend for PDFextract must look like a serious, modern, business-ready document
operations product. It must communicate trust, control, and clarity. Its job is not to
entertain. Its job is not to decorate AI. Its job is to make the upload → track → download
workflow obvious and dependable.
The final design language is:
- light and structured
- blue-accented, not multi-accented
- whitespace-driven
- card-based
- status-forward
- typography-led
- calm under async processing
- highly consistent across all pages
That is the official frontend standard.
