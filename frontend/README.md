# TransitOps Frontend

This is the frontend application for the TransitOps Smart Transport Operations Platform. It is built with **Vite**, **React**, **TypeScript**, and **Tailwind CSS**.

## Overview
Currently, this frontend serves as a **high-fidelity mock UI**. It implements full routing, role-based access control (gating), client-side validation using `react-hook-form` and `zod`, and a comprehensive suite of UI components without relying on a live backend.

### Key Features
- **Authentication & RBAC:** Mock login flow with role selection (Fleet Manager, Dispatcher, Safety Officer, Financial Analyst). Routes and navigation are gated by role.
- **UI Kit:** A custom design system (available at `/dev/kit` in dev mode) featuring glassmorphic and high-contrast dark-mode elements.
- **Trip Lifecycle:** Full forms for creating, dispatching (with AI Advisor mock), and completing trips (with paired fuel validations).
- **Fleet & Maintenance:** Dashboards for tracking vehicle status and logging maintenance costs.
- **Analytics & Finance:** Mock bar charts and CSV export functionality for financial reporting.
- **Global AI Chat:** A floating chat widget available on all screens.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open `http://localhost:5173` in your browser. Log in using any email matching a role prefix (e.g. `manager@transitops.in`) and the password `password123`.

## File Structure
- `/src/components/ui`: Reusable primitive components (Buttons, Inputs, Modals, etc.)
- `/src/components/layout`: AppShell and navigation components.
- `/src/features/*`: Domain-specific pages and modals (e.g. `/trips`, `/fleet`, `/finance`).
- `/src/lib/schemas`: Zod validation schemas for forms.
- `/src/types`: Global TypeScript types (API, Models, Roles).
- `/src/auth`: Mock AuthProvider for context and route guards.

## Next Steps
Once the backend API is ready, you will need to replace the static `mockData` arrays in the feature pages with React Query (`@tanstack/react-query`) hooks that fetch from the real endpoints.
