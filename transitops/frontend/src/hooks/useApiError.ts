import { AxiosError } from 'axios';
import type { FieldValues, UseFormSetError } from 'react-hook-form';
import type { ErrorEnvelope } from '../types/api';
// import { useToast } from '../components/ui/Toast'; // Assuming toast exists

export interface ApiErrorDetail {
  code: string;
  message: string;
  field?: string | null;
  status?: number;
}

/** Extracts {code,message,field} from an axios error's response.data.error, with sane fallbacks. */
export function getApiErrorDetail(error: unknown): ApiErrorDetail {
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as AxiosError<ErrorEnvelope>;
    const errorData = axiosError.response?.data?.error;
    const status = axiosError.response?.status;

    if (errorData) {
      return { code: errorData.code, message: errorData.message, field: errorData.field, status };
    }

    return { code: 'UNKNOWN_ERROR', message: axiosError.message || 'An unexpected error occurred.', status };
  }

  return { code: 'UNKNOWN_ERROR', message: 'An unexpected error occurred.' };
}

export function useApiError() {
  // const { addToast } = useToast();

  const handleApiError = (error: unknown, setError?: UseFormSetError<FieldValues>) => {
    const { message, field } = getApiErrorDetail(error);

    if (field && setError) {
      // Map to RHF field
      setError(field, {
        type: 'server',
        message,
      });
    } else {
      // Global toast
      // addToast({ type: 'danger', message });
      alert(message); // Fallback for now until Toast is built
    }
  };

  return { handleApiError, getApiErrorDetail };
}
