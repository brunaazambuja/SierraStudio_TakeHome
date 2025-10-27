import { CssBaseline, ThemeProvider } from '@mui/material';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Toast from './components/Toast';
import { ToastProvider } from './context/ToastContext';
import Home from './pages/Home';
import Upload from './pages/Upload';
import Watch from './pages/Watch';
import { theme } from './styles/theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ToastProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/watch/:videoName" element={<Watch />} />
            </Routes>
          </Layout>
          <Toast />
        </Router>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
