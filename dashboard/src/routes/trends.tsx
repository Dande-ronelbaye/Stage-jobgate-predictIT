import { createFileRoute } from '@tanstack/react-router'
import TrendsPairsPage from '../components/TrendsPairsPage'

export const Route = createFileRoute('/trends')({
  component: TrendsPairsPage,
})