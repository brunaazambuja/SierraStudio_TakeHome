import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    background: {
      default: '#121212',
      paper: '#383432',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  typography: {
    allVariants: {
      color: '#ffffff',
    },
  },
  components: {
    MuiSnackbarContent: {
      styleOverrides: {
        root: {
          color: '#ffffff',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          color: '#ffffff',
        },
      },
    },
  },
});
