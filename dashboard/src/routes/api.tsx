import { createFileRoute } from '@tanstack/react-router'
import ApiPage from '../components/ApiPage'

export const Route = createFileRoute('/api')({
  component: ApiPage,
})