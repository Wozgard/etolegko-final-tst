import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import { CampaignListPage } from './CampaignListPage'
import { appTheme } from '../shared/theme'

function renderPage() {
  return render(
    <MantineProvider theme={appTheme}>
      <BrowserRouter>
        <CampaignListPage />
      </BrowserRouter>
    </MantineProvider>,
  )
}

describe('CampaignListPage', () => {
  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [],
      }),
    )
  })

  it('renders campaign list heading', async () => {
    renderPage()

    expect(
      await screen.findByRole('heading', { name: 'Кампании' }),
    ).toBeInTheDocument()
  })

  it('shows test prefix notice', async () => {
    renderPage()

    expect(
      await screen.findByText('Показаны только кампании с префиксом test_shvirev_'),
    ).toBeInTheDocument()
  })

  it('opens create modal when clicking new campaign', async () => {
    renderPage()

    fireEvent.click(
      await screen.findByRole('button', { name: 'Новая кампания' }),
    )

    expect(await screen.findByLabelText('Название')).toBeInTheDocument()
  })

  it('searches offers in create modal and submits selected offer id', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })

    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const href =
          typeof input === 'string'
            ? input
            : input instanceof URL
              ? input.href
              : input.url

        if (href.includes('/offers?q=77')) {
          return Promise.resolve({
            ok: true,
            json: async () => [{ id: 77, name: 'Sample Offer' }],
          })
        }

        if (href.includes('/campaigns') && init?.method === 'POST') {
          return Promise.resolve({
            ok: true,
            json: async () => ({ id: 1 }),
          })
        }

        return Promise.resolve({
          ok: true,
          json: async () => [],
        })
      },
    )
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    fireEvent.click(
      await screen.findByRole('button', { name: 'Новая кампания' }),
    )

    expect(screen.queryByRole('spinbutton')).not.toBeInTheDocument()

    const offerInput = await screen.findByLabelText('ID оффера')

    fireEvent.change(offerInput, {
      target: { value: '77' },
    })

    await vi.advanceTimersByTimeAsync(300)

    fireEvent.click(
      await screen.findByRole('option', { name: '77 — Sample Offer' }),
    )

    expect(offerInput).toHaveValue('77 — Sample Offer')

    fireEvent.change(screen.getByLabelText('Название'), {
      target: { value: 'test_shvirev_campaign' },
    })
    fireEvent.change(screen.getByLabelText('Гео-код'), {
      target: { value: 'us' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/campaigns'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            name: 'test_shvirev_campaign',
            geo: 'us',
            offer_id: 77,
          }),
        }),
      )
    })

    vi.useRealTimers()
  })

  it('does not show stale offers after input cleared before response', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })

    let resolveOffers: (() => void) | undefined

    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const href =
          typeof input === 'string'
            ? input
            : input instanceof URL
              ? input.href
              : input.url

        if (href.includes('/offers?q=77')) {
          return new Promise<Response>((resolve) => {
            resolveOffers = () =>
              resolve({
                ok: true,
                json: async () => [{ id: 77, name: 'Sample Offer' }],
              } as Response)
          })
        }

        return Promise.resolve({
          ok: true,
          json: async () => [],
        })
      },
    )
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    fireEvent.click(
      await screen.findByRole('button', { name: 'Новая кампания' }),
    )

    const offerInput = await screen.findByLabelText('ID оффера')

    fireEvent.change(offerInput, {
      target: { value: '77' },
    })

    await vi.advanceTimersByTimeAsync(300)

    fireEvent.change(offerInput, {
      target: { value: '' },
    })

    resolveOffers?.()
    await Promise.resolve()
    await Promise.resolve()

    expect(
      screen.queryByRole('option', { name: '77 — Sample Offer' }),
    ).not.toBeInTheDocument()

    vi.useRealTimers()
  })
})