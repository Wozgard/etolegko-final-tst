import { Title } from '@mantine/core'
import { useParams } from 'react-router-dom'

export function CampaignOffersPage() {
  const { id } = useParams<{ id: string }>()

  return <Title order={1}>Офферы кампании {id}</Title>
}