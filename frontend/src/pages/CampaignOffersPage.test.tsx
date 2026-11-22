import { MantineProvider } from '@mantine/core'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { CampaignOffersPage } from './CampaignOffersPage'
import { appTheme } from '../shared/theme'

const CAMPAIGN_ID = '5'
const CAMPAIGN_NAME = 'test_shvirev_campaign_five'

const streamsPayload = [
  {
    name: 'geo',
    offers: [],
  },
  {
    name: 'offer',
    offers: [
      { id: 77, name: 'Offer Alpha', share: 50 },
      { id: 88, name: 'Offer Beta', share: 50 },
    ],
  },
]

function hrefOf(input: string | URL | Request): string {
  return typeof input === 'string'
    ? input
    : input instanceof URL
      ? input.href
      : input.url
}

function countPushCalls(fetchMock: ReturnType<typeof vi.fn>): number {
  return fetchMock.mock.calls.filter(
    ([input, init]) =>
      hrefOf(input as string).includes(`/campaigns/${CAMPAIGN_ID}/push`) &&
      init?.method === 'POST',
  ).length
}

type FetchMockOptions = {
  offersSearch?: Array<{ id: number; name: string }>
}

function createStreamsFetchMock(options: FetchMockOptions = {}) {
  return vi.fn((input: string | URL | Request, init?: RequestInit) => {
    const href = hrefOf(input)

    if (
      href.includes(`/campaigns/${CAMPAIGN_ID}/streams`) &&
      init?.method !== 'POST'
    ) {
      return Promise.resolve({
        ok: true,
        json: async () => streamsPayload,
      })
    }

    if (
      href.includes(`/campaigns/${CAMPAIGN_ID}/push`) &&
      init?.method === 'POST'
    ) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ ok: true }),
      })
    }

    if (href.includes('/offers?q=')) {
      return Promise.resolve({
        ok: true,
        json: async () => options.offersSearch ?? [],
      })
    }

    if (
      href.includes('/campaigns') &&
      init?.method !== 'POST' &&
      !href.includes('/streams') &&
      !href.includes('/push')
    ) {
      return Promise.resolve({
        ok: true,
        json: async () => [{ id: Number(CAMPAIGN_ID), name: CAMPAIGN_NAME }],
      })
    }

    return Promise.resolve({
      ok: true,
      json: async () => [],
    })
  })
}

function renderOffersPage(fetchMock = createStreamsFetchMock()) {
  vi.stubGlobal('fetch', fetchMock)

  return render(
    <MantineProvider theme={appTheme}>
      <MemoryRouter initialEntries={[`/campaigns/${CAMPAIGN_ID}`]}>
        <Routes>
          <Route path="/campaigns/:id" element={<CampaignOffersPage />} />
        </Routes>
      </MemoryRouter>
    </MantineProvider>,
  )
}

async function waitForOfferTable() {
  await screen.findByRole('heading', { name: CAMPAIGN_NAME })
  await screen.findByRole('cell', { name: /Offer Alpha/ })
  await screen.findByRole('cell', { name: /Offer Beta/ })
  expect(screen.getAllByText('50%')).toHaveLength(2)
}

