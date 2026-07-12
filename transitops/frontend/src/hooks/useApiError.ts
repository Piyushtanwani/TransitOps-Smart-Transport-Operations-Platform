import { AxiosError } from 'axios';
import type { UseFormSetError } from 'react-hook-form';
import type { ErrorEnvelope } from '../types/api';
// import { useToast } from '../components/ui/Toast'; // Assuming toast exists

export function useApiError() {
  // const { addToast } = useToast();

  const handleApiError = (error: unknown, setError?: UseFormSetError<any>) => {
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as AxiosError<ErrorEnvelope>;
      const errorData = axiosError.response?.data?.error;

      if (errorData) {
        if (errorData.field && setError) {
          // Map to RHF field
          setError(errorData.field, {
            type: 'server',
            message: errorData.message,
          });
        } else {
          // Global toast
          // addToast({ type: 'danger', message: errorData.message });
          alert(errorData.message); // Fallback for now until Toast is built
        }
        return;
      }
    }
    
    // Generic fallback
    // addToast({ type: 'danger', message: 'An unexpected error occurred.' });
    alert('An unexpected error occurred.');
  };

  return { handleApiError };
}
