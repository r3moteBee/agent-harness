# Pantheon Frontend - Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

**Note**: Make sure the backend is running on `http://localhost:8000` for API calls to work.

## First Time Setup

1. **Backend URL**: The frontend proxies all `/api` and `/ws` requests to `http://localhost:8000`
   - Update `vite.config.js` if your backend runs on a different URL

2. **Create a Project**:
   - Click "Projects" in the sidebar
   - Click "Create Project"
   - Enter a name (e.g., "My First Project")
   - Click "Create Project"

3. **Configure LLM**:
   - Click "Settings" in the sidebar
   - Enter your LLM API endpoint (e.g., `https://api.openai.com/v1`)
   - Paste your API key
   - Click "Test Connection"
   - Select a model from the dropdown (click "Fetch Models" to refresh)

4. **Start Chatting**:
   - Click "Chat" in the sidebar
   - Type a message and press Enter
   - Watch the agent respond in real-time

## File Structure at a Glance

```
frontend/
├── src/
│   ├── api/client.js          # All API endpoints
│   ├── store/index.js         # Global state (Zustand)
│   ├── components/            # 8 main components
│   ├── pages/                 # 7 page wrappers
│   ├── App.jsx               # Router setup
│   └── index.css             # Tailwind styles
├── package.json              # Dependencies
├── vite.config.js            # Dev server config
└── tailwind.config.js        # Tailwind setup
```

## Common Tasks

### Add a New Page
1. Create component in `src/components/MyComponent.jsx`
2. Create page wrapper in `src/pages/MyPage.jsx`
3. Add route to `src/App.jsx`
4. Add navigation item to `src/components/Layout.jsx`

### Make an API Call
```javascript
import { myApi } from '../api/client'
import { useStore } from '../store'

// In component:
const activeProject = useStore(s => s.activeProject)
const addNotification = useStore(s => s.addNotification)

try {
  const response = await myApi.someMethod(activeProject.id)
  // Use response.data
  addNotification({ type: 'success', message: 'Done!' })
} catch (error) {
  addNotification({ type: 'error', message: error.message })
}
```

### Update Global State
```javascript
import { useStore } from '../store'

const messages = useStore(s => s.messages)
const addMessage = useStore(s => s.addMessage)

addMessage({ role: 'user', content: 'Hello!' })
```

### Add Styling
```jsx
<div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
  <h1 className="text-xl font-bold text-gray-100">Title</h1>
  <p className="text-sm text-gray-400">Subtitle</p>
</div>
```

## Production Build

```bash
npm run build        # Creates dist/ folder
npm run preview      # Preview the build locally
docker build -t my-frontend .  # Build Docker image
docker run -p 80:80 my-frontend  # Run in Docker
```

## Troubleshooting

### "Cannot GET /"
- Make sure you're visiting `http://localhost:5173`
- Check that the dev server is running with `npm run dev`

### API calls are failing
- Verify backend is running on port 8000
- Check Network tab in DevTools for failed requests
- Look at backend logs for errors

### Chat isn't working
- Check if WebSocket connection is open in DevTools Network tab
- Verify LLM settings are correct (Settings page)
- Test connection button should show green checkmark

### Styles look broken
- Clear browser cache (Ctrl+Shift+Delete)
- Try hard refresh (Ctrl+Shift+R on Windows, Cmd+Shift+R on Mac)
- Rebuild with `npm run build`

## Documentation

See `README.md` for complete documentation including:
- Full feature list
- Component reference
- API integration details
- Responsive design info
- Browser support

## Next Steps

1. **Explore the UI**: Click through each page to understand the interface
2. **Read the code**: Start with `src/App.jsx` and `src/components/Layout.jsx`
3. **Check the API**: Review `src/api/client.js` for available endpoints
4. **Customize**: Update colors in `tailwind.config.js` or components in `src/components/`

## Tips

- Use `console.log()` in components for debugging
- React DevTools browser extension is helpful
- Check Network tab to inspect API calls
- Use Ctrl+K (Cmd+K on Mac) shortcuts in most modern IDEs

Enjoy building with Pantheon!
