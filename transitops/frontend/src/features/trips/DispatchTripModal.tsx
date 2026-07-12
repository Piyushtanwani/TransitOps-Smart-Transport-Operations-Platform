import { ConfirmDialog } from '../../components/ui/ConfirmDialog';

interface DispatchTripModalProps {
  isOpen: boolean;
  onClose: () => void;
  tripCode: string;
  vehicleReg: string;
  driverName: string;
  cargoWeight: number;
}

export function DispatchTripModal({ 
  isOpen, 
  onClose, 
  tripCode,
  vehicleReg,
  driverName,
  cargoWeight 
}: DispatchTripModalProps) {
  
  const handleDispatch = () => {
    console.log(`Dispatching trip ${tripCode}`);
    onClose();
  };

  return (
    <ConfirmDialog
      isOpen={isOpen}
      title="Dispatch Trip"
      message={
        <div className="space-y-4 text-left w-full mt-2">
          <ul className="list-disc pl-5 space-y-1 text-ink-mute">
            <li><strong className="text-ink">{vehicleReg}</strong> is available</li>
            <li><strong className="text-ink">{driverName}</strong> license is valid</li>
            <li>Cargo (<strong className="text-ink">{cargoWeight} kg</strong>) is within capacity</li>
          </ul>
          
          <div className="mt-6 p-4 rounded-lg bg-surface-1 border border-line relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-warn"></div>
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold text-sm flex items-center text-ink">
                <svg className="w-4 h-4 mr-2 text-signal" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                AI Trip Advisor
              </h4>
              <span className="bg-warn/20 text-warn border border-warn/30 text-[10px] uppercase font-bold px-2 py-0.5 rounded-full">Caution</span>
            </div>
            <p className="text-sm text-ink-mute">
              Heavy rain is forecasted along the route for the next 4 hours. Recommend reducing speed and ensuring cargo is fully secured against water damage. Driver fatigue risk is low.
            </p>
          </div>
        </div>
      }
      confirmText="Dispatch Now"
      onConfirm={handleDispatch}
      onCancel={onClose}
    />
  );
}
