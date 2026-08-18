# Resolve AI Frontend

Professional light-theme React/Vite frontend for Resolve AI.

## UI direction
- Clean light enterprise/SaaS interface
- Minimal card surfaces and subtle borders
- No login or registration screen
- No user profile/avatar in the application header
- Analytics pages emphasize the primary insight rather than dense card grids
- Existing routes, types, services, mock data, and backend integration points are preserved

## Run

```powershell
npm.cmd install
npm.cmd run dev
```

Build:

```powershell
npm.cmd run build
```

## Integration

Connect backend/ML APIs through the existing service layer and TypeScript types. Do not expose secrets in the frontend.