describe('CampaignOffersPage', () => {
  afterEach(() => {
    cleanup()
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('removing offer keeps row at bottom with 0% and pending actions', async () => {
    const fetchMock = createStreamsFetchMock()
    renderOffersPage(fetchMock)
    await waitForOfferTable()

    fireEvent.click(screen.getAllByRole('button', { name: 'Удалить' })[0])

    expect(
      await screen.findByRole('button', { name: 'Вернуть' }),
    ).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Удалить' })).toHaveLength(1)
    expect(
      screen.getByRole('button', { name: 'В Keitaro' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Отмена' })).toBeInTheDocument()

    const dataRows = screen.getAllByRole('row').slice(1)
    const removedRow = dataRows[dataRows.length - 1]
    expect(removedRow).toHaveTextContent('Offer Alpha')
    expect(removedRow).toHaveTextContent('0%')
    expect(
      within(removedRow).getByRole('button', { name: 'Вернуть' }),
    ).toBeInTheDocument()
    expect(
      within(removedRow).queryByRole('button', { name: 'Удалить' }),
    ).not.toBeInTheDocument()

    const activeRow = screen.getByRole('row', { name: /Offer Beta/ })
    expect(
      within(activeRow).getByRole('button', { name: 'Удалить' }),
    ).toBeInTheDocument()

    expect(countPushCalls(fetchMock)).toBe(0)
  })

  it('cancel restores even shares and hides push actions', async () => {
    const fetchMock = createStreamsFetchMock()
    renderOffersPage(fetchMock)
    await waitForOfferTable()

    fireEvent.click(screen.getAllByRole('button', { name: 'Удалить' })[0])
    await screen.findByRole('button', { name: 'Отмена' })

    fireEvent.click(screen.getByRole('button', { name: 'Отмена' }))

    expect(
      screen.queryByRole('button', { name: 'В Keitaro' }),
    ).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Отмена' })).not.toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Удалить' })).toHaveLength(2)
    expect(screen.getAllByText('50%')).toHaveLength(2)
  })

  it('pin on even 50/50 shares does not show push actions', async () => {
    const fetchMock = createStreamsFetchMock()
    renderOffersPage(fetchMock)
    await waitForOfferTable()

    fireEvent.click(screen.getAllByRole('button', { name: 'Закрепить' })[0])

    expect(
      screen.queryByRole('button', { name: 'В Keitaro' }),
    ).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Отмена' })).not.toBeInTheDocument()
    expect(screen.getAllByText('50%')).toHaveLength(2)
  })

  it('pinned first offer stays at 50% when a third offer is added', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })

    const fetchMock = createStreamsFetchMock({
      offersSearch: [{ id: 99, name: 'Offer Gamma' }],
    })
    renderOffersPage(fetchMock)
    await waitForOfferTable()

    fireEvent.click(screen.getAllByRole('button', { name: 'Закрепить' })[0])

    fireEvent.click(screen.getByRole('button', { name: 'Добавить оффер' }))

    const offerInput = await screen.findByLabelText('ID оффера')
    fireEvent.change(offerInput, { target: { value: '99' } })
    await vi.advanceTimersByTimeAsync(300)
    fireEvent.click(
      await screen.findByRole('option', { name: '99 — Offer Gamma' }),
    )

    const gammaRow = await screen.findByRole('row', { name: /Offer Gamma/ })
    expect(within(gammaRow).getByText('25%')).toBeInTheDocument()

    const alphaRow = screen.getByRole('row', { name: /Offer Alpha/ })
    const betaRow = screen.getByRole('row', { name: /Offer Beta/ })
    expect(within(alphaRow).getByText('50%')).toBeInTheDocument()
    expect(within(betaRow).getByText('25%')).toBeInTheDocument()
  })

  it('bring back after push shows pending actions and records only on push', async () => {
    const fetchMock = createStreamsFetchMock()
    renderOffersPage(fetchMock)
    await waitForOfferTable()

    fireEvent.click(screen.getAllByRole('button', { name: 'Удалить' })[0])
    await screen.findByRole('button', { name: 'В Keitaro' })

    fireEvent.click(screen.getByRole('button', { name: 'В Keitaro' }))
    await vi.waitFor(() => expect(countPushCalls(fetchMock)).toBe(1))

    expect(
      screen.queryByRole('button', { name: 'В Keitaro' }),
    ).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Вернуть' }))

    expect(
      screen.getByRole('button', { name: 'В Keitaro' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Отмена' })).toBeInTheDocument()
    expect(countPushCalls(fetchMock)).toBe(1)

    fireEvent.click(screen.getByRole('button', { name: 'В Keitaro' }))
    await vi.waitFor(() => expect(countPushCalls(fetchMock)).toBe(2))
  })
})