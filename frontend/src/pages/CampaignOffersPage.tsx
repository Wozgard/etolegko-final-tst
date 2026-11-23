import {
  Box,
  Button,
  Combobox,
  Group,
  Anchor,
  Loader,
  Popover,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  useCombobox,
} from '@mantine/core'
import { IconArrowBackUp, IconArrowLeft, IconArrowUp, IconPin, IconTrash } from '@tabler/icons-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  distributeShares,
  sortOffers,
  type EditableOffer,
} from '../features/edit-offers'
import { apiClient } from '../shared/api/client'
import { palette } from '../shared/theme'

type StreamOfferApi = {
  id: number
  name: string
  share: number
  removed: boolean
  pinned: boolean
}

type StreamApi = {
  name: string
  offers?: StreamOfferApi[]
}

type OfferListItem = {
  id: number
  name: string
}

type CampaignListItem = {
  id: number
  name: string
}

type OfferSnapshot = {
  id: number
  name: string
  share: number
  removed: boolean
}

const DIRTY_TABLE_BG = '#C5DFE9'

function cloneOffers(offers: EditableOffer[]): EditableOffer[] {
  return offers.map((o) => ({ ...o }))
}

function toEditable(offers: StreamOfferApi[]): EditableOffer[] {
  return offers.map((o) => ({
    id: o.id,
    name: o.name,
    share: o.share,
    pinned: o.pinned,
    removed: o.removed,
  }))
}

function snapshotIgnoringPin(offers: EditableOffer[]): OfferSnapshot[] {
  return offers.map(({ id, name, share, removed }) => ({
    id,
    name,
    share,
    removed,
  }))
}

function snapshotsEqual(a: OfferSnapshot[], b: OfferSnapshot[]): boolean {
  if (a.length !== b.length) {
    return false
  }
  return a.every(
    (item, i) =>
      item.id === b[i].id &&
      item.name === b[i].name &&
      item.share === b[i].share &&
      item.removed === b[i].removed,
  )
}

function formatOfferOption(offer: OfferListItem): string {
  return `${offer.id} — ${offer.name}`
}

function isOfferStream(stream: StreamApi): boolean {
  return Array.isArray(stream.offers) && stream.offers.length > 0
}

