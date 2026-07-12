import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { RoleBadge } from '../../components/ui/RoleBadge';
import { ScoreBar } from '../../components/ui/ScoreBar';

export function ComponentKit() {
  return (
    <div className="p-8 space-y-12 bg-surface-0 min-h-screen">
      <div>
        <h1 className="text-3xl font-heading font-bold text-ink mb-2">TransitOps Component Kit</h1>
        <p className="text-ink-mute">Standard UI building blocks</p>
      </div>

      <section>
        <h2 className="text-xl font-heading font-semibold text-ink mb-4 border-b border-line pb-2">Buttons</h2>
        <div className="flex flex-wrap gap-4">
          <Button className="bg-signal text-white border-transparent">Primary Signal</Button>
          <Button>Secondary / Default</Button>
          <Button variant="ghost">Ghost Button</Button>
          <Button className="bg-danger text-white border-transparent">Destructive</Button>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-heading font-semibold text-ink mb-4 border-b border-line pb-2">Inputs</h2>
        <div className="max-w-md space-y-4">
          <Input label="Standard Input" placeholder="Type here..." />
          <Input label="With Error" error="This field is required" defaultValue="Invalid" />
        </div>
      </section>

      <section>
        <h2 className="text-xl font-heading font-semibold text-ink mb-4 border-b border-line pb-2">Badges & Indicators</h2>
        <div className="flex flex-col gap-6">
          <div className="flex flex-wrap gap-4 items-center">
            <StatusBadge status="available" />
            <StatusBadge status="on_trip" />
            <StatusBadge status="in_shop" />
            <StatusBadge status="suspended" />
            <StatusBadge status="draft" />
          </div>
          <div className="flex flex-wrap gap-4 items-center">
            <RoleBadge role="fleet_manager" />
            <RoleBadge role="driver" />
            <RoleBadge role="safety_officer" />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-heading font-semibold text-ink mb-4 border-b border-line pb-2">ScoreBar</h2>
        <div className="space-y-4 max-w-sm">
          <ScoreBar score={95} />
          <ScoreBar score={65} />
          <ScoreBar score={40} />
        </div>
      </section>
    </div>
  );
}
