import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from '@tanstack/react-router'
import { getRouter } from './router' // On importe la fonction de création
import './styles.css'

// On appelle la fonction pour générer l'instance du routeur
const router = getRouter()

if (!document.getElementById('root')?.innerHTML) {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <RouterProvider router={router} />
    </React.StrictMode>,
  )
}

