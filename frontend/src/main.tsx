import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ErrorBoundary } from 'react-error-boundary'
import './index.css'
import App from './App.tsx'

const ErrorFallback = ({ error }: any) => (
  <div className="flex h-screen w-full items-center justify-center bg-black text-red-500 p-8 flex-col gap-4 font-mono text-sm">
    <h2 className="text-xl font-bold">UI Component Crashed</h2>
    <pre className="bg-red-500/10 p-4 rounded border border-red-500/20 max-w-full overflow-auto">
      {error.message}
    </pre>
  </div>
);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
