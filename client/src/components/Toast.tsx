import { Alert, Snackbar } from '@mui/material';
import { useToast } from '../context/ToastContext';

export default function Toast() {
  const { toastOpen, toastSeverity, toastMessage, hideToast } = useToast();
  return (
    <Snackbar
      open={toastOpen}
      autoHideDuration={3000}
      onClose={hideToast}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert
        onClose={hideToast}
        severity={toastSeverity}
        variant="filled"
        sx={{ width: '100%' }}
      >
        {toastMessage}
      </Alert>
    </Snackbar>
  );
}