export function CampaignOffersPage() {
  const { id } = useParams<{ id: string }>()
  const campaignId = id ?? ''

  const [campaignTitle, setCampaignTitle] = useState(campaignId)
  const [streams, setStreams] = useState<StreamApi[]>([])
  const [offers, setOffers] = useState<EditableOffer[]>([])
  const [baseline, setBaseline] = useState<EditableOffer[]>([])
  const [dirty, setDirty] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [addingOffer, setAddingOffer] = useState(false)
  const [pushInFlight, setPushInFlight] = useState(false)
  const [backLinkHover, setBackLinkHover] = useState(false)

  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption(),
  })
  const [offerInput, setOfferInput] = useState('')
  const [searchResults, setSearchResults] = useState<OfferListItem[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const requestIdRef = useRef(0)
  const abortRef = useRef<AbortController | null>(null)
  const offerInputRef = useRef('')
  const comboboxRef = useRef(combobox)
  comboboxRef.current = combobox
  const pushEpochRef = useRef(0)

  const applyOffers = useCallback((next: EditableOffer[], nextDirty: boolean) => {
    if (nextDirty) {
      pushEpochRef.current += 1
      setPushInFlight(false)
    }
    setOffers(next)
    setDirty(nextDirty)
  }, [])

  const loadStreams = useCallback(async () => {
    setLoading(true)
    setLoadError(null)

    try {
      const [campaignsResponse, streamsResponse] = await Promise.all([
        apiClient('/campaigns'),
        apiClient(`/campaigns/${campaignId}/streams`),
      ])

      if (campaignsResponse.ok) {
        const campaigns: CampaignListItem[] = await campaignsResponse.json()
        const found = campaigns.find((c) => String(c.id) === campaignId)
        setCampaignTitle(found?.name ?? campaignId)
      } else {
        setCampaignTitle(campaignId)
      }

      if (!streamsResponse.ok) {
        setLoadError('Не удалось загрузить потоки кампании')
        setStreams([])
        setOffers([])
        setBaseline([])
        setDirty(false)
        return
      }

      const streamList: StreamApi[] = await streamsResponse.json()
      let tableOffers: EditableOffer[] = []

      for (const stream of streamList) {
        if (isOfferStream(stream)) {
          tableOffers = toEditable(stream.offers!)
        }
      }

      const sorted = sortOffers(tableOffers)
      setStreams(streamList)
      setOffers(sorted)
      setBaseline(cloneOffers(sorted))
      setDirty(false)
    } catch {
      setLoadError('Не удалось загрузить потоки кампании')
      setStreams([])
      setOffers([])
      setBaseline([])
      setDirty(false)
    } finally {
      setLoading(false)
    }
  }, [campaignId])

  useEffect(() => {
    void loadStreams()
  }, [loadStreams])

  const cancelOfferSearch = () => {
    abortRef.current?.abort()
    abortRef.current = null
  }

  const syncOfferInput = (value: string) => {
    offerInputRef.current = value
    setOfferInput(value)
  }

  const resetAddOffer = () => {
    cancelOfferSearch()
    syncOfferInput('')
    setSearchResults([])
    combobox.closeDropdown()
  }

  const closeAddOfferPopover = () => {
    resetAddOffer()
    setAddingOffer(false)
  }

  const toggleAddOfferPopover = () => {
    if (addingOffer) {
      closeAddOfferPopover()
    } else {
      setAddingOffer(true)
    }
  }

  useEffect(() => {
    if (!addingOffer || offerInput === '') {
      setSearchResults([])
      setSearchLoading(false)
      return
    }

    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId

    const timer = window.setTimeout(() => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      setSearchLoading(true)

      const query = offerInputRef.current

      void (async () => {
        try {
          const response = await apiClient(
            `/offers?q=${encodeURIComponent(query)}`,
            { signal: controller.signal },
          )

          if (
            requestId !== requestIdRef.current ||
            offerInputRef.current !== query ||
            offerInputRef.current === ''
          ) {
            return
          }

          if (!response.ok) {
            setSearchResults([])
            return
          }

          const data: OfferListItem[] = await response.json()

          if (
            requestId !== requestIdRef.current ||
            offerInputRef.current !== query
          ) {
            return
          }

          setSearchResults(data)
          if (data.length > 0) {
            comboboxRef.current.openDropdown()
          } else {
            comboboxRef.current.closeDropdown()
          }
        } catch (err) {
          if (err instanceof DOMException && err.name === 'AbortError') {
            return
          }
          if (
            requestId === requestIdRef.current &&
            offerInputRef.current === query
          ) {
            setSearchResults([])
          }
        } finally {
          if (
            requestId === requestIdRef.current &&
            offerInputRef.current === query
          ) {
            setSearchLoading(false)
          }
        }
      })()
    }, 300)

    return () => window.clearTimeout(timer)
  }, [offerInput, addingOffer])

  const handleOfferInputChange = (rawValue: string) => {
    const digits = rawValue.replace(/\D/g, '')

    if (digits === '') {
      cancelOfferSearch()
      syncOfferInput('')
      setSearchResults([])
      combobox.closeDropdown()
      return
    }

    cancelOfferSearch()
    syncOfferInput(digits)
  }

  const handleOfferSelect = (value: string) => {
    const found = searchResults.find((item) => String(item.id) === value)
    if (!found) {
      return
    }

    if (offers.some((o) => o.id === found.id)) {
      closeAddOfferPopover()
      return
    }

    const next = sortOffers(
      distributeShares([
        ...offers,
        {
          id: found.id,
          name: found.name,
          share: 0,
          pinned: false,
          removed: false,
        },
      ]),
    )

    applyOffers(next, true)
    closeAddOfferPopover()
  }

  const handleRemove = (offerId: number) => {
    const next = sortOffers(
      distributeShares(
        offers.map((o) =>
          o.id === offerId ? { ...o, removed: true, share: 0 } : o,
        ),
      ),
    )
    applyOffers(next, true)
  }

  const handleBringBack = (offerId: number) => {
    const next = sortOffers(
      distributeShares(
        offers.map((o) =>
          o.id === offerId ? { ...o, removed: false } : o,
        ),
      ),
    )
    applyOffers(next, true)
  }

  const handlePin = (offerId: number) => {
    const before = snapshotIgnoringPin(offers)
    const next = sortOffers(
      distributeShares(
        offers.map((o) =>
          o.id === offerId ? { ...o, pinned: !o.pinned } : o,
        ),
      ),
    )
    const after = snapshotIgnoringPin(next)

    if (snapshotsEqual(before, after)) {
      setOffers(next)
      if (!dirty) {
        setBaseline(cloneOffers(next))
        setDirty(false)
      }
      return
    }

    applyOffers(next, true)
  }

  const handleCancel = () => {
    applyOffers(cloneOffers(baseline), false)
    closeAddOfferPopover()
  }

  const handlePush = async () => {
    const epoch = pushEpochRef.current
    const body = {
      offers: offers.map((o) => ({
        id: o.id,
        removed: o.removed,
        pinned: o.pinned,
        ...(o.pinned && !o.removed ? { share: o.share } : {}),
      })),
    }

    setPushInFlight(true)

    try {
      const response = await apiClient(`/campaigns/${campaignId}/push`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (epoch !== pushEpochRef.current) {
        return
      }

      if (!response.ok) {
        return
      }

      setBaseline(cloneOffers(offers))
      setDirty(false)
    } catch {
      if (epoch !== pushEpochRef.current) {
        return
      }
    } finally {
      if (epoch === pushEpochRef.current) {
        setPushInFlight(false)
      }
    }
  }

  const renderOfferTable = () => (
    <Box
      style={{
        backgroundColor: dirty ? DIRTY_TABLE_BG : 'transparent',
        transition: 'background-color 0.15s ease',
      }}
    >
      <Table
        verticalSpacing="sm"
        styles={{
          table: { borderCollapse: 'separate', borderSpacing: 0 },
          th: {
            color: palette.textSecondary,
            fontWeight: 500,
            borderBottom: `1px solid ${palette.border}`,
          },
          td: {
            borderBottom: `1px solid ${palette.border}`,
          },
        }}
      >
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Оффер</Table.Th>
            <Table.Th>Доля</Table.Th>
            <Table.Th>Действия</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {offers.map((offer) => (
            <Table.Tr key={offer.id}>
              <Table.Td>
                <Text
                  c={offer.removed ? palette.textSecondary : palette.text}
                >
                  {offer.name}
                </Text>
              </Table.Td>
              <Table.Td>
                <Text c={offer.removed ? palette.textSecondary : palette.text}>
                  {offer.share}%
                </Text>
              </Table.Td>
              <Table.Td>
                <Group gap="xs">
                  {offer.removed ? (
                    <Button
                      size="compact-sm"
                      variant="light"
                      leftSection={<IconArrowBackUp size={14} aria-hidden />}
                      onClick={() => handleBringBack(offer.id)}
                    >
                      Вернуть
                    </Button>
                  ) : (
                    <>
                      <Button
                        size="compact-sm"
                        variant="light"
                        color="red"
                        leftSection={<IconTrash size={14} aria-hidden />}
                        onClick={() => handleRemove(offer.id)}
                      >
                        Удалить
                      </Button>
                      <Button
                        size="compact-sm"
                        variant={offer.pinned ? 'filled' : 'light'}
                        color="brand"
                        aria-label={offer.pinned ? 'Открепить' : 'Закрепить'}
                        onClick={() => handlePin(offer.id)}
                      >
                        <IconPin size={16} aria-hidden />
                      </Button>
                    </>
                  )}
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Box>
  )

  return (
    <Box
      mih="100vh"
      py="xl"
      px="md"
      style={{ backgroundColor: palette.pageBg }}
    >
      <Box maw={960} mx="auto">
        <Stack gap="lg">
          <Stack gap={4}>
            <Anchor
              component={Link}
              to="/"
              size="sm"
              c={palette.primary}
              underline="never"
              w="fit-content"
              onMouseEnter={() => setBackLinkHover(true)}
              onMouseLeave={() => setBackLinkHover(false)}
              style={{
                alignSelf: 'flex-start',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                borderBottom: `1px solid ${backLinkHover ? palette.primary : 'transparent'}`,
              }}
            >
              <IconArrowLeft size={14} aria-hidden />
              Компании
            </Anchor>
            <Title order={1} c={palette.text}>
              {campaignTitle}
            </Title>
          </Stack>

          <Box style={{ borderBottom: `1px solid ${palette.border}` }} />

          {loadError ? (
            <Text size="sm" c="red">
              {loadError}
            </Text>
          ) : null}

          {!loading
            ? streams.map((stream) =>
                isOfferStream(stream) ? (
                  <Stack key={stream.name} gap="md">
                    <Text fw={600} c={palette.text}>
                      Поток {stream.name}
                    </Text>

                    <Group justify="space-between" align="center" wrap="wrap">
                      <Text size="sm" c={palette.textSecondary}>
                        Редактируется только этот поток
                      </Text>
                      <Popover
                        opened={addingOffer}
                        onChange={(opened) => {
                          if (!opened) {
                            closeAddOfferPopover()
                          } else {
                            setAddingOffer(true)
                          }
                        }}
                        position="bottom-end"
                        closeOnEscape
                      >
                        <Popover.Target>
                          <Button
                            variant="light"
                            color="brand"
                            onClick={toggleAddOfferPopover}
                          >
                            Добавить оффер
                          </Button>
                        </Popover.Target>
                        <Popover.Dropdown
                          styles={{
                            dropdown: { borderColor: palette.border },
                          }}
                        >
                          <Combobox
                            store={combobox}
                            withinPortal={false}
                            position="bottom-start"
                            onOptionSubmit={handleOfferSelect}
                          >
                            <Combobox.Target>
                              <TextInput
                                label="ID оффера"
                                placeholder="77"
                                value={offerInput}
                                onChange={(event) =>
                                  handleOfferInputChange(
                                    event.currentTarget.value,
                                  )
                                }
                                onClick={() => {
                                  if (searchResults.length > 0) {
                                    combobox.openDropdown()
                                  }
                                }}
                                onFocus={() => {
                                  if (searchResults.length > 0) {
                                    combobox.openDropdown()
                                  }
                                }}
                                inputMode="numeric"
                                rightSection={
                                  searchLoading ? <Loader size="xs" /> : null
                                }
                                styles={{
                                  label: { color: palette.textSecondary },
                                }}
                              />
                            </Combobox.Target>

                            <Combobox.Dropdown
                              styles={{
                                dropdown: { borderColor: palette.border },
                              }}
                            >
                              <Combobox.Options
                                style={{ maxHeight: 240, overflowY: 'auto' }}
                              >
                                {searchResults.map((item) => (
                                  <Combobox.Option
                                    key={item.id}
                                    value={String(item.id)}
                                  >
                                    {formatOfferOption(item)}
                                  </Combobox.Option>
                                ))}
                              </Combobox.Options>
                            </Combobox.Dropdown>
                          </Combobox>
                        </Popover.Dropdown>
                      </Popover>
                    </Group>

                      {renderOfferTable()}

                      {!pushInFlight && dirty ? (
                        <Group gap="sm">
                          <Button
                            color="brand"
                            leftSection={
                              <IconArrowUp size={16} aria-hidden />
                            }
                            onClick={() => void handlePush()}
                          >
                            В Keitaro
                          </Button>
                          <Button variant="default" onClick={handleCancel}>
                            Отмена
                          </Button>
                        </Group>
                      ) : null}
                  </Stack>
                ) : (
                  <Stack key={stream.name} gap="xs">
                    <Text fw={600} c={palette.text}>
                      Поток {stream.name}
                    </Text>
                    <Text size="sm" c={palette.textSecondary}>
                      Только просмотр
                    </Text>
                  </Stack>
                ),
              )
            : null}
        </Stack>
      </Box>
    </Box>
  )
}