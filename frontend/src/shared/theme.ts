import { createTheme } from '@mantine/core'

export const CAMPAIGN_NAME_PREFIX = 'test_shvirev_'

export const palette = {
  pageBg: '#D8EDF4',
  text: '#5A5058',
  textSecondary: '#918980',
  border: '#B8ADAC',
  primary: '#D28E5F',
} as const

export const appTheme = createTheme({
  colors: {
    brand: [
      '#fbf0e8',
      '#f5e0d0',
      '#eec9ad',
      '#e7b28a',
      '#e09d6c',
      '#d28e5f',
      '#c47d4f',
      '#a6653f',
      '#894e30',
      '#6d3822',
    ],
  },
  primaryColor: 'brand',
  primaryShade: { light: 5, dark: 5 },
  fontFamily:
    'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
})