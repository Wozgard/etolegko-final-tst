import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CampaignListPage } from './CampaignListPage'

describe('CampaignListPage', () => {
  it('renders campaign list heading', () => {
    render(
      <MantineProvider>
        <CampaignListPage />
      </MantineProvider>,
    )

    expect(
      screen.getByRole('heading', { name: 'Кампании' }),
    ).toBeInTheDocument()
  })
})