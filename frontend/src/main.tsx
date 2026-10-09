import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Amplify } from 'aws-amplify'
import { Authenticator } from '@aws-amplify/ui-react'
import '@aws-amplify/ui-react/styles.css'
import './index.css'
import App from './App.tsx'

const authMode = import.meta.env.VITE_AUTH_MODE || 'demo'
if (authMode !== 'demo' && authMode !== 'cognito') {
  throw new Error(`Unsupported VITE_AUTH_MODE: ${authMode}`)
}

if (authMode === 'cognito') {
  const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
  const userPoolClientId = import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID
  if (!userPoolId || !userPoolClientId) {
    throw new Error('Cognito mode requires the VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_USER_POOL_CLIENT_ID values.')
  }
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId,
        loginWith: { username: true },
      },
    },
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {authMode === 'cognito' ? (
      <Authenticator hideSignUp>
        {({ signOut }) => <App onSignOut={signOut} />}
      </Authenticator>
    ) : (
      <App />
    )}
  </StrictMode>,
)
