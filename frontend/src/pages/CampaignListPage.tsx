import {
  Box,
  Button,
  Group,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CreateCampaignModal } from '../features/create-campaign'
import { apiClient } from '../shared/api/client'
import { CAMPAIGN_NAME_PREFIX, palette } from '../shared/theme'

type CampaignListItem = {
  id: number
  name: string
}

export function CampaignListPage() {
  const navigate = useNavigate()
  const [campaigns, setCampaigns] = useState<CampaignListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const loadCampaigns = useCallback(async () => {
    setLoading(true)
    setLoadError(null)

    try {
      const response = await apiClient('/campaigns')
      if (!response.ok) {
        setLoadError('Не удалось загрузить список кампаний')
        setCampaigns([])
        return
      }

      const data: CampaignListItem[] = await response.json()
      setCampaigns(data)
    } catch {
      setLoadError('Не удалось загрузить список кампаний')
      setCampaigns([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadCampaigns()
  }, [loadCampaigns])

  return (
    <Box
      mih="100vh"
      py="xl"
      px="md"
      style={{ backgroundColor: palette.pageBg }}
    >
      <Box maw={960} mx="auto">
        <Group justify="space-between" align="flex-start" wrap="wrap">
          <Stack gap={4}>
            <Title order={1} c={palette.text}>
              Кампании
            </Title>
            <Text size="sm" c={palette.textSecondary}>
              Показаны только кампании с префиксом {CAMPAIGN_NAME_PREFIX}
            </Text>
          </Stack>
          <Button color="brand" onClick={() => setModalOpen(true)}>
            Новая кампания
          </Button>
        </Group>

        <Box
          mt="lg"
          style={{ borderBottom: `1px solid ${palette.border}` }}
        />

        {loadError ? (
          <Text size="sm" c="red" mt="sm">
            {loadError}
          </Text>
        ) : null}

        <Table
          highlightOnHover
          verticalSpacing="sm"
          styles={{
            table: { borderCollapse: 'separate', borderSpacing: 0 },
            th: {
              color: palette.textSecondary,
              fontWeight: 500,
              borderBottom: `1px solid ${palette.border}`,
            },
            td: {
              color: palette.text,
              borderBottom: `1px solid ${palette.border}`,
            },
          }}
        >
          <Table.Thead>
            <Table.Tr>
              <Table.Th>ID</Table.Th>
              <Table.Th>Название</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {loading ? (
              <Table.Tr>
                <Table.Td colSpan={2}>
                  <Text c={palette.textSecondary}>Загрузка…</Text>
                </Table.Td>
              </Table.Tr>
            ) : campaigns.length === 0 ? (
              <Table.Tr>
                <Table.Td colSpan={2}>
                  <Text c={palette.textSecondary}>
                    Кампаний пока нет. Создайте первую.
                  </Text>
                </Table.Td>
              </Table.Tr>
            ) : (
              campaigns.map((campaign) => (
                <Table.Tr
                  key={campaign.id}
                  onClick={() => navigate(`/campaigns/${campaign.id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <Table.Td>{campaign.id}</Table.Td>
                  <Table.Td>{campaign.name}</Table.Td>
                </Table.Tr>
              ))
            )}
          </Table.Tbody>
        </Table>
      </Box>

      <CreateCampaignModal
        opened={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => void loadCampaigns()}
      />
    </Box>
  )
}