import type { ReactNode } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: ReactNode;
  confirmText?: string;
  cancelText?: string;
  isDestructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDestructive = false,
  onConfirm,
  onCancel
}: ConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} title={title}>
      <div className="space-y-6">
        <div className="text-ink text-sm leading-relaxed">{message}</div>
        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onCancel}>{cancelText}</Button>
          <Button 
            className={isDestructive ? 'bg-danger hover:bg-danger/90 border-transparent text-white' : 'bg-signal hover:bg-signal/90 border-transparent text-white'} 
            onClick={onConfirm}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
