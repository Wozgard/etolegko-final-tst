import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { CampaignListPage } from './CampaignListPage'
import { CampaignOffersPage } from './CampaignOffersPage'
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

  it('renders two campaigns in table rows and opens campaign on row click', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [
          { id: 10, name: 'test_shvirev_alpha' },
          { id: 20, name: 'test_shvirev_beta' },
        ],
      }),
    )

    render(
      <MantineProvider theme={appTheme}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<CampaignListPage />} />
            <Route path="/campaigns/:id" element={<CampaignOffersPage />} />
          </Routes>
        </BrowserRouter>
      </MantineProvider>,
    )

    await screen.findByRole('cell', { name: '10' })
    await screen.findByRole('cell', { name: 'test_shvirev_beta' })

    const rows = screen.getAllByRole('row')
    expect(rows).toHaveLength(3)

    const cells = screen.getAllByRole('cell')
    expect(cells[0]).toHaveTextContent('10')
    expect(cells[1]).toHaveTextContent('test_shvirev_alpha')
    expect(cells[2]).toHaveTextContent('20')
    expect(cells[3]).toHaveTextContent('test_shvirev_beta')

    fireEvent.click(rows[1])

    expect(
      await screen.findByRole('heading', { name: 'Офферы кампании 10' }),
    ).toBeInTheDocument()
  })

  it('keeps create disabled until offer selected and posts offer id', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })

    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const href =
          typeof input === 'string'
            ? input
            : input instanceof URL
              ? input.href
              : input.url

        if (href.includes('/offers?q=99')) {
          return Promise.resolve({
            ok: true,
            json: async () => [{ id: 99, name: 'Chosen Offer' }],
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

    await screen.findByLabelText('Название')

    const createButton = screen.getByRole('button', {
      name: 'Создать',
      hidden: true,
    })
    expect(createButton).toBeDisabled()

    const offerInput = await screen.findByLabelText('ID оффера')
    fireEvent.change(offerInput, { target: { value: '99' } })
    await vi.advanceTimersByTimeAsync(300)

    expect(createButton).toBeDisabled()
    expect(offerInput).toHaveValue('99')

    fireEvent.click(
      await screen.findByRole('option', { name: '99 — Chosen Offer' }),
    )

    expect(
      screen.getByRole('button', { name: 'Создать', hidden: true }),
    ).not.toBeDisabled()
    expect(offerInput).toHaveValue('99 — Chosen Offer')

    fireEvent.change(screen.getByLabelText('Название'), {
      target: { value: 'test_shvirev_campaign' },
    })
    fireEvent.change(screen.getByLabelText('Гео-код'), {
      target: { value: 'ru' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await vi.waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/campaigns'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            name: 'test_shvirev_campaign',
            geo: 'ru',
            offer_id: 99,
          }),
        }),
      )
    })

    vi.useRealTimers()
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