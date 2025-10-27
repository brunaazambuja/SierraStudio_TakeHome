import { createContext, useCallback, useContext, useState } from 'react';

interface ToastContextType {
  toastOpen: boolean;
  toastMessage: string;
  toastSeverity: 'success' | 'error';
  showToast: (message: string, severity: 'success' | 'error') => void;
  hideToast: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  const [toastOpen, setToastOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastSeverity, setToastSeverity] = useState<'success' | 'error'>(
    'success'
  );

  const showToast = useCallback(
    (message: string, severity: 'success' | 'error') => {
      setToastMessage(message);
      setToastSeverity(severity);
      setToastOpen(true);
    },
    []
  );

  const hideToast = useCallback(() => {
    setToastOpen(false);
  }, []);

  return (
    <ToastContext.Provider
      value={{
        toastOpen,
        toastMessage,
        toastSeverity,
        showToast,
        hideToast,
      }}
    >
      {children}
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
