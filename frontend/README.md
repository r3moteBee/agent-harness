# Agent Harness Frontend

A modern React + Vite + Tailwind CSS interface for the Agent Harness AI agent framework.

## Features

### Pages

1. **Chat** - Real-time streaming conversation with the AI agent
   - Live message streaming with markdown rendering
   - Tool call tracking and result visualization
   - Session management
   - Keyboard shortcuts (Enter to send, Shift+Enter for newline)

2. **Memory** - Multi-tiered memory management system
   - Episodic: Personal notes and conversation history
   - Semantic: Vector-embedded knowledge documents with similarity scores
   - Graph: Knowledge graph visualization with nodes and relationships
   - Archival: Long-term storage management
   - Search, browse, and delete memories

3. **Files** - Project file repository
   - Browse folder structure with breadcrumb navigation
   - Upload, download, and delete files
   - Create new folders
   - Preview text files inline
   - Responsive file browser

4. **Personality** - Agent personality configuration
   - Split-pane editor for soul.md and agent.md
   - Live Markdown preview
   - Per-project personality overrides
   - Save and reload functionality

5. **Tasks** - Autonomous task scheduler
   - Create scheduled tasks with cron expressions
   - View task status and next run times
   - Real-time task logs viewer
   - Cancel running tasks
   - Auto-refresh every 30 seconds

6. **Projects** - Project management
   - Create and manage multiple projects
   - Set active project
   - View project metadata (created date, ID)
   - Delete inactive projects
   - Active project indicator in sidebar

7. **Settings** - System configuration
   - LLM endpoint and API key management
   - Model selection with "Fetch Models" button
   - Connection testing
   - Secret management for API keys and tokens
   - Key masking for security

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js           # API client with Axios and WebSocket helpers
│   ├── store/
│   │   └── index.js            # Zustand global state management
│   ├── components/
│   │   ├── Layout.jsx          # Main layout with sidebar
│   │   ├── Chat.jsx            # Chat interface with streaming
│   │   ├── MemoryBrowser.jsx   # Memory tier management
│   │   ├── FileRepository.jsx  # File explorer
│   │   ├── PersonalityEditor.jsx # Soul/Agent editor
│   │   ├── Settings.jsx        # LLM & secrets config
│   │   ├── TaskMonitor.jsx     # Task scheduler
│   │   └── Projects.jsx        # Project manager
│   ├── pages/
│   │   ├── ChatPage.jsx
│   │   ├── MemoryPage.jsx
│   │   ├── FilesPage.jsx
│   │   ├── PersonalityPage.jsx
│   │   ├── SettingsPage.jsx
│   │   ├── TasksPage.jsx
│   │   └── ProjectsPage.jsx
│   ├── App.jsx                 # Router configuration
│   ├── main.jsx                # React root
│   └── index.css               # Tailwind styles
├── index.html                  # HTML entry point
├── package.json                # Dependencies
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind customization
├── postcss.config.js           # PostCSS setup
├── Dockerfile                  # Docker build configuration
├── nginx.conf                  # Nginx reverse proxy
└── README.md
```

## Installation

### Requirements
- Node.js 18+
- npm or yarn

### Development

```bash
npm install
npm run dev
```

The app will be available at `http://localhost:5173` with hot module reloading.

### Production Build

```bash
npm install
npm run build
npm run preview
```

## Docker

Build and run in Docker:

```bash
docker build -t agent-harness-frontend .
docker run -p 80:80 agent-harness-frontend
```

The app will be available at `http://localhost`.

## API Integration

### Backend Configuration

The frontend proxies API calls to the backend:

```javascript
// Proxies /api/* to http://localhost:8000
// Proxies /ws/* to ws://localhost:8000
```

Configure backend URL in `vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://your-backend:8000',
    changeOrigin: true,
  },
}
```

### API Client

All API calls are centralized in `src/api/client.js`:

```javascript
import { chatApi, memoryApi, filesApi, settingsApi, tasksApi, personalityApi, projectsApi } from './api/client'

// Examples:
await chatApi.send(message, sessionId, projectId)
await memoryApi.search(query, projectId)
await filesApi.upload(file, projectId)
```

### WebSocket Chat Streaming

Real-time chat uses WebSocket:

