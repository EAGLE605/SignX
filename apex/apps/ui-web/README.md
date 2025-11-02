# APEX UI Web - CalcuSign Frontend

React frontend application for the APEX mechanical engineering copilot, covering CalcuSign stages 1-8 with interactive canvas, file uploads, and PDF preview.

## Features

- **Project Management**: Create, list, and manage sign design projects
- **Persistent Stepper Navigation**: Non-linear navigation with progress tracking
- **Interactive 2D Canvas**: Konva.js-powered canvas with drag-resize and two-way binding
- **Stage-by-Stage Workflow**: 8 stages covering the complete design process
  - Overview
  - Site & Environmental
  - Cabinet Design
  - Structural Design
  - Foundation Design
  - Finalization & Pricing
  - Review
  - Submission
- **File Uploads**: Support for PDF, DWG, DXF, and image files
- **PDF Preview**: In-app PDF report preview and download
- **State Persistence**: LocalStorage-backed state management with Zustand
- **Responsive Design**: Mobile-friendly Material-UI components

## Tech Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for components
- **Konva.js** / **react-konva** for interactive canvas
- **Zustand** for state management
- **React Router** for navigation
- **Vite** for build tooling

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
cd apex/apps/ui-web
npm install
```

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000` with API proxy to `http://localhost:8000`.

### Build

```bash
npm run build
```

### Lint

```bash
npm run lint
npm run lint:fix
```

### Type Check

```bash
npm run typecheck
```

## Project Structure

```
src/
├── api/              # API client layer
│   └── client.ts
├── components/       # React components
│   ├── stages/      # Stage-specific components
│   ├── Layout.tsx
│   ├── ProjectList.tsx
│   ├── ProjectWorkspace.tsx
│   ├── StepperNavigation.tsx
│   ├── InteractiveCanvas.tsx
│   ├── FileUpload.tsx
│   └── PDFPreview.tsx
├── store/           # Zustand state management
│   └── projectStore.ts
├── types/           # TypeScript type definitions
│   └── api.ts
├── App.tsx
└── main.tsx
```

## Key Components

### InteractiveCanvas

2D interactive canvas using Konva.js with:
- Drag to move shapes
- Resize handles with constraints
- Two-way binding: Canvas changes sync to form inputs
- Form inputs sync to canvas (real-time updates)

### StepperNavigation

Persistent stepper showing:
- Current stage
- Completed stages
- Non-linear navigation (click any step to jump)
- Visual progress indicators

### ProjectWorkspace

Main workspace with:
- Tab-based stage navigation
- Persistent state across page refreshes
- Stage completion tracking
- Project data aggregation

## API Integration

The frontend communicates with the APEX API via:

- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/:id` - Get project
- `POST /signage/common/site/resolve` - Resolve address
- `POST /signage/common/cabinets/derive` - Calculate cabinet
- `POST /signage/common/poles/options` - Get pole options
- `POST /projects/:id/estimate` - Get pricing estimate

All API calls return standardized `ResponseEnvelope` format.

## State Management

State is managed with Zustand and persisted to localStorage:

- Current project ID
- Current stage
- Completed stages
- Canvas dimensions
- Project data (site, cabinet, structural, foundation, pricing)

## Environment Variables

Create `.env.local`:

```env
VITE_API_BASE=/api
```

## Linting

ESLint is configured for:
- TypeScript strict mode
- React hooks rules
- Unused variable detection
- 100% lint-clean target

## Responsive Design

All components are responsive:
- Mobile-first breakpoints
- Flexible grid layouts
- Touch-friendly interactions
- Adaptive canvas sizing

## Future Enhancements

- Real-time collaboration
- Advanced CAD features
- 3D visualization
- Multi-project management
- Export to various formats
