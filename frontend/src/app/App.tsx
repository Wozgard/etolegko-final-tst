import '@mantine/core/styles.css'
import { MantineProvider } from '@mantine/core'
import { appTheme } from '../shared/theme'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { CampaignListPage } from '../pages/CampaignListPage'
import { CampaignOffersPage } from '../pages/CampaignOffersPage'

export function App() {
  return (
    <MantineProvider theme={appTheme}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<CampaignListPage />} />
          <Route path="/campaigns/:id" element={<CampaignOffersPage />} />
        </Routes>
      </BrowserRouter>
    </MantineProvider>
  )
}