```javascript
import { createChatSocket } from './api/client'

const socket = createChatSocket((event) => {
  switch (event.type) {
    case 'text_delta':
      // Append to message
      break
    case 'tool_call':
      // Display tool execution
      break
    case 'done':
      // Message complete
      break
  }
})

socket.send(JSON.stringify({ message, session_id, project_id }))
```

## State Management

Uses Zustand for global state:

```javascript
import { useStore } from './store'

// In components:
const messages = useStore((s) => s.messages)
const addMessage = useStore((s) => s.addMessage)
const activeProject = useStore((s) => s.activeProject)
const notifications = useStore((s) => s.notifications)
```

### Store Structure

- `activeProject`: Current project context
- `sessionId`: Current chat session
- `messages`: Chat message history
- `isStreaming`: Chat streaming state
- `streamingContent`: Live message content
- `currentToolCalls`: Tool execution tracking
- `projects`: Available projects list
- `settings`: LLM configuration
- `sidebarOpen`: Mobile sidebar toggle
- `notifications`: Toast notifications queue

## Styling

### Tailwind CSS

Full Tailwind CSS v3 with custom brand colors:

```javascript
// tailwind.config.js
colors: {
  brand: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    900: '#0c4a6e',
  }
}
```

### Dark Theme

The app uses dark mode by default (gray-950 background). Customize in `index.css`.

### Custom Scrollbar

Styled scrollbar with `.scrollbar-thin` class for narrow scrollbars with gray color.

## Responsive Design

Mobile-first responsive design:

- **Mobile**: Full-width single column, hamburger menu sidebar
- **Tablet**: Sidebar takes 264px width
- **Desktop**: Fixed sidebar + main content area

## Components Reference

### Chat Component
- Real-time streaming with markdown rendering
- Tool call visualization with expandable details
- Message timestamps and sender avatars
- Keyboard shortcuts
- Stop streaming button

### MemoryBrowser
- 4 memory tiers (Episodic, Semantic, Graph, Archival)
- Search within each tier
- Similarity scores for semantic documents
- Graph visualization with nodes and edges
- Delete operations

### FileRepository
- Breadcrumb navigation
- Upload, download, delete files
- Create folders
- Text file preview pane
- File size display

### PersonalityEditor
- Dual editor panes (Edit + Preview)
- Markdown preview with syntax highlighting
- Save per-project
- Reload from backend

### TaskMonitor
- Create tasks with schedule selection
- Expandable task details
- Real-time logs viewer
- Cancel tasks
- Auto-refresh every 30 seconds

### Projects
- Grid layout of project cards
- Create new projects
- Set active project
- Delete inactive projects
- Project metadata display

### Settings
- LLM endpoint configuration
- API key management (masked input)
- Model fetching and selection
- Connection testing
- Secret key-value storage

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Performance Optimizations

- Code splitting via Vite
- Image optimization
- CSS minification
- Gzip compression (nginx)
- Scrollbar styling for smooth scrolling
- Debounced API calls
- Local state management to reduce API calls

## Development Tips

### Adding New Pages

1. Create component in `src/components/`
2. Create page wrapper in `src/pages/`
3. Add route in `src/App.jsx`
4. Add nav item in `src/components/Layout.jsx`

### Adding API Endpoints

1. Add method to appropriate API object in `src/api/client.js`
2. Use in components with `try/catch` and `addNotification`

### Styling Components

1. Use Tailwind classes directly in JSX
2. Dark theme colors: `bg-gray-900`, `text-gray-100`
3. Brand colors: `bg-brand-600`, `text-brand-400`
4. Hover states: `hover:bg-gray-800`

### Debugging

- React DevTools for component inspection
- Network tab for API calls
- Console for client-side errors
- WebSocket messages in Network tab

## Troubleshooting

### API Connection Issues
- Verify backend is running on port 8000
- Check CORS headers in backend
- Inspect Network tab for failed requests

### Chat Not Streaming
- Check WebSocket connection in Network tab
- Verify backend WebSocket endpoint
- Check browser console for errors

### Styling Issues
- Clear Tailwind cache: `npm run build`
- Check if styles are in content globs in tailwind.config.js

## License

Part of the Agent Harness project.
