import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        host: '0.0.0.0',
        proxy: {
            // Forward all /api/* requests to the FastAPI backend (server.py)
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                rewrite: function (path) { return path; }
            }
        }
    },
    preview: {
        port: 4173,
        host: '0.0.0.0'
    }
});
