import {
  Button,
  Combobox,
  Group,
  Loader,
  Modal,
  Stack,
  Text,
  TextInput,
  useCombobox,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { useEffect, useRef, useState } from 'react'
import { apiClient } from '../../shared/api/client'
import { palette } from '../../shared/theme'

type CreateCampaignModalProps = {
  opened: boolean
  onClose: () => void
  onCreated: () => void
}

type OfferListItem = {
  id: number
  name: string
}

function formatOffer(offer: OfferListItem): string {
  return `${offer.id} — ${offer.name}`
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const data: { detail?: string | { msg: string }[] } = await response.json()
    if (typeof data.detail === 'string') {
      return data.detail
    }
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      return data.detail.map((item) => item.msg).join(', ')
    }
  } catch {
    // ignore parse errors
  }
  return 'Не удалось создать кампанию'
}

export function CreateCampaignModal({
  opened,
  onClose,
  onCreated,
}: CreateCampaignModalProps) {
  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption(),
  })

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [offers, setOffers] = useState<OfferListItem[]>([])
  const [selectedOffer, setSelectedOffer] = useState<OfferListItem | null>(
    null,
  )
  const [loading, setLoading] = useState(false)

  const requestIdRef = useRef(0)
  const abortRef = useRef<AbortController | null>(null)
  const inputValueRef = useRef('')
  const comboboxRef = useRef(combobox)
  comboboxRef.current = combobox

  const form = useForm({
    initialValues: {
      name: '',
      geo: '',
    },
    validate: {
      name: (value) => (value.trim() ? null : 'Укажите название'),
      geo: (value) => (value.trim() ? null : 'Укажите гео-код'),
    },
  })

  const syncInputValue = (value: string) => {
    inputValueRef.current = value
    setInputValue(value)
  }

  const cancelOfferRequest = () => {
    requestIdRef.current += 1
    abortRef.current?.abort()
    abortRef.current = null
    setLoading(false)
  }

  const resetOfferState = () => {
    cancelOfferRequest()
    syncInputValue('')
    setOffers([])
    setSelectedOffer(null)
    combobox.closeDropdown()
  }

  const handleClose = () => {
    if (submitting) {
      return
    }
    setError(null)
    form.reset()
    resetOfferState()
    onClose()
  }

  useEffect(() => {
    if (!opened || selectedOffer) {
      return
    }

    if (inputValue === '') {
      setOffers([])
      setLoading(false)
      return
    }

    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId

    const timer = window.setTimeout(() => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      setLoading(true)

      const query = inputValueRef.current

      void (async () => {
        try {
          const response = await apiClient(
            `/offers?q=${encodeURIComponent(query)}`,
            { signal: controller.signal },
          )

          if (
            requestId !== requestIdRef.current ||
            inputValueRef.current !== query ||
            inputValueRef.current === ''
          ) {
            return
          }

          if (!response.ok) {
            setOffers([])
            return
          }

          const data: OfferListItem[] = await response.json()

          if (
            requestId !== requestIdRef.current ||
            inputValueRef.current !== query ||
            inputValueRef.current === ''
          ) {
            return
          }

          setOffers(data)
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
            inputValueRef.current === query
          ) {
            setOffers([])
          }
        } finally {
          if (
            requestId === requestIdRef.current &&
            inputValueRef.current === query
          ) {
            setLoading(false)
          }
        }
      })()
    }, 300)

    return () => window.clearTimeout(timer)
  }, [inputValue, opened, selectedOffer])

  const handleInputChange = (rawValue: string) => {
    if (selectedOffer) {
      setSelectedOffer(null)
    }

    const digits = rawValue.replace(/\D/g, '')

    if (digits === '') {
      cancelOfferRequest()
      syncInputValue('')
      setOffers([])
      combobox.closeDropdown()
      return
    }

    cancelOfferRequest()
    syncInputValue(digits)
  }

  const handleOfferSelect = (value: string) => {
    const offer = offers.find((item) => String(item.id) === value)
    if (!offer) {
      return
    }

    cancelOfferRequest()
    setOffers([])
    setSelectedOffer(offer)
    syncInputValue(formatOffer(offer))
    combobox.closeDropdown()
  }

  const handleSubmit = form.onSubmit(async (values) => {
    if (!selectedOffer) {
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const response = await apiClient('/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: values.name.trim(),
          geo: values.geo.trim(),
          offer_id: selectedOffer.id,
        }),
      })

      if (!response.ok) {
        setError(await readErrorDetail(response))
        return
      }

      form.reset()
      resetOfferState()
      onClose()
      onCreated()
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title="Новая кампания"
      radius="lg"
      padding="lg"
      overlayProps={{ backgroundOpacity: 0.35 }}
      styles={{
        title: { color: palette.text, fontWeight: 600 },
        content: { border: `1px solid ${palette.border}` },
      }}
    >
      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          <TextInput
            label="Название"
            placeholder="campaign1"
            {...form.getInputProps('name')}
            styles={{ label: { color: palette.textSecondary } }}
          />
          <TextInput
            label="Гео-код"
            placeholder="us"
            {...form.getInputProps('geo')}
            styles={{ label: { color: palette.textSecondary } }}
          />
          <Combobox
            store={combobox}
            position="bottom-start"
            onOptionSubmit={handleOfferSelect}
          >
            <Combobox.Target>
              <TextInput
                label="ID оффера"
                placeholder="77"
                value={inputValue}
                onChange={(event) =>
                  handleInputChange(event.currentTarget.value)
                }
                onClick={() => {
                  if (!selectedOffer && offers.length > 0) {
                    combobox.openDropdown()
                  }
                }}
                onFocus={() => {
                  if (!selectedOffer && offers.length > 0) {
                    combobox.openDropdown()
                  }
                }}
                inputMode="numeric"
                rightSection={loading ? <Loader size="xs" /> : null}
                styles={{ label: { color: palette.textSecondary } }}
              />
            </Combobox.Target>

            <Combobox.Dropdown
              styles={{
                dropdown: {
                  borderColor: palette.border,
                },
              }}
            >
              <Combobox.Options
                style={{ maxHeight: 240, overflowY: 'auto' }}
              >
                {offers.map((offer) => (
                  <Combobox.Option key={offer.id} value={String(offer.id)}>
                    {formatOffer(offer)}
                  </Combobox.Option>
                ))}
              </Combobox.Options>
            </Combobox.Dropdown>
          </Combobox>
          {error ? (
            <Text size="sm" c="red">
              {error}
            </Text>
          ) : null}
          <Group justify="flex-end" gap="sm">
            <Button variant="subtle" color="gray" onClick={handleClose}>
              Отмена
            </Button>
            <Button
              type="submit"
              loading={submitting}
              color="brand"
              disabled={!selectedOffer}
            >
              Создать
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